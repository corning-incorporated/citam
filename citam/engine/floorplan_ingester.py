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
import queue
from typing import Dict, List, Tuple

import progressbar as pb
from svgpathtools import Line, CubicBezier, Path

import citam.engine.floorplan_utils as fu
import citam.engine.geometry_and_svg_utils as gsu
import citam.engine.input_parser as parser
from citam.engine.door import Door
from citam.engine.point import Point
from citam.engine.space import Space
from citam.engine.floorplan import Floorplan
import math as m

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

        print("CSV file is: ", csv_file)

        self.buildings = set()

        self.excluded_buildings = excluded_buildings  # TODO: Implement this

        self.buildings_to_keep = buildings_to_keep
        if buildings_to_keep:
            self.buildings_to_keep = [b.lower() for b in buildings_to_keep]

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

        for _path, _attr in zip(self.space_paths, self.space_attributes):
            for _data in self.space_data:
                if _data["id"] == _attr["id"]:
                    self.buildings.add(_data["building"])
                    if (
                        self.buildings_to_keep
                        and _data["building"] not in self.buildings_to_keep
                    ):
                        continue
                    for i, line in enumerate(_path):
                        new_start = complex(
                            int(round(line.start.real)),
                            int(round(line.start.imag)),
                        )
                        new_end = complex(
                            int(round(line.end.real)),
                            int(round(line.end.imag)),
                        )
                        new_line = Line(start=new_start, end=new_end)
                        _path[i] = new_line
                        space = Space(
                            boundaries=_path,
                            path=copy.deepcopy(_path),
                            **_data,
                        )
                    self.spaces.append(space)
                    break
        self.validate_buildings()

    def create_spaces_from_svg_data(self):
        """Create space objects from data extracted in standalone svg file"""

        for space_path, space_attr in zip(
            self.space_paths, self.space_attributes
        ):
            self.buildings.add(space_attr["building"])
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
        self.validate_buildings()

    def validate_buildings(self):
        """
        Make sure we take all user-provided building names into account
        """
        # Validate building names
        if self.buildings_to_keep:
            for building in self.buildings_to_keep:
                if building not in self.buildings:
                    msg = f"Building not found: {building}. \
                            Valid buildings are: {self.buildings}"
                    raise ValueError(msg)
        else:
            self.buildings_to_keep = self.buildings

    def read_data_from_svg_file(self):
        """Read and parse floorplan from svg file"""
        (
            self.space_paths,
            self.space_attributes,
            self.door_pathsparser,
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

    def read_input_files(self):
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

        n_spaces = len(self.space_paths)
        n_doors = len(self.door_paths)
        LOG.info(f"Number of spaces extracted from SVG file {n_spaces}")
        LOG.info(f"Number of doors extracted from SVG file: {n_doors}")

    def run(self):
        """Perform the ingestion process"""

        if self.csv_file is None:
            self.create_spaces_from_svg_data()
        else:
            self.create_spaces_from_csv_and_svg_data()

        self.process_doors()

        self.building_walls = {}
        all_room_walls, all_hallway_walls = [], []
        for building in self.buildings_to_keep:
            room_walls, hallway_walls = self.find_valid_walls_and_create_doors(
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
            "Number of spaces: %d, aisles: %d, walls: %d, doors: %d",
            len(self.spaces),
            len(self.aisles),
            len(self.walls),
            len(self.doors),
        )

        self.find_min_and_max_coordinates()

        return

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
                if dot_product is not None and (
                    abs(dot_product - 1.0) < 1e-1
                    and distance < max_distance
                    and distance < current_min_distance
                ):
                    current_min_distance = distance
                    wall_index = w
                    best_door_line = door_line

        return wall_index, best_door_line

    def _find_all_overlapping_walls(
        self, door_line: Line
    ) -> Dict[int, List[int]]:
        """
        Given a door and one of the spaces that it connects, find the other
        space.

        :param int space_index: index of the space of interest
        :param Line door_line: Line representing the door
        :return: wall_index, space_index, new_walls after extracting door from
                wall
        :rtype: dict
        """
        # TODO: Handle case where more than 2 spaces are involved.
        # Find which other space this wall is shared with

        results = {}
        for space_index, space in enumerate(self.spaces):
            for wall_index_in_space, other_wall in enumerate(space.path):
                if gsu.do_walls_overlap(other_wall, door_line):
                    if space_index in results:
                        results[space_index].append(wall_index_in_space)
                    else:
                        results[space_index] = [wall_index_in_space]

        if len(results) > 2:
            space_ids = []
            for space_index in results:
                space_ids.append(self.spaces[space_index].unique_name)
            msg = "Door connecting more than 2 spaces. This is not typical: "
            LOG.warning(f"{msg}: {', '.join(space_ids)}")

        return results

    def build_door_line(self, door: Path) -> Line:
        """
        Take a door path (Line or Bezier Curve) and return a Line that
        corresponds to where it acutally falls on the map based on
        overlap with existing walls.
        """
        # Find the space where this door belongs
        space_index, door_lines = self.find_space_index_for_door(door)

        if space_index is None:
            LOG.warning("Space index for this door is None: %s", door)
            return None

        # For each door line, find closest wall and choose best door line
        # based on proximity to a wall

        wall_index, best_door_line = self.find_closest_wall_and_best_door_line(
            space_index, door_lines
        )

        if wall_index is None:
            LOG.warning("Unable to find a nearby wall %s.", door)
            return None

        wall = self.spaces[space_index].path[wall_index]
        door_line = best_door_line

        # Translate door line to overlap with wall
        door_line = gsu.align_to_reference(wall, door_line)
        V_perp = gsu.calculate_normal_vector_between_walls(door_line, wall)
        V_perp = Point(V_perp[0], V_perp[1])
        door_line = door_line.translated(V_perp.complex_coords)

        return door_line

    def _create_door_object(self, door_line, space_indices):
        """
        Given a door line and space indices, create new door object
        """
        if not space_indices:
            return
        door_obj = Door(path=door_line, space1=self.spaces[space_indices[0]])
        if not self.spaces[space_indices[0]].is_space_a_hallway():
            self.spaces[space_indices[0]].doors.append(door_line)

        if len(space_indices) > 1:
            door_obj.space2 = self.spaces[space_indices[1]]
            if not self.spaces[space_indices[1]].is_space_a_hallway():
                self.spaces[space_indices[1]].doors.append(door_line)

        self.doors.append(door_obj)

    def _remove_door_from_overlapping_walls(
        self, door_line, overlapping_walls
    ):
        """
        Given a door line and a dict of overlapping walls grouped by their
        corresponding space index, carve out the door in each wall and update
        walls accordingly.
        """
        for space_index in overlapping_walls:
            for wall_index in overlapping_walls[space_index]:
                wall = self.spaces[space_index].path[wall_index]
                new_walls = gsu.remove_segment_from_wall(wall, door_line)
                del self.spaces[space_index].path[wall_index]
                for new_wall in new_walls:
                    self.spaces[space_index].path.append(new_wall)

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

            door_line = self.build_door_line(door)
            if not door_line:
                n_no_match += 1
                continue

            # Find overlapping walls grouped by spaces to which they belong
            overlapping_walls = self._find_all_overlapping_walls(door_line)

            if not overlapping_walls:
                continue

            # Create door object and add door line to space
            self._create_door_object(door_line, list(overlapping_walls.keys()))

            # Remove door from overlapping walls
            self._remove_door_from_overlapping_walls(
                door_line, overlapping_walls
            )
            n_success += 1

        LOG.info(
            "Number of door paths: %d, no matches: %d, doors added: %d",
            len(self.door_paths),
            n_no_match,
            n_success,
        )

        return

    def create_new_door_to_room(self, room_wall, room_id):
        """
        Add door to access a given room from a given wall.

        :param Space room: the room to add door to
        :param svgpathtools.Line room_wall: the wall to carve out the door
        :param int room_id: index of the room of interest
        :return: the door created. None if unsuccessful.
        """
        door_line = gsu.compute_new_door_line(room_wall, door_size=12.0)
        if door_line is not None:
            # Find overlapping walls
            overlapping_walls = self._find_all_overlapping_walls(door_line)
            if not overlapping_walls:
                space_name = self.spaces[room_id].unique_name
                LOG.warning(
                    f"Unable to add a door to this space: {space_name}"
                )
                return
            # Create door object and add door line to spaces
            self._create_door_object(door_line, list(overlapping_walls.keys()))

            # Remove door from overlapping walls
            self._remove_door_from_overlapping_walls(
                door_line, overlapping_walls
            )

    def find_and_remove_overlaps_between_walls(
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

                # if hallway and room walls overlap, add room to door and
                # remove overlap from hallway wall
                if gsu.do_walls_overlap(h_wall, room_wall):
                    room = self.spaces[room_id]
                    n_overlaps += 1
                    if add_door and len(room.doors) == 0:
                        self.create_new_door_to_room(room_wall, room_id)

                    # Update processing queue
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

    def get_building_walls(
        self, building: str
    ) -> Tuple[list, list, list, list]:
        """
        Extract all walls from building separated by room and hallways.
        """
        hallway_walls, room_walls = [], []
        hallway_indices, room_ids = [], []
        # Seperate spaces between hallways and rooms
        for i, space in enumerate(self.spaces):

            if space.building != building:
                continue

            if space.is_space_a_hallway():
                for line in space.path:
                    hallway_indices.append(i)
                    hallway_walls.append(line)
            else:
                for line in space.path:
                    room_ids.append(i)
                    room_walls.append(line)

        return room_ids, room_walls, hallway_indices, hallway_walls

    def find_valid_walls_and_create_doors(self, building):
        """Create missing doors and remove walls between hallways

        If a wall belongs to 2 aisles or hallways, it is likely invalid.
        Similarly, if a wall belongs to a hallway but also belongs
        to a room, it is likely that there is a door to the room, unless
        the room already has a door.

        :param str building: Name of the building of interest
        :return: list of valid room and hallway walls: room_walls, valid_walls
        :rtype (list[svgpathtools.Line], list[svgpathtools.Line])
        """

        LOG.info("Creating doors in building %s", building)
        room_ids, room_walls, _, hallway_walls = self.get_building_walls(
            building
        )

        LOG.info("Room walls identified: %d", len(room_walls))
        LOG.info("Hallway walls identified: %d", len(hallway_walls))

        # Find walls that are shared between two hallways
        valid_hallway_walls, invalid_hallway_walls = self.find_invalid_walls(
            hallway_walls
        )

        LOG.info("Done with shared hallway walls.")
        LOG.info("Now working with rooms and hallways...")

        valid_walls = []
        for hallway_wall in pb.progressbar(valid_hallway_walls):
            valid_walls += self.find_and_remove_overlaps_between_walls(
                hallway_wall, room_walls, room_ids, add_door=True
            )

        for hallway_wall in pb.progressbar(invalid_hallway_walls):
            self.find_and_remove_overlaps_between_walls(
                hallway_wall, room_walls, room_ids, add_door=True
            )

        _, room_walls, _, _ = self.get_building_walls(building)

        return room_walls, valid_walls

    def get_floorplan(self):
        """
        Return the ingested floorplan object.
        """
        return Floorplan(
            self.scale,
            self.spaces,
            self.doors,
            self.walls,
            self.aisles,
            self.minx,
            self.miny,
            self.maxx,
            self.maxy,
        )

    def find_min_and_max_coordinates(self):
        """
        Find the min and max coordinates for both x and y.
        """
        self.minx = m.inf
        self.miny = m.inf
        self.maxx = -m.inf
        self.maxy = -m.inf
        for wall in self.walls:
            for x in (wall.start.real, wall.end.real):
                if x < self.minx:
                    self.minx = x
                elif x > self.maxx:
                    self.maxx = x
            for y in (wall.start.imag, wall.end.imag):
                if y < self.miny:
                    self.miny = y
                elif y > self.maxx:
                    self.maxy = y
