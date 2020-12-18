# Copyright 2020. Corning Incorporated. All rights reserved.
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

import logging
from typing import Union, List, Tuple, Optional
import pathlib

from svgpathtools import Line, svg2paths, Path

import citam.engine.map.geometry as gsu
import citam.engine.map.utils as fu
from citam.engine.map.door import Door
from citam.engine.io.input_parser import parse_csv_metadata_file
from citam.engine.map.point import Point
from citam.engine.map.space import Space
from citam.engine.map.floorplan import Floorplan

LOG = logging.getLogger(__name__)


class FloorplanUpdater:
    """
    Class to update an existing floorplan from SVG and CSV files.
    """

    def __init__(
        self,
        floorplan: Floorplan,
        svg_file: Union[str, pathlib.Path] = None,
        csv_file: Union[str, pathlib.Path] = None,
    ) -> None:
        """
        Initialize a new floorplan updater object.

        :param floorplan: The floorplan to update.
        :type floorplan: Floorplan
        :param svg_file: location of the svg file, defaults to None
        :type svg_file: Union[str, pathlib.Path], optional
        :param csv_file: location of the csv file, defaults to None
        :type csv_file: Union[str, pathlib.Path], optional
        """

        self.floorplan = floorplan
        self.csv_file = csv_file
        self.svg_file = svg_file

        if self.svg_file is None and self.csv_file is None:
            LOG.error("At least one of svg or csv file required")
            quit()

        return

    def update_from_CSV_data(self) -> None:
        """
        Update space properties in floorplan using data from CSV file

        ..Note:: Cannot change space unique names
        """

        space_info = parse_csv_metadata_file(self.csv_file)
        LOG.debug(
            "Successfully read CSV file. Number of spaces found: %d",
            len(space_info),
        )

        for s_info in space_info:
            for i, space in enumerate(self.floorplan.spaces):
                if space.unique_name == s_info["unique_name"]:
                    space = Space(**s_info)
                    self.floorplan.spaces[i] = space
                    break

    def read_updated_svg_file(self) -> Tuple[List[Path], List[Path]]:
        """
        Read edited SVG file and extract wall and door paths.

        TODO: use appropriate function in io.input_parser instead.

        :return: List of wall and door paths from SVG file.
        :rtype: Tuple[List[Path], List[Path]]
        """
        paths, attributes = svg2paths(self.svg_file)
        svg_door_paths = []
        svg_wall_paths = []
        for i, path in enumerate(paths):
            if "id" not in attributes[i]:
                svg_wall_paths.append(path[0])
            elif "door" not in attributes[i]["id"]:
                svg_wall_paths.append(path[0])
            else:
                svg_door_paths.append(path[0])

        return svg_wall_paths, svg_door_paths

    def find_special_walls(self, svg_wall_paths: List[Line]) -> None:
        """
        Compared walls from svg file to exising walls and identify new or
        edited walls as special walls

        :param svg_wall_paths: List of path elements representing the walls
             from the SVG file.
        :type svg_wall_paths: List[Line]
        """

        new_or_edited_walls = [
            wall for wall in svg_wall_paths if wall not in self.floorplan.walls
        ]
        LOG.info("We found %d updated walls", len(new_or_edited_walls))
        self.floorplan.special_walls = new_or_edited_walls

    def remove_door_from_spaces(self, door: Door) -> None:
        """
        Remove door from corresponding spaces.

        :param door: The door to remove from the facility.
        :type door: Door
        """

        if door.space1 is not None:
            index = self.floorplan.spaces.index(door.space1)
            if door.path in self.floorplan.spaces[index].doors:
                self.floorplan.spaces[index].doors.remove(door.path)
        if door.space2 is not None:
            index = self.floorplan.spaces.index(door.space2)
            if door.path in self.floorplan.spaces[index].doors:
                self.floorplan.spaces[index].doors.remove(door.path)
        # TODO: In the future, use the code below to shorten
        # door sizes. But this is not supported for now
        # new_door = \
        #         self.remove_segment_from_wall(door.path, wall)
        # break

    def find_doors_to_remove(self) -> List[Door]:
        """
        Go through existing doors and check if they overal with any special
        walls. If so, tag them for removal

        :return: List of doors to remove.
        :rtype: List[Door]
        """

        doors_to_remove = []
        for door in self.floorplan.doors:
            for wall in self.floorplan.special_walls:
                if fu.do_walls_overlap(wall, door.path):
                    # remove the wall from the door so as to shorten or
                    # completely remove the door
                    doors_to_remove.append(door)

        return doors_to_remove

    def run(self) -> None:
        """
        Run the floorplan update process using data from provided csv
        and svg files.
        """
        if self.svg_file is not None:
            svg_wall_paths, svg_door_paths = self.read_updated_svg_file()
            self.update_from_SVG_data(svg_wall_paths, svg_door_paths)

        if self.csv_file is not None:
            self.update_from_CSV_data()

    def update_from_SVG_data(
        self, svg_wall_paths: List[Path], svg_door_paths: List[Path]
    ) -> None:
        """
        Read SVG file to extract walls and door info and update floorplan
        object accordingly.

        :param svg_wall_paths: List of paths representing walls.
        :type svg_wall_paths: List[Path]
        :param svg_door_paths: List of paths representing doors.
        :type svg_door_paths: List[Path]
        """

        n_walls = len(self.floorplan.walls)
        LOG.info("Number of walls before: %d", n_walls)
        self.find_special_walls(svg_wall_paths)

        # Update the walls after extracting the special ones
        self.floorplan.walls = svg_wall_paths
        LOG.info("New number of walls: %d", len(self.floorplan.walls))

        # Now working with doors
        n_doors = len(self.floorplan.doors)
        LOG.info("Number of doors before: %d", n_doors)

        # Delete any old door that overlaps with one of the updated walls
        LOG.info("Checking if walls overlaps with existing doors...")
        doors_to_remove = self.find_doors_to_remove()
        updated_doors = []
        for door in self.floorplan.doors:
            if door in doors_to_remove:
                self.remove_door_from_spaces(door)
            else:
                updated_doors.append(door)

        LOG.info("We removed %d doors", len(doors_to_remove))
        LOG.info("New number of doors: %d", len(updated_doors))

        # Process new door lines found in SVG file
        self.process_new_doors(svg_door_paths, updated_doors)
        self.floorplan.doors = updated_doors

        LOG.info("Final walls: %d", len(self.floorplan.walls))
        LOG.info("Final doors: %d", len(self.floorplan.doors))
        LOG.info("Done.")

    def find_spaces_for_door(
        self, door_path: Path
    ) -> Tuple[Optional[Space], Optional[Space]]:
        """
        Given a door path, check which spaces are on both sides of the door.

        ..Note:: Only line objects are supported (BezierCurves are not).

        :param door_path: the door of interest.
        :type door_path: Path
        :return: Spaces of either side of the door, None if not found.
        :rtype: Tuple[Optional[Space], Optional[Space]]
        """

        # Rounding coordinates (fractional coordinates are not supported)
        door_path = Line(
            start=complex(
                round(door_path.start.real), round(door_path.start.imag)
            ),
            end=complex(round(door_path.end.real), round(door_path.end.imag)),
        )
        door_normal = door_path.normal(0.5)
        dx = door_normal.real
        dy = door_normal.imag
        new_point1 = Point(
            x=round(door_path.point(0.5).real + 2.0 * dx),
            y=round(door_path.point(0.5).imag + 2.0 * dy),
        )
        new_point2 = Point(
            x=round(door_path.point(0.5).real - 2.0 * dx),
            y=round(door_path.point(0.5).imag - 2.0 * dy),
        )

        indices = self.find_spaces_of_point(new_point1)
        if len(indices) > 0:
            space1: Optional[Space] = self.floorplan.spaces[indices[0]]
        else:
            space1 = None

        indices = self.find_spaces_of_point(new_point2)
        if len(indices) > 0:
            space2: Optional[Space] = self.floorplan.spaces[indices[0]]
        else:
            space2 = None

        return space1, space2

    def overlap_door_with_wall(
        self, new_door: Line, max_distance_to_walls=3.0
    ) -> Line:
        """
        Verify if new door lines as provided by user overlap with existing
        walls. If so, update walls accordingly (carve out door segment) and
        update door path as necessary (e.g. translate and change orientation
        to match be perfectly superimposed on wall).

        :param new_door: New door objects.
        :type new_door: Line
        :param max_distance_to_walls: Distance beyond which door is considered
            too far to belong to a given wall, defaults to 3.0
        :type max_distance_to_walls: float, optional
        :return: The door line after any changes.
        :rtype: Line
        """

        n_initial_walls = len(self.floorplan.walls)
        for i, wall in enumerate(
            self.floorplan.walls + self.floorplan.special_walls
        ):
            xo, yo = gsu.calculate_x_and_y_overlap(wall, new_door)
            if xo < 1.0 and yo < 1.0:
                continue
            (
                dot_product,
                distance,
            ) = gsu.calculate_dot_product_and_distance_between_walls(
                wall, new_door
            )
            if dot_product is not None and (
                abs(dot_product - 1.0) < 1e-1
                and distance < max_distance_to_walls
            ):
                new_door = gsu.align_to_reference(wall, new_door)
                V_perp = gsu.calculate_normal_vector_between_walls(
                    new_door, wall
                )
                V_perp = Point(V_perp[0], V_perp[1])
                new_door = new_door.translated(V_perp.complex_coords)
                new_wall_segments = gsu.remove_segment_from_wall(
                    wall, new_door
                )

                if i < n_initial_walls:
                    del self.floorplan.walls[i]
                    self.floorplan.walls += new_wall_segments
                else:
                    del self.floorplan.special_walls[i - n_initial_walls]
                    self.floorplan.special_walls += new_wall_segments

        return new_door

    def process_new_doors(
        self, svg_door_paths: List[Line], updated_doors: List[Door]
    ) -> None:
        """
        Iterate over door paths extracted from svg file and process them
        for addition to the floorplan.

        :param svg_door_paths: List of door paths extracted from svg file.
        :type svg_door_paths: List[Line]
        :param updated_doors: List of door objects to add new doors to.
        :type updated_doors: List[Door]
        """

        n_door_paths = len(svg_door_paths)
        LOG.info("Processing %d new doors...", n_door_paths)
        for new_door in svg_door_paths:
            start_point = Point(
                x=round(new_door.start.real), y=round(new_door.start.imag)
            )
            end_point = Point(
                x=round(new_door.end.real), y=round(new_door.end.imag)
            )
            new_door = Line(
                start=start_point.complex_coords, end=end_point.complex_coords
            )
            # Find normal line and get the 2 spaces that this door connect
            space1, space2 = self.find_spaces_for_door(new_door)

            if space1 is not None or space2 is not None:
                new_door = self.overlap_door_with_wall(new_door)
                door_obj = Door(path=new_door, space1=space1, space2=space2)
                updated_doors.append(door_obj)

                if space1 and not space1.is_space_a_hallway():
                    space1.doors.append(door_obj)

                if space2 and not space2.is_space_a_hallway():
                    space2.doors.append(door_obj)
            else:
                LOG.warning("Could not add this door: %s", new_door)
        LOG.info("New doors processed: %d", len(svg_door_paths))

    def find_spaces_of_point(self, point: Point) -> List[int]:
        """
        Find all spaces that a point belongs to. This should always be
        one unless the point is on a door line or a space boundary.

        :param point: Point object of interest
        :type point: Point
        :return: List of spaces to which the point belongs.
        :rtype: List[int]
        """

        indices = []
        for i, space in enumerate(self.floorplan.spaces):
            if space.is_point_inside_space(point):
                indices.append(i)
                if len(indices) == 2:
                    break

        return indices
