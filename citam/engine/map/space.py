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

from typing import List, Any, Dict, Tuple
import numpy as np

from svgpathtools import Line, Path

import citam.engine.map.geometry as gsu
from citam.engine.map.point import Point
from citam.engine.io.serializer import serializer
from citam.engine.constants import DEFAULT_MEETING_ROOM_CAPACITY


@serializer
class Space:
    """
    Class to manage all types of spaces within a facility (a space can be a
    room, a hallway or any navigable area within a facility)
    """

    def __init__(
        self,
        path: Path,
        boundaries: Path,
        id: str,
        unique_name: str,
        building: str,
        space_function: str,
        facility: str = None,
        floor: str = None,
        space_category: str = None,
        capacity: int = None,
        department: str = None,
        square_footage: float = None,
    ) -> None:
        """
        Initialize a new space object.

        :param path: The path object describing the walls of this space
        :type path: Path
        :param boundaries: The path object describing the boundaries of this
            space.
        :type boundaries: Path
        :param id: The unique identifier of this space.
        :type id: str
        :param unique_name: The common name of this space.
        :type unique_name: str
        :param building: The name of the building where this space is located.
        :type building: str
        :param space_function: The function of this space (e.g. circulation,
            stairs, autitorium, office, etc.). See the docs for a complete
            description of supported functions
        :type space_function: str
        :param facility: The name of the facility where this space is located,
             defaults to None
        :type facility: str, optional
        :param floor: The name of the floor where this space is located,
             defaults to None
        :type floor: str, optional
        :param space_category: , defaults to None
        :type space_category: str, optional
        :param capacity: Maximum number of people allowed in this space,
             defaults to None
        :type capacity: int, optional
        :param department: Name of the department that owns this space,
             defaults to None
        :type department: str, optional
        :param square_footage: Square footage of this space, defaults to None
        :type square_footage: float, optional
        """

        self.id = id
        self.boundaries = boundaries
        self.path = path
        self.building = building
        self.unique_name = unique_name
        self.facility = facility
        self.floor = floor
        self.space_function = space_function
        self.space_category = space_category
        self.capacity = capacity
        self.department = department
        self.square_footage = square_footage
        self.doors: List[Line] = []

        if not self.capacity and self.is_space_a_meeting_room():
            # default meeting room capacity
            self.capacity = np.random.randint(DEFAULT_MEETING_ROOM_CAPACITY)

    def __eq__(self, other) -> bool:
        """
        Check if two spaces are equal (meaning they are the same space in real
        life). This function does not compare door objects directly as they
        hold references to space objects which in turn hold references to door
        objects and would therefore cause a recursion error.

        :param other: The space to compare this space to.
        :type other: Space
        :return: Whether the spaces are the same or not.
        :rtype: bool
        """
        if (
            self.boundaries == other.boundaries
            and self.path == other.path
            and self.building == other.building
            and self.unique_name == other.unique_name
            and self.facility == other.facility
            and self.floor == other.floor
            and self.space_function == other.space_function
            and self.space_category == other.space_category
            and self.capacity == other.capacity
            and self.department == other.department
            and len(self.doors) == len(other.doors)
        ):
            doors_match = True
            for i in range(len(self.doors)):
                if self.doors[i].path != other.doors[i].path:
                    doors_match = False
                    break
            return doors_match

        return False

    def __hash__(self):
        return id(self)

    def __str__(self):
        return str(self.__dict__.items())

    def _as_dict(self) -> Dict[str, Any]:
        """
         Return this space object as a dictionary. Note: this operation
        ignores any reference to door objects which must be recreated
        at the floorplan level when a space object is to be recreated.

        :return: Dictionary representation of this space.
        :rtype: Dict[str, Any]
        """
        d: Dict[str, Any] = {}
        d["id"] = self.id
        d["boundaries"] = self.boundaries  # This is a list of objects!
        d["path"] = self.path  # This is a list of objects
        d["building"] = self.building
        d["unique_name"] = self.unique_name
        d["space_function"] = self.space_function
        d["space_category"] = self.space_category
        d["capacity"] = self.capacity
        d["department"] = self.department
        d["square_footage"] = self.square_footage
        d["facility"] = self.facility
        d["floor"] = self.floor

        return d

    def is_point_on_space_walls(self, test_point: Point) -> bool:
        """
        Verify if a given point falls on one of the walls of this space.

        :param test_point: The point of interest.
        :type test_point: Point
        :return: Whether the point is on a wall.
        :rtype: bool
        """
        return any(
            wall.length() > 1.0 and gsu.is_point_on_line(wall, test_point)
            for wall in self.path
        )

    def is_point_on_space_boundaries(self, test_point: Point) -> bool:
        """
        Verify if a given point falls on one of the boundaries of this space.

        :param test_point: The point of interest.
        :type test_point: Point
        :return: Whether the point is on a boundary.
        :rtype: bool
        """
        return any(
            bound_line.length() > 1.0
            and gsu.is_point_on_line(bound_line, test_point)
            for bound_line in self.boundaries
        )

    def is_point_inside_space(
        self, test_point: Point, include_boundaries=False
    ) -> bool:
        """
        Check if a given point falls inside this space.

        :param test_point: The point of interest.
        :type test_point: Point
        :param include_boundaries: Whether to include the boundaries or not,
             defaults to False
        :type include_boundaries: bool, optional
        :return: Whether the point falls inside or not.
        :rtype: bool
        """
        # check if point is outside bounding box
        minx, maxx, miny, maxy = self.path.bbox()
        if test_point.x < round(minx) or test_point.x > round(maxx):
            return False
        elif test_point.y < round(miny) or test_point.y > round(maxy):
            return False

        # Check if point is on the door line, for a room
        if not self.is_space_a_hallway() and len(self.doors) > 0:
            for door in self.doors:
                start_door = Point(complex_coords=door.path.start)
                end_door = Point(complex_coords=door.path.end)
                if gsu.on_segment(start_door, test_point, end_door):
                    return True

        # Check if point is on any boundary
        on_boundary = self.is_point_on_space_boundaries(test_point)
        if on_boundary:
            if not include_boundaries:
                return False
            else:
                return True

        # Create a point for line segment from p to infinite
        inf = 1e10
        extreme_points = [
            Point(x=inf, y=test_point.y + 5.0),
            Point(x=test_point.x - 5.0, y=inf),
            Point(x=-inf, y=test_point.y + 5.0),
            Point(x=test_point.x - 5.0, y=-inf),
            Point(x=inf, y=inf),
            Point(x=inf, y=-inf),
            Point(x=-inf, y=inf),
            Point(x=-inf, y=-inf),
        ]

        # Count intersections of the above lines with sides of polygon

        for extreme in extreme_points:
            count = 0
            for line in self.boundaries:
                start_segment = Point(complex_coords=line.start)
                end_segment = Point(complex_coords=line.end)

                # Check if the line segment from 'p' to 'extreme' intersects
                # with the line segment from 'start_segment' to 'end_segment'
                intersects = gsu.do_intersect(
                    start_segment, end_segment, test_point, extreme
                )
                if intersects:
                    count += 1

            # Return true if count is odd, false otherwise
            if count % 2 == 1:
                return True

        return False

    def get_random_internal_point(self) -> Point:
        """
        Return a randomly selected point inside this space.

        :return: xy coordinates of the point.
        :rtype: Point
        """
        xmin, xmax, ymin, ymax = self.path.bbox()
        found = False
        while not found:
            x = np.random.randint(round(xmin) + 1, round(xmax))
            y = np.random.randint(round(ymin) + 1, round(ymax))
            inside_point = Point(x=x, y=y)
            if self.is_point_inside_space(inside_point):
                found = True

        return inside_point

    def is_space_a_hallway(self) -> bool:
        """
        Verify is this space is a hallway.

        :return: Whether this space is a hallway or not.
        :rtype: bool
        """
        return (
            "circulation" in self.space_function.lower()
            or "aisle" in self.space_function.lower()
            or "lobby" in self.space_function.lower()
            or "vestibule" in self.space_function.lower()
        )

    def is_space_an_office(self) -> bool:
        """
        Verify if this space is an office.

        :return: Whether this space is an office or not.
        :rtype: bool
        """
        return (
            "office" in self.space_function.lower()
            or "workstation" in self.space_function.lower()
        )

    def is_space_a_cafeteria(self) -> bool:
        """
        Verify if this space is a cafeteria.

        :return: Whether this space is a cafeteria or not.
        :rtype: bool
        """
        return "cafe" in self.space_function.lower()

    def is_space_a_lab(self) -> bool:
        """
        Verify if this space is a lab.

        :return: Whether this space is a lab or not
        :rtype: bool
        """
        return "lab" in self.space_function.lower()

    def is_space_a_meeting_room(self) -> bool:
        """
        Verify if this space is meeting room.

        :return: Whether this space is a meeting room or not.
        :rtype: bool
        """
        return (
            "conference" in self.space_function.lower()
            or "meeting" in self.space_function.lower()
        )

    def is_space_a_restroom(self) -> bool:
        """
        Verify if this space is a restroom.

        :return: Whether this space is a restroom or not.
        :rtype: bool
        """
        return "restroom" in self.space_function.lower()

    def is_space_vertical(self) -> bool:
        """
        Check if this space is a stair or an elevator that can be used for
        regular navigation.

        :return: Whether the space is vertical.
        :rtype: bool
        """
        return (
            "stair" in self.space_function.lower()
            or "elev" in self.space_function.lower()
        ) and "evac" not in self.space_function.lower()

    def get_space_coords(
        self,
    ) -> Tuple[int, int]:  # Use geometric center of the space
        """
        Compute coordinates of the geometric center of this space

        :return: The xy coordinates of the center.
        :rtype: Tuple[int, int]
        """
        xmin, xmax, ymin, ymax = self.path.bbox()

        x = int((xmax - xmin) / 2.0)
        y = int((ymax - ymin) / 2.0)

        return (x, y)
