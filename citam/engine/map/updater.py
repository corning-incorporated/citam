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

import logging

from svgpathtools import Line, svg2paths

import citam.engine.geometry_and_svg_utils as gsu
from citam.engine.map.door import Door
from citam.engine.input_parser import parse_csv_metadata_file
from citam.engine.point import Point
from citam.engine.map.space import Space

LOG = logging.getLogger(__name__)


class FloorplanUpdater:
    def __init__(self, floorplan, svg_file=None, csv_file=None):
        super().__init__()
        self.floorplan = floorplan
        self.csv_file = csv_file
        self.svg_file = svg_file

        if self.svg_file is None and self.csv_file is None:
            LOG.error("At least one of svg or csv file required")
            quit()

        return

    def update_from_CSV_data(self):
        """Update space properties in floorplan using data from CSV file

        Cannot change space unique names

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

        return

    def read_updated_svg_file(self):
        """Read edited SVG file and extract wall and door paths.

        Parameters
        -----------
        svg_file: str
            The SVG file to read

        Returns
        --------
        svg_wall_paths: list<Path>
        svg_door_paths: list<Path>
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

    def find_special_walls(self, svg_wall_paths):
        """Compared walls from svg file to exising walls and identify new or
        edited walls as special walls

        Parameters
        -----------
        svg_wall_paths: list<Path>
            List of path elements representing the walls from the SVG file

        Returns
        --------
        None
        """
        new_or_edited_walls = [
            wall for wall in svg_wall_paths if wall not in self.floorplan.walls
        ]
        LOG.info("We found %d updated walls", len(new_or_edited_walls))
        self.floorplan.special_walls = new_or_edited_walls

    def remove_door_from_spaces(self, door):
        """
        Remove door from corresponding spaces.
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

    def find_doors_to_remove(self):
        """Go through existing doors and check if they overal with any special
        walls. If so, tag them for removal

        Parameters
        -----------

        Returns
        --------
        list<Door>
            List of doors to remove
        """
        doors_to_remove = []
        for door in self.floorplan.doors:
            for wall in self.floorplan.special_walls:
                if gsu.do_walls_overlap(wall, door.path):
                    # remove the wall from the door so as to shorten or
                    # completely remove the door
                    doors_to_remove.append(door)

        return doors_to_remove

    def run(self):
        """Run the floorplan update process using data from provided csv
        and svg files.
        """
        if self.svg_file is not None:
            svg_wall_paths, svg_door_paths = self.read_updated_svg_file()
            self.update_from_SVG_data(svg_wall_paths, svg_door_paths)

        if self.csv_file is not None:
            self.update_from_CSV_data()

        return

    def update_from_SVG_data(self, svg_wall_paths, svg_door_paths):
        """Read SVG file to extract walls and door info and update floorplan
        object accordingly.

        This cannot be used to add or remove spaces from the floorplan.

        Parameters
        -----------
        svg_file: str
            The svg file to use for the update

        Returns
        --------
        bool
            Whether the process was successful or not
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

        return

    def find_spaces_for_door(self, door_path):
        """Given a door path, check which spaces lie of both sides of the door.

        For now, only lines are supported. Bezier not supported yet.

        Parameters
        -----------
        door_path: Line
            The line object describing the door

        Returns
        --------
        space1: int
            Integer index of the first space
        space2: int
            Integer index of the second space
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
            space1 = self.floorplan.spaces[indices[0]]
            if not space1.is_space_a_hallway():
                self.floorplan.spaces[indices[0]].doors.append(door_path)
        else:
            space1 = None

        indices = self.find_spaces_of_point(new_point2)
        if len(indices) > 0:
            space2 = self.floorplan.spaces[indices[0]]
            if not space2.is_space_a_hallway():
                self.floorplan.spaces[indices[0]].doors.append(door_path)
        else:
            space2 = None

        return space1, space2

    def overlap_door_with_wall(self, new_door, max_distance_to_walls=3.0):
        """
        Verify if new door lines overlap with existing walls,
        if so, update wall accordingly and update door as well
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
                # door and wall overlap
                # if gsu.do_walls_overlap(wall, new_door):

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

    def process_new_doors(self, svg_door_paths, updated_doors):
        """Iterate over door paths extracted from svg file and process them
        for addition to the floorplan

        Parameters
        -----------
        svg_door_paths: list<Line>
            List of door paths extracted from svg file
        updated_doors: list<Door>
            List of door objects to add new doors to
        max_distance_to_wall: float
            The maximum distance from an existing wall for a door to be
            considered as overlapping with the wall
        Returns
        --------
        None
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
            else:
                LOG.warning("Could not add this door: %s", new_door)
        LOG.info("New doors processed: %d", len(svg_door_paths))

        return

    def find_spaces_of_point(self, point):
        """Find all spaces that a point belongs to. This should always be
        one unless the point is on a door line or a space boundary.

        Parameters
        -----------
        point:Point
            Point object of interst

        Returns
        -------
        list<Space>
            List of spaces where the point is found to be located
        """

        indices = []
        for i, space in enumerate(self.floorplan.spaces):
            if space.is_point_inside_space(point):
                indices.append(i)
                if len(indices) == 2:
                    break

        return indices
