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

import copy
import logging
import pickle
import queue

import progressbar as pb
from svgpathtools import Line, CubicBezier

import citam.engine.floorplan_utils as fu
import citam.engine.geometry_and_svg_utils as gsu
import citam.engine.input_parser as parser
from citam.engine.door import Door
from citam.engine.point import Point
from citam.engine.space import Space

LOG = logging.getLogger(__name__)


class FloorplanIngester:
    """Ingest floorplan data from svg and csv files."""

    def __init__(
        self,
        svg_file,
        scale,
        csv_file=None,
        extract_doors_from_file=False,
        buildings_to_keep=None,
        excluded_buildings=None,
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
        if self.excluded_buildings is None:
            self.excluded_buildings = []

        self.buildings_to_keep = buildings_to_keep
        if self.buildings_to_keep is None:
            self.buildings_to_keep = ["all"]

        if self.svg_file is not None and self.csv_file is not None:
            self.read_data_from_csv_and_svg_files()
        elif self.svg_file is not None:
            self.read_data_from_svg_file()
        else:
            LOG.warning("No svg and/or csv file provided.")

        return

    def create_spaces_from_csv_and_svg_data(self):
        """Create space objects from data extracted in csv and svg files"""

        if len(self.space_data) < len(self.space_paths):
            raise ValueError("Each good path in svg must have metadata")

        for space_path, space_attr in zip(
            self.space_paths, self.space_attributes
        ):
            for space_data in self.space_data:
                if space_data["id"] == space_attr["id"]:
                    if space_data["building"] not in self.buildings:
                        self.buildings.append(space_data["building"])
                    for i, line in enumerate(space_path):
                        new_start = complex(
                            int(round(line.start.real)),
                            int(round(line.start.imag)),
                        )
                        new_end = complex(
                            int(round(line.end.real)),
                            int(round(line.end.imag)),
                        )
                        new_line = Line(start=new_start, end=new_end)
                        space_path[i] = new_line
                        space = Space(
                            boundaries=space_path,
                            path=copy.deepcopy(space_path),
                            **space_data,
                        )
                    self.spaces.append(space)
                    break

    def create_spaces_from_svg_data(self):
        """Create space objects from data extracted in standalone svg file"""

        for space_path, space_attr in zip(
            self.space_paths, self.space_attributes
        ):
            if space_data["building"] not in self.buildings:
                self.buildings.append(space_data["building"])
            for i, line in enumerate(space_path):
                new_start = complex(
                    int(round(line.start.real)),
                    int(round(line.start.imag)),
                )
                new_end = complex(
                    int(round(line.end.real)),
                    int(round(line.end.imag)),
                )
                new_line = Line(start=new_start, end=new_end)
                space_path[i] = new_line
                space = Space(
                    boundaries=space_path,
                    path=copy.deepcopy(space_path),
                    **space_attr,
                )
            self.spaces.append(space)

    def read_data_from_svg_file(self):
        """Read and parse floorplan from svg file"""
        (self.space_paths,
         self.space_attributes,
         self.door_pathsparser
         ) = parser.parse_standalone_svg_floorplan_file(self.svg_file)

    def read_data_from_csv_and_svg_files(self):
        """Read and parse csv and svg files"""
        self.space_data = parser.parse_csv_metadata_file(self.csv_file)

        if len(self.space_data) == 0:
            raise ValueError("Could not load any space data from CSV file")

        n_data = len(self.space_data)
        LOG.info("Successfully loaded %d rows from csv file", n_data)

        svg_data = parser.parse_svg_floorplan_file(self.svg_file)

        if len(svg_data[0]) == 0:
            raise ValueError("Could not load any space path from SVG file")

        self.space_paths = svg_data[0]
        self.space_attributes = svg_data[1]
        self.door_paths = svg_data[2]

        return

    def run(self):
        """Perform the ingestion process"""

        if self.csv_file is None:
            self.create_spaces_from_svg_data()
        else:
            self.create_spaces_from_csv_and_svg_data()

        self.process_doors()

        self.building_walls = {}
        all_room_walls, all_hallway_walls = [], []
        for building in self.buildings:
            room_walls, hallway_walls = self.find_walls_and_create_doors(
                building
            )
            building_walls = room_walls + hallway_walls
            xmin, xmax, ymin, ymax = fu.compute_bounding_box(building_walls)

            self.building_walls[building] = {
                "walls": building_walls,
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
            }
            all_room_walls += room_walls
            all_hallway_walls += hallway_walls

        self.walls = all_room_walls + all_hallway_walls

        LOG.info("Done loading floorplan from files.")
        LOG.info(
            "Number of spaces: %d, aisles: %d, walls: %d",
            len(self.spaces),
            len(self.aisles),
            len(self.walls),
        )

    def find_space_index_for_door(self, door):
        """
        Given a door SVG element, find the index of the space to which it
        belongs.

        :param Path door: path element representing a door in the drawing
        :return: space_index and door lines
        :rtype: (int,list[Line])
        """
        # Find lines on which the door potentially lies
        test_points = []
        door_lines = door

        for path in door:
            if type(path) == CubicBezier:
                door_lines = gsu.find_door_line(path)
                test_points.append(Point(complex_coords=path.point(0.5)))
                test_points.append(Point(complex_coords=path.start))
                test_points.append(Point(complex_coords=path.end))
            else:
                test_points.append(Point(complex_coords=path.point(0.5)))
                test_points.append(Point(complex_coords=path.start))
                test_points.append(Point(complex_coords=path.end))

        # Use the test points to find the space to which this door belongs
        space_index = None
        for test_point in test_points:
            for i, space in enumerate(self.spaces):
                if space.is_point_inside_space(
                    test_point, include_boundaries=True
                ):
                    space_index = i
                    break
            if space_index is not None:
                break

        return space_index, door_lines

    def find_closest_wall_and_best_door_line(
        self, space_index, door_lines, max_distance=10.0
    ):
        """
        Given a number of lines in the door SVG element, find the best line
        based on proximity to a wall.

        :param int space_index: index of the space where this door is located
        :param list door_lines: list of Line elements that represent the door
        :param float max_distance: max distance beyond which a wall is
            considered too far from the door.
        :return: wall index and best_door_line
                index of the closest wall to any given line and Line that is
                closest to that wall
        :rtype: (int, Line)
        """
        wall_index = None
        current_min_distance = 100.0
        best_door_line = None

        for w, wall in enumerate(self.spaces[space_index].path):
            if wall.length() <= 2:
                continue

            for door_line in door_lines:
                xo, yo = gsu.calculate_x_and_y_overlap(wall, door_line)
                if xo < 1.0 and yo < 1.0:
                    continue
                (
                    dot_product,
                    distance,
                ) = gsu.calculate_dot_product_and_distance_between_walls(
                    wall, door_line
                )
                if dot_product is not None:
                    if (
                        abs(dot_product - 1.0) < 1e-1
                        and distance < max_distance
                        and distance < current_min_distance
                    ):
                        current_min_distance = distance
                        wall_index = w
                        best_door_line = door_line

        return wall_index, best_door_line

    def find_adjacent_space(self, space_index, door_line):
        """
        Given a door and one of the spaces that it connects, find the other
        space.

        :param int space_index: index of the space of interest
        :param Line door_line: Line representing the door
        :return: wall_index, space_index, new_walls after extracting door from
                wall
        :rtype: int, int, Line
        """
        # TODO: Handle case where more than 2 spaces are involved.
        # Find which other space this wall is shared with
        space2_index = None
        wall2_index = None
        new_walls2 = []
        for j, space in enumerate(self.spaces):
            if space != self.spaces[space_index]:
                for k, other_wall in enumerate(space.path):
                    if gsu.do_walls_overlap(other_wall, door_line):
                        space2_index = j
                        wall2_index = k
                        new_walls2 = gsu.remove_segment_from_wall(
                            other_wall, door_line
                        )
                        if not space.is_space_a_hallway():
                            space.doors.append(door_line)
                        break
            if space2_index is not None:
                break

        return wall2_index, space2_index, new_walls2

    def process_doors(self):
        """Iterate over the door paths extracted from the SVG file, find
        associated spaces and create door objects.
        """
        LOG.info("Processing doors from SVG file...")

        n_success = 0
        n_no_match = 0

        i = -1
        for door in pb.progressbar(self.door_paths):
            i += 1

            # Find the space where this door belongs
            space_index, door_lines = self.find_space_index_for_door(door)

            if space_index is None:
                LOG.warning("Space index for this door is None: %s", door)
                n_no_match += 1
                continue

            # For each door line, find closest wall and choose best door line
            # based on proximity to a wall
            (
                wall_index,
                best_door_line,
            ) = self.find_closest_wall_and_best_door_line(
                space_index, door_lines
            )

            if wall_index is None:
                LOG.warning("Unable to find a nearby wall %s.", door)
                continue

            wall = self.spaces[space_index].path[wall_index]
            door_line = best_door_line

            # Translate door line to overlap with wall
            door_line = gsu.align_to_reference(wall, door_line)
            V_perp = gsu.calculate_normal_vector_between_walls(door_line, wall)
            V_perp = Point(V_perp[0], V_perp[1])
            door_line = door_line.translated(V_perp.complex_coords)

            # Find adjacent space
            wall2_index, space2_index, new_walls2 = self.find_adjacent_space(
                space_index, door_line
            )

            # Add door line to space
            self.spaces[space_index].doors.append(door_line)
            new_walls = gsu.remove_segment_from_wall(wall, door_line)

            # Create door object
            door_obj = Door(path=door_line, space1=self.spaces[space_index])
            if space2_index is not None:
                door_obj.space2 = self.spaces[space2_index]
            self.doors.append(door_obj)
            n_success += 1

            # Delete walls that have been broken down
            del self.spaces[space_index].path[wall_index]
            for new_wall in new_walls:
                self.spaces[space_index].path.append(new_wall)

            if wall2_index is not None:
                del self.spaces[space2_index].path[wall2_index]
                for new_wall in new_walls2:
                    self.spaces[space2_index].path.append(new_wall)

        LOG.info(
            "Number of door paths: %d, no matches: %d, doors added: %d",
            len(self.door_paths),
            n_no_match,
            n_success,
        )

        return

    def add_door_to_room(self, room, room_wall, room_id):
        """
        Add door to access a given room from a given wall.

        :param Space room: the room to add door to
        :param svgpathtools.Line room_wall: the wall to carve out the door
        :param int room_id: index of the room of interest
        :return: the door created. None if unsuccessful.
        """
        door = gsu.create_door_in_room_wall(room_wall, door_size=12.0)
        if door is not None:
            door_obj = Door(path=door, space1=room)
            space2_found = False
            for sp in self.spaces:
                if sp == self.spaces[room_id]:
                    continue
                for k, other_wall in enumerate(sp.path):
                    if gsu.do_walls_overlap(other_wall, door):
                        door_obj.space2 = sp
                        space2_found = True
                        break
                if space2_found:
                    break

            self.doors.append(door_obj)
            room.doors.append(door)

        return door

    def find_and_remove_overlaps(
        self,
        hallway_wall,
        other_walls,
        other_space_ids,
        add_door=True,
    ):
        """Given a hallway wall, iterate over all other walls to test for
        overap. If found, remove overlap.

        :param Line hallway_wall: Line representing one of the walls
        :param list[svgpathtools.Line] other_walls: list of other walls from
            which to look for overlap with this wall
        :param list[int] other_space_ids: list of indices of the space to
            which each wall belongs
        :param boolean add_door: Whether to add a wall or not to the otehr
            wall if an overlap is found
        """
        wall_fragments = []
        processed_segments = []

        processing_queue = queue.Queue()
        processing_queue.put(hallway_wall)

        n_overlaps = 0
        while not processing_queue.empty():
            j = 0  # iterator over room walls
            h_wall = processing_queue.get()
            processed_segments.append(h_wall)
            overlap_found = False
            while j < len(other_walls):

                room_wall = other_walls[j]
                room_id = other_space_ids[j]

                # Edge case of room wall being a single point
                p_segment = Point(complex_coords=room_wall.start)
                q_segment = Point(complex_coords=room_wall.end)
                if p_segment == q_segment:  # This is just one point.
                    j += 1
                    continue

                if gsu.do_walls_overlap(h_wall, room_wall):
                    room = self.spaces[room_id]
                    n_overlaps += 1
                    if add_door and len(room.doors) == 0:
                        door = self.add_door_to_room(room, room_wall, room_id)
                        # update room wall to carve out door
                        if door is not None:
                            new_wall = gsu.subtract_walls(room_wall, door)
                            for w, wall in enumerate(room.path):
                                if wall == room_wall:
                                    room.path[w] = new_wall
                                    other_walls[j] = new_wall
                                    self.spaces[room_id] = room
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

    def find_invalid_walls(self, hallway_walls):
        """Find and remove walls that are between 2 hallways (or aisles)

        :param list[Line] hallway_walls: list of lines representing the walls
            to check.
        :return valid_hallway_walls, invalid_hallway_walls
        :rtype: (list[svgpathtools.Line], list[svgpathtools.Line])
        """
        valid_hallway_walls = []
        invalid_hallway_walls = []

        for i in range(len(hallway_walls)):
            # space1 = self.spaces[hallway_indices[i]]
            wall1 = hallway_walls[i]
            wall1 = gsu.round_coords(wall1)
            if wall1.start == wall1.end:  # This is just one point.
                continue

            for j in range(i + 1, len(hallway_walls)):
                # find other hallways that share this wall
                # space2 = self.spaces[hallway_indices[j]]
                wall2 = hallway_walls[j]
                wall2 = gsu.round_coords(wall2)
                if wall2.start == wall2.end:  # This is just one point.
                    continue

                if gsu.do_walls_overlap(wall1, wall2, max_distance=2.0):
                    if wall1 not in invalid_hallway_walls:
                        invalid_hallway_walls.append(wall1)
                    if wall2 not in invalid_hallway_walls:
                        invalid_hallway_walls.append(wall2)

            if wall1 not in invalid_hallway_walls:
                valid_hallway_walls.append(wall1)

        return valid_hallway_walls, invalid_hallway_walls

    def find_walls_and_create_doors(self, building):
        """Create missing doors and remove walls between hallways

        If a wall belongs two aisles or hallways, it is likely invalid.
        Similarly, if a wall belongs to a hallway but also belongs
        to a room, it is likely that there is a door to the room, unless
        the room already has a door.

        :param str building: Name of the building of interest
        :return: list of valid room and hallway walls: room_walls, valid_walls
        :rtype (list[svgpathtools.Line], list[svgpathtools.Line])
        """

        LOG.info("Creating doors in building %s", building)
        hallway_walls, room_walls = [], []
        hallway_indices, room_ids = [], []

        # Seperate spaces between hallways and rooms
        n_hallways = 0
        for i, space in enumerate(self.spaces):

            if space.building != building:
                continue

            if space.is_space_a_hallway():
                n_hallways += 1
                for line in space.path:
                    hallway_indices.append(i)
                    hallway_walls.append(line)
            else:
                for line in space.path:
                    room_ids.append(i)
                    room_walls.append(line)

        LOG.info("Hallways identified: %d", n_hallways)
        LOG.info("Room walls identified: %d", len(room_walls))

        # Find walls that are shared between two hallways
        valid_hallway_walls, invalid_hallway_walls = self.find_invalid_walls(
            hallway_walls
        )

        LOG.info("Done with shared hallway walls.")
        LOG.info("Now working with rooms and hallways...")

        valid_walls = []
        i = 0
        for hallway_wall in pb.progressbar(valid_hallway_walls):
            valid_walls += self.find_and_remove_overlaps(
                hallway_wall, room_walls, room_ids, add_door=True
            )
            i += 1

        for hallway_wall in pb.progressbar(invalid_hallway_walls):
            self.find_and_remove_overlaps(
                hallway_wall, room_walls, room_ids, add_door=True
            )

        return room_walls, valid_walls

    def export_data_to_pickle_file(self, pickle_file):
        """Export extracted floorplan data to a pickle file.

        :param str pickle_file: file location where to save the data
        :return: boolean indicating if the operation was successful or not
        :rtype: bool:
        """
        special_walls = []
        data_to_save = [
            self.spaces,
            self.doors,
            self.walls,
            special_walls,
            self.aisles,
            1000,
            1000,
            self.scale,
        ]
        try:
            with open(pickle_file, "wb") as f:
                pickle.dump(data_to_save, f)
            return True
        except Exception as e:
            LOG.exception(e)
            return False
