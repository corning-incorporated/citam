# Copyright 2021. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
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
from typing import Dict, List, Tuple, Union, Set, Optional
import pathlib

import progressbar as pb
from svgpathtools import Line, CubicBezier, Path

import citam.engine.map.utils as fu
import citam.engine.map.geometry as gsu
import citam.engine.io.input_parser as parser
from citam.engine.map.door import Door
from citam.engine.map.point import Point
from citam.engine.map.space import Space
from citam.engine.map.floorplan import Floorplan
import math as m

LOG = logging.getLogger(__name__)


class FloorplanIngester:
    """Ingest floorplan data from svg and csv files."""

    def __init__(
        self,
        svg_file: Union[str, pathlib.Path],
        scale: float,
        csv_file: Union[str, pathlib.Path] = None,
        extract_doors_from_file: bool = False,
        buildings_to_keep: Set[str] = None,
        excluded_buildings: Set[str] = None,
    ) -> None:
        """
        Initialize a new floorplan ingester object.

        :param svg_file: path to the SVG file.
        :type svg_file: Union[str, pathlib.Path]
        :param scale: The scale of the floorplan.
        :type scale: float
        :param csv_file: path to the CSV file, defaults to None
        :type csv_file: Union[str, pathlib.Path], optional
        :param extract_doors_from_file: Whether to extract doors from the SVG
             file or not, defaults to False
        :type extract_doors_from_file: bool, optional
        :param buildings_to_keep: List of buildings to keep, all other
             buildings will be ignored., defaults to None
        :type buildings_to_keep: bool, optional
        :param excluded_buildings: List of buildings to exclude,
            defaults to None
        :type excluded_buildings: bool, optional
        """
        self.svg_file = svg_file
        self.csv_file = csv_file
        self.extract_doors_from_file = extract_doors_from_file
        self.scale = scale

        self.spaces: List[Space] = []
        self.doors: List[Door] = []
        self.aisles: List[Tuple[Line]] = []
        self.walls: List[Line] = []

        self.minx = None
        self.miny = None
        self.maxx = None
        self.maxy = None

        self.buildings: Set[str] = set()

        self.excluded_buildings = set(
            excluded_buildings if excluded_buildings else []
        )

        self.buildings_to_keep = set(
            [b.lower() for b in buildings_to_keep] if buildings_to_keep else []
        )

        if self.svg_file is not None and self.csv_file is not None:
            self.read_data_from_csv_and_svg_files()
        elif self.svg_file is not None:
            self.read_data_from_svg_file()
        else:
            LOG.warning("No svg and/or csv file provided.")

    def create_spaces_from_csv_and_svg_data(self) -> None:
        """
        Create space objects from data extracted in csv and svg files
        """

        if len(self.space_data) < len(self.space_paths):
            raise ValueError("Each good path in svg must have metadata")

        for _path, _attr in zip(self.space_paths, self.space_attributes):
            for _data in self.space_data:

                if (
                    self.buildings_to_keep
                    and _data["building"] not in self.buildings_to_keep
                ):
                    continue

                if _data["id"] == _attr["id"]:

                    self.buildings.add(_data["building"])

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

    def create_spaces_from_svg_data(self) -> None:
        """
        Create space objects from data extracted in standalone svg file
        """

        for space_path, space_attr in zip(
            self.space_paths, self.space_attributes
        ):
            self.buildings.add(space_attr["building"])
            for i, line in enumerate(space_path):
                new_start = complex(
                    int(round(line.start.real)), int(round(line.start.imag)),
                )
                new_end = complex(
                    int(round(line.end.real)), int(round(line.end.imag)),
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

    def validate_buildings(self) -> None:
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

    def read_data_from_svg_file(self) -> None:
        """
        Read and parse floorplan from svg file
        """
        (
            self.space_paths,
            self.space_attributes,
            self.door_paths,
        ) = parser.parse_standalone_svg_floorplan_file(self.svg_file)

    def read_data_from_csv_and_svg_files(self) -> None:
        """
        Read and parse csv and svg files
        """
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

    def read_input_files(self) -> None:
        """
        Read and parse csv and svg files
        """
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

    def run(self) -> None:
        """
        Perform the ingestion process
        """

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

    def find_space_index_for_door(
        self, door: Path
    ) -> Tuple[Optional[int], List[Line]]:
        """
        Given a door SVG element, find the index of the space to which it
        belongs.

        :param door: path element representing a door in the drawing
        :type: Door
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
        self, space_index: int, door_lines: List[Line], max_distance=10.0
    ) -> Tuple[Optional[int], Optional[Line]]:
        """
        Given a number of lines in the door SVG element, find the best line
        based on proximity to a wall.

        :param space_index: index of the space where this door is located.
        :type space_index: int
        :param door_lines: list of Line elements that represent the door
        :type door_lines: List[Line]
        :param max_distance: max distance beyond which a wall is considered too
             far from the door., defaults to 10.0
        :type max_distance: float, optional
        :return: The index of the space and the best door line
        :rtype: Tuple[Optional[int], Optional[Line]]
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
        Given a door line, find all overlapping walls.

        :param door_line: Line representing the door
        :type door_line: Line
        :return: Dictionary with all the overallping walls.
        :rtype: Dict[int, List[int]]
        """
        # TODO: Handle case where more than 2 spaces are involved.
        # Find which other space this wall is shared with
        wall_overlaps_by_space: Dict[int, list] = {}
        for space_index, space in enumerate(self.spaces):
            for wall_index_in_space, other_wall in enumerate(space.path):
                if fu.do_walls_overlap(other_wall, door_line):
                    if space_index in wall_overlaps_by_space:
                        wall_overlaps_by_space[space_index].append(
                            wall_index_in_space
                        )
                    else:
                        wall_overlaps_by_space[space_index] = [
                            wall_index_in_space
                        ]

        if len(wall_overlaps_by_space) > 2:
            space_ids = set()
            for space_index in wall_overlaps_by_space:
                space_ids.add(self.spaces[space_index].unique_name)
            msg = "Door connecting more than 2 spaces. This is not typical: "
            LOG.warning(f"Door: {door_line} --> {msg}: {', '.join(space_ids)}")

        return wall_overlaps_by_space

    def build_door_line(self, door: Path) -> Line:
        """
        Take a door path (Line or Bezier Curve) and return a Line that
        corresponds to where it acutally falls on the map based on
        overlap with existing walls.

        :param door: The door path
        :type door: Path
        :return: The best line to represent the door.
        :rtype: Line
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

    def _create_door_object(
        self, door_line: Line, space_indices: List[int]
    ) -> None:
        """
        Given a door line and space indices, create new door object and add it
        to the list of doors for this floorplan.

        :param door_line: The door line of interest.
        :type door_line: Line
        :param space_indices: Indices of the spaces that this door connects
        :type space_indices: List[int]
        """
        if not space_indices:
            return
        door_obj = Door(path=door_line, space1=self.spaces[space_indices[0]])
        if not self.spaces[space_indices[0]].is_space_a_hallway():
            self.spaces[space_indices[0]].doors.append(door_obj)

        if len(space_indices) > 1:
            door_obj.space2 = self.spaces[space_indices[1]]
            if not self.spaces[space_indices[1]].is_space_a_hallway():
                self.spaces[space_indices[1]].doors.append(door_obj)

        self.doors.append(door_obj)

    def _remove_door_from_overlapping_walls(
        self, door_line: Line, overlapping_walls: Dict[int, List[int]]
    ) -> None:
        """
        Given a door line and a dict of overlapping walls grouped by their
        corresponding space index, carve out the door in each wall and update
        walls accordingly.

        :param door_line: The door line.
        :type door_line: Line
        :param overlapping_walls: A dictionary of overlapping walls.
        :type overlapping_walls: Dict[int, List[int]]
        """
        for space_index in overlapping_walls:
            for wall_index in overlapping_walls[space_index]:
                wall = self.spaces[space_index].path[wall_index]
                new_walls = gsu.remove_segment_from_wall(wall, door_line)
                del self.spaces[space_index].path[wall_index]
                for new_wall in new_walls:
                    self.spaces[space_index].path.append(new_wall)

    def process_doors(self) -> None:
        """
        Iterate over the door paths extracted from the SVG file, find
        associated spaces and create door objects.
        """
        LOG.info("Processing doors from SVG file...")

        n_success = 0
        n_no_match = 0

        for door in pb.progressbar(self.door_paths):

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

    def create_new_door_to_room(self, room_wall: Line, room_id: int) -> None:
        """
        Add door to access a given room from a given wall.

        :param room_wall: the wall to carve out the door from.
        :type room_wall: Line
        :param room_id: index of the room of interest.
        :type room_id: int
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

    def check_for_overlap_with_other_walls_and_add_door_to_wall(
        self,
        h_wall: Line,  # Hallway wall
        other_walls: List[Line],
        other_space_ids: List[int],
        add_door: bool,
    ) -> Optional[List[Line]]:
        """
        Check for overlap between a given wall and all other walls in facility
        and add door if overlap exists with room wall that has no door.

        Before:
                    ----------
                    |  Room  |
                    |        |
        ----------------------------   <-- Split this wall to add door to room
            Hallway
        ----------------------------

        After:
                    ----------
                    |  Room  |
                    |        |
        ------------------   -------
            Hallway
        ----------------------------

        :param h_wall: The hallway wall of interest.
        :type h_wall: LIne
        :param other_walls: List of other walls to check for overlap with.
        :param other_space_ids: List of IDs corresponding to each wall.
        :type other_space_ids: List[int]
        :param add_door: Whether to add doors to room or not.
        :type add_door: bool
        :return: List of segments after wall was split. None of no overlap.
        :rtype: Optional[List[Line]]
        """
        segments = None
        j = 0  # iterator over room walls
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
            if fu.do_walls_overlap(h_wall, room_wall):
                room = self.spaces[room_id]
                if add_door and len(room.doors) == 0:
                    self.create_new_door_to_room(room_wall, room_id)

                # Update processing queue
                segments = gsu.remove_segment_from_wall(h_wall, room_wall)
                break
            j += 1
        return segments

    def find_and_remove_overlaps_between_walls(
        self,
        hallway_wall: Line,
        other_walls: List[Line],
        other_space_ids: List[int],
        add_door=True,
    ) -> List[Line]:
        """
        Given a hallway wall, iterate over all other walls to test for overlap.
        If found, remove overlap.

        :param hallway_wall: Line representing one of the walls
        :type hallway_wall: Line
        :param other_walls: list of other walls from which to look for overlap
             with this wall
        :type other_walls: List[Line]
        :param other_space_ids: list of indices of the space to which each wall
             belongs
        :type other_space_ids: List[int]
        :param add_door: Whether to add doors to the wall or not,
             defaults to True
        :type add_door: bool, optional
        :return: The list of wall fragments after removing overlaps.
        :rtype: List[Line]
        """
        wall_fragments = []
        processed_segments = []

        processing_queue = queue.Queue()  # type: ignore
        processing_queue.put(hallway_wall)

        while not processing_queue.empty():
            h_wall = processing_queue.get()
            processed_segments.append(h_wall)
            segments = self.check_for_overlap_with_other_walls_and_add_door_to_wall(
                h_wall, other_walls, other_space_ids, add_door,
            )
            if segments is not None:
                for seg in segments:
                    if seg not in processed_segments:
                        processing_queue.put(seg)
            else:
                wall_fragments.append(h_wall)

        return wall_fragments

    def get_building_walls(
        self, building: str
    ) -> Tuple[list, list, list, list]:
        """
        Extract all walls from building and return the room walls and hallway
        walls seperately.

        :param building: The name of the building
        :type building: str
        :return: List of room indices and walls as well as hallway indices
            and walls.
        :rtype: Tuple[list, list, list, list]
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

    def find_valid_walls_and_create_doors(
        self, building: str
    ) -> Tuple[List[Line], List[Line]]:
        """
        Remove all invalid walls, create missing doors and return the remaining
        walls.

        :param building: The name of the building.
        :type building: str
        :return: The list of all rooms and the list of the valid ones.
        :rtype: Tuple[List[Line], List[Line]]
        """

        LOG.info("Creating doors in building %s", building)
        room_ids, room_walls, _, hallway_walls = self.get_building_walls(
            building
        )

        LOG.info("Room walls identified: %d", len(room_walls))
        LOG.info("Hallway walls identified: %d", len(hallway_walls))

        # Find walls that are shared between two hallways
        valid_hallway_walls, invalid_hallway_walls = find_invalid_walls(
            hallway_walls
        )

        LOG.info("Done with shared hallway walls.")
        LOG.info("Now working with rooms and hallways...")

        valid_walls = []

        # Remove overlap between hallway and room walls
        for hallway_wall in pb.progressbar(valid_hallway_walls):
            valid_walls += self.find_and_remove_overlaps_between_walls(
                hallway_wall, room_walls, room_ids, add_door=True
            )
        # Remove overlaps between any invalid hallway halls and room walls
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


def find_invalid_walls(
    hallway_walls: List[Line],
) -> Tuple[List[Line], List[Line]]:
    """
    Find and remove any wall that seperates 2 hallways (or aisles).

                Remove this wall
                        |
                        V

    --------------------|------------------
        hallway 1       |   hallway 2
    --------------------|------------------

    :param hallway_walls: list of lines representing the walls to check.
    :type hallway_walls: List[Line]
    :return: list of valid walls and list of invalid_hallway_walls
    :rtype: Tuple[List[Line], List[Line]]
    """
    valid_hallway_walls = []
    invalid_hallway_walls = []

    for i in range(len(hallway_walls)):

        wall1 = hallway_walls[i]
        wall1 = gsu.round_coords(wall1)
        if wall1.start == wall1.end:  # This is just one point.
            continue

        check_for_overlap_with_other_walls(
            i, hallway_walls, invalid_hallway_walls
        )

        if wall1 not in invalid_hallway_walls:
            valid_hallway_walls.append(wall1)

    return valid_hallway_walls, invalid_hallway_walls


def check_for_overlap_with_other_walls(
    wall_index: int,
    hallway_walls: List[Line],
    invalid_hallway_walls: List[Line],
) -> None:
    """
    Given hallway wall at index wall_index, iterate over all hallway walls and
    check for overlap. If there is overlap, update list of invalid hallways.

    :param wall_index: Index of the wall of interest.
    :type wall_index: int
    :param hallway_walls: The list of all hallway walls.
    :type hallway_walls: List[Path
    :param invalid_hallway_walls: The list of invalid hallway walls.
    :type invalid_hallway_walls: List[Path]
    """
    wall1 = hallway_walls[wall_index]
    for j in range(wall_index + 1, len(hallway_walls)):
        # find other hallways that share this wall
        # space2 = self.spaces[hallway_indices[j]]
        wall2 = hallway_walls[j]
        wall2 = gsu.round_coords(wall2)
        if wall2.start == wall2.end:  # This is just one point.
            continue

        if fu.do_walls_overlap(wall1, wall2, max_distance=2.0):
            if wall1 not in invalid_hallway_walls:
                invalid_hallway_walls.append(wall1)
            if wall2 not in invalid_hallway_walls:
                invalid_hallway_walls.append(wall2)
