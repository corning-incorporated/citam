# Copyright 2020. Corning Incorporated. All rights reserved.
#
# This software may only be used in accordance with the licenses granted by
# Corning Incorporated. All other uses as well as any copying, modification or
# reverse engineering of the software is strictly prohibited.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================

import citam.engine.geometry_and_svg_utils as gsu
from citam.engine.point import Point
from citam.engine.space import Space
from citam.engine.door import Door
import citam.engine.input_parser as parser
import citam.engine.floorplan_utils as fu

from svgpathtools import Line, CubicBezier
import progressbar as pb

import logging
import queue
import copy
import pickle


class FloorplanIngester:
    """Ingest floorplan data from svg and csv files.
    """

    def __init__(self,
                 svg_file,
                 csv_file,
                 scale,
                 extract_doors_from_file=False,
                 buildings_to_keep=['all'],
                 excluded_buildings=[]
                 ):
        super().__init__()

        self.svg_file = svg_file
        self.csv_file = csv_file
        self.extract_doors_from_file = extract_doors_from_file
        self.scale = scale

        self.spaces = []
        self.doors = []
        self.aisles = []
        self.walls = []

        self.minx = None
        self.miny = None
        self.maxx = None
        self.maxy = None

        self.buildings = []

        self.excluded_buildings = excluded_buildings
        self.buildings_to_keep = buildings_to_keep

        if self.svg_file is not None and self.csv_file is not None:
            self.read_input_files()
        else:
            logging.warning('No svg and/or csv file provided.')

        return

    def create_spaces(self):
        """Create space objects from data extracted in csv and svg files

        Parameters
        -----------
        No parameter

        Returns
        --------
        None
        """
        if len(self.space_paths) == 0:
            logging.error('No space paths provided.')
            return
        if len(self.space_attributes) != len(self.space_paths):
            logging.error('The number of attributes and paths must be equal')
            return
        if len(self.space_data) < len(self.space_paths):
            logging.error('Each good path in svg must have metadata')
            return

        for space_path, space_attr in zip(self.space_paths,
                                          self.space_attributes
                                          ):
            for space_data in self.space_data:
                if space_data['id'] == space_attr['id']:
                    if space_data['building'] not in self.buildings:
                        self.buildings.append(space_data['building'])
                    for i, line in enumerate(space_path):
                        new_start = complex(int(round(line.start.real)),
                                            int(round(line.start.imag))
                                            )
                        new_end = complex(int(round(line.end.real)),
                                          int(round(line.end.imag))
                                          )
                        new_line = Line(start=new_start, end=new_end)
                        space_path[i] = new_line
                        space = Space(boundaries=space_path,
                                      path=copy.deepcopy(space_path),
                                      **space_data
                                      )
                    self.spaces.append(space)
                    break
        return

    def read_input_files(self):
        """Read and parse csv and svg files
        """
        self.space_data = parser.parse_csv_metadata_file(self.csv_file)
        if len(self.space_data) == 0:
            logging.fatal('Could not load any space data from CSV file')
            return
        else:
            n_data = len(self.space_data)
            msg = f'Successfully loaded {n_data} rows from csv file'
            logging.info(msg)

        svg_data = parser.parse_svg_floorplan_file(self.svg_file)

        if len(svg_data[0]) == 0:
            logging.fatal('Could not load any space path from SVG file')
            return
        else:
            self.space_paths = svg_data[0]
            self.space_attributes = svg_data[1]
            self.door_paths = svg_data[2]

        return

    def run(self):
        """Perform the ingestion process
        """
        self.create_spaces()
        self.process_doors()

        self.building_walls = {}
        all_room_walls, all_hallway_walls = [], []
        for building in self.buildings:
            room_walls, hallway_walls = \
                self.find_walls_and_create_doors(building)
            building_walls = room_walls + hallway_walls
            xmin, xmax, ymin, ymax = fu.compute_bounding_box(building_walls)

            self.building_walls[building] = {'walls': building_walls,
                                             'xmin': xmin,
                                             'ymin': ymin,
                                             'xmax': xmax,
                                             'ymax': ymax
                                             }
            all_room_walls += room_walls
            all_hallway_walls += hallway_walls

        self.walls = all_room_walls + all_hallway_walls

        logging.info('Done loading floorplan from files.')
        logging.info('Number of spaces: ' + str(len(self.spaces)))
        logging.info('Number of aisles: ' + str(len(self.aisles)))
        logging.info('Number of walls: ' + str(len(self.walls)))

        return

    def process_doors(self):
        """Iterate over the door paths extracted from the SVG file, find
        associated spaces and create door objects.
        """
        logging.info('Processing doors from SVG file...')

        n_success = 0
        n_no_match = 0
        max_distance = 10.0

        i = -1
        for door in pb.progressbar(self.door_paths):
            i += 1
            # Find lines on which the door potentially lies
            is_bezier = False
            test_points = []
            for path in door:
                if type(path) == CubicBezier:
                    is_bezier = True
                    bezier = path
                    door_lines = gsu.find_door_line(bezier)
                    test_points.append(Point(complex_coords=bezier.point(0.5)))
                    test_points.append(Point(complex_coords=bezier.start))
                    test_points.append(Point(complex_coords=bezier.end))
            if not is_bezier:
                door_lines = door
                for dl in door_lines:
                    test_points.append(Point(complex_coords=dl.point(0.5)))
                    test_points.append(Point(complex_coords=dl.start))
                    test_points.append(Point(complex_coords=dl.end))

            # Use the test points to find the space to which this door belongs
            space_index = None
            for test_point in test_points:
                for i, space in enumerate(self.spaces):
                    if space.is_point_inside_space(test_point,
                                                   include_boundaries=True
                                                   ):
                        space_index = i
                        break
                if space_index is not None:
                    break

            if space_index is None:
                logging.error('Space index for this door is None! Fix it!!!')
                n_no_match += 1
                continue

            # For each door line, compute distance with existing walls
            wall_index = None
            current_min_distance = 100.0
            best_door_line = None

            for w, wall in enumerate(self.spaces[space_index].path):
                if wall.length() <= 2:
                    continue

                for door_line in door_lines:
                    xo, yo = gsu.calculate_x_and_y_overlap(wall,
                                                           door_line
                                                           )
                    if xo < 1.0 and yo < 1.0:
                        continue
                    dot_product, distance = \
                        gsu.calculate_dot_product_and_distance_between_walls(
                                                            wall,
                                                            door_line
                                                        )
                    if dot_product is not None:
                        if abs(dot_product - 1.0) < 1e-1 and \
                                distance < max_distance and \
                                distance < current_min_distance:

                            current_min_distance = distance
                            wall_index = w
                            best_door_line = door_line

            if wall_index is None:
                continue

            wall = self.spaces[space_index].path[wall_index]
            door_line = best_door_line

            door_line = gsu.align_to_reference(wall, door_line)
            V_perp = gsu.calculate_normal_vector_between_walls(door_line, wall)
            V_perp = Point(V_perp[0], V_perp[1])
            door_line = door_line.translated(V_perp.complex_coords)

            self.spaces[space_index].doors.append(door_line)
            new_walls = gsu.remove_segment_from_wall(wall, door_line)

            door_obj = Door(path=door_line, space1=self.spaces[space_index])

            # Find which other space this wall is shared with
            space2_index = None
            wall2_index = None
            new_walls2 = []
            for j, space in enumerate(self.spaces):
                if space != self.spaces[space_index]:
                    for k, other_wall in enumerate(space.path):
                        if gsu.do_walls_overlap(other_wall, door_line):
                            door_obj.space2 = space
                            space2_index = j
                            wall2_index = k
                            new_walls2 = gsu.remove_segment_from_wall(
                                                    other_wall,
                                                    door_line
                                                )
                            if not space.is_space_a_hallway():
                                space.doors.append(door_line)
                            break
                if space2_index is not None:
                    break

            self.doors.append(door_obj)
            n_success += 1

            del self.spaces[space_index].path[wall_index]
            for new_wall in new_walls:
                self.spaces[space_index].path.append(new_wall)

            if wall2_index is not None:
                del self.spaces[space2_index].path[wall2_index]
                for new_wall in new_walls2:
                    self.spaces[space2_index].path.append(new_wall)

        logging.info('Number of door paths: ' + str(len(self.door_paths)))
        logging.info('Number of no matches: ' + str(n_no_match))
        logging.info('Number of doors added: ' + str(n_success))

        return

    def find_and_remove_overlaps(self,
                                 hallway_wall,
                                 other_walls,
                                 other_space_ids,
                                 add_door=True,
                                 verbose=False
                                 ):
        """Given a hallway wall, iterate over all other walls to test for
        overap. If found, remove overlap.
        """
        wall_fragments = []
        processed_segments = []

        processing_queue = queue.Queue()
        processing_queue.put(hallway_wall)

        n_overlaps = 0
        if verbose:
            logging.debug('\nWorking with hallway wall : ' + str(hallway_wall))

        while not processing_queue.empty():
            j = 0  # iterator over room walls
            h_wall = processing_queue.get()
            processed_segments.append(h_wall)
            overlap_found = False
            while j < len(other_walls):

                room_wall = other_walls[j]

                # Edge case of room wall being a single point
                p_segment = Point(complex_coords=room_wall.start)
                q_segment = Point(complex_coords=room_wall.end)
                if p_segment == q_segment:  # This is just one point.
                    j += 1
                    continue

                if gsu.do_walls_overlap(h_wall, room_wall):
                    room = self.spaces[other_space_ids[j]]
                    if room.id == '1':
                        print('N doors in space 1: ', len(room.doors))
                    n_overlaps += 1
                    if add_door and len(room.doors) == 0:
                        door = gsu.create_door_in_room_wall(room_wall,
                                                            door_size=12.0
                                                            )
                        if door is not None:
                            door_obj = Door(path=door, space1=room)
                            space2_found = False
                            for sp in self.spaces:
                                if sp != self.spaces[other_space_ids[j]]:
                                    for k, other_wall in enumerate(sp.path):
                                        if gsu.do_walls_overlap(other_wall,
                                                                door):
                                            door_obj.space2 = sp
                                            space2_found = True
                                            break
                                if space2_found:
                                    break

                            self.doors.append(door_obj)
                            room.doors.append(door)

                            # update room wall to carve out door
                            new_wall = gsu.subtract_walls(room_wall, door)
                            for w, wall in enumerate(room.path):
                                if wall == room_wall:
                                    room.path[w] = new_wall
                                    other_walls[j] = new_wall
                                    self.spaces[other_space_ids[j]] = room
                                    break

                    segments = gsu.remove_segment_from_wall(h_wall, room_wall)
                    for seg in segments:
                        if seg not in processed_segments:
                            processing_queue.put(seg)
                    overlap_found = True
                    break
                j += 1
            if not overlap_found:
                wall_fragments.append(h_wall)

        return wall_fragments

    def find_invalid_walls(self, hallway_walls, indices=None):
        """Find and remove walls that are between 2 hallways (or aisles)
        """
        valid_hallway_walls = []
        invalid_hallway_walls = []

        if indices is not None:
            valid_hallway_indices = []
        else:
            valid_hallway_indices = None

        for i in range(len(hallway_walls)):
            # space1 = self.spaces[hallway_indices[i]]
            wall1 = hallway_walls[i]
            wall1 = gsu.round_coords(wall1)

            p_segment = Point(complex_coords=wall1.start)
            q_segment = Point(complex_coords=wall1.end)
            if p_segment == q_segment:  # This is just one point.
                continue

            for j in range(i+1, len(hallway_walls)):
                # find other hallways that share this wall
                # space2 = self.spaces[hallway_indices[j]]
                wall2 = hallway_walls[j]
                wall2 = gsu.round_coords(wall2)

                p_segment = Point(complex_coords=wall2.start)
                q_segment = Point(complex_coords=wall2.end)
                if p_segment == q_segment:  # This is just one point.
                    continue

                if gsu.do_walls_overlap(wall1, wall2, max_distance=2.0):
                    if wall1 not in invalid_hallway_walls:
                        invalid_hallway_walls.append(wall1)
                    if wall2 not in invalid_hallway_walls:
                        invalid_hallway_walls.append(wall2)

            if wall1 not in invalid_hallway_walls:
                valid_hallway_walls.append(wall1)
                if indices is not None:
                    valid_hallway_indices.append(indices[i])

        return_values = \
            valid_hallway_walls, invalid_hallway_walls, valid_hallway_indices

        return return_values

    def find_walls_and_create_doors(self, building):
        """Create missing doors and remove walls between hallways

        If a wall belongs two aisles or hallways, it is likely invalid.
        Similarly, if a wall belongs to a hallway but also belongs
        to a room, it is likely that there is a door to the room, unless
        the room already has a door.

        Parameters
        -----------
        building: str
            The building of interest

        returns
        ---------
        list
            list of valid walls
        """

        logging.info('\nCreating doors in building ' + building)

        building_walls = []
        hallway_walls, room_walls = [], []
        hallway_indices, room_ids = [], []

        # Seperate spaces between hallways and rooms
        n_hallways = 0
        for i, space in enumerate(self.spaces):

            if space.building == building:

                if space.is_space_a_hallway():
                    n_hallways += 1
                    for line in space.path:
                        hallway_indices.append(i)
                        hallway_walls.append(line)
                else:
                    for line in space.path:
                        room_ids.append(i)
                        room_walls.append(line)

        logging.info('Hallways identified: ' + str(n_hallways))
        logging.info('Room walls identified: ' + str(len(room_walls)))

        # Find walls that are shared between two hallways
        valid_hallway_walls, invalid_hallway_walls, valid_hallway_indices = \
            self.find_invalid_walls(hallway_walls, indices=hallway_indices)

        logging.info('Done with shared hallway walls.')
        logging.info('Now working with rooms and hallways...')

        valid_walls = []
        i = 0
        for hallway_wall in pb.progressbar(valid_hallway_walls):
            valid_walls += self.find_and_remove_overlaps(hallway_wall,
                                                         room_walls,
                                                         room_ids,
                                                         add_door=True
                                                         )
            i += 1

        for hallway_wall in pb.progressbar(invalid_hallway_walls):
            self.find_and_remove_overlaps(hallway_wall,
                                          room_walls,
                                          room_ids,
                                          add_door=True
                                          )

        for wall in room_walls + valid_walls:
            building_walls.append(wall)

        return room_walls, valid_walls

    def export_data_to_pickle_file(self, pickle_file):
        """Export extracted floorplan data to a pickle file.

        Parameters
        -----------
        pickle_file: str
            Path to the file location where to save the data

        Returns
        -------
        bool:
            Whether the operation was successful or not
        """
        special_walls = []
        data_to_save = [self.spaces,
                        self.doors,
                        self.walls,
                        special_walls,
                        self.aisles,
                        1000,
                        1000,
                        self.scale
                        ]
        try:
            with open(pickle_file, 'wb') as f:
                pickle.dump(data_to_save, f)
            return True
        except Exception as e:
            logging.exception(e)
            return False

    # def export_building_to_svg(self, building: str, svg_file:str):
    #     """Export a specific building to svg

    #     Parameters
    #     -----------
    #     building: str
    #         The name of the building to export
    #     svg_file: str
    #         Path to where to save the svg file
    #     Returns
    #     --------
    #     None
    #     """

    #     walls = self.building_walls[building]['walls']
    #     xmin = self.building_walls[building]['xmin']
    #     ymin = self.building_walls[building]['ymin']
    #     xmax = self.building_walls[building]['xmax']
    #     ymax = self.building_walls[building]['ymax']

    #     # Map svg file for the entire facility
    #     bv.export_world_to_svg(
    #         walls,
    #         [],
    #         svg_file,
    #         marker_locations = [],
    #         marker_type = None,
    #         arrows = [],
    #         max_contacts = 100,
    #         current_time = None,
    #         show_colobar = False,
    #         viewbox = [xmin - 20, ymin -20, xmax + 50, ymax + 50]
    #     )

    #     return
