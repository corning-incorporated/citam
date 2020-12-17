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
from typing import Tuple, Optional, Dict, Any

from svgpathtools import Path

from citam.engine.map.point import Point
from citam.engine.io.serializer import serializer
from citam.engine.map.space import Space


@serializer
class Door:
    """
    Class to represent and manage a door in a floorplan.

    Note: the in_service, emergency and special_access flags are currently not
    used.
    """

    _intersect_coords: Optional[Tuple[int, int]] = None

    def __init__(
        self,
        path: Path,
        space1: Space = None,
        space2: Space = None,
        space1_id: int = None,
        space2_id: int = None,
        in_service: bool = True,
        emergency_only: bool = False,
        special_access: bool = False,
    ) -> None:
        """
        Create a new door object.

        :param path: The path element describing this door.
        :type path: Path
        :param space1: The first space this door is attached to, defaults to
                None
        :type space1: Space, optional
        :param space2: The second space this door is attached to, defaults to
                None
        :type space2: Space, optional
        :param space1_id: index of the first space id in the floorplan,
                defaults to None
        :type space1_id: int, optional
        :param space2_id: index of the second space id in hte floorplan,
                defaults to None
        :type space2_id: int, optional
        :param in_service: whether this door is in service or not,
                 defaults to True
        :type in_service: bool, optional
        :param emergency_only: whether this is an emergency door or not,
                 defaults to False
        :type emergency_only: bool, optional
        :param special_access: whether special access is needed to use this
                door or not, defaults to False
        :type special_access: bool, optional
        """
        self.path = path
        self.space1 = space1
        self.space2 = space2
        self.space1_id = space1_id
        self.space2_id = space2_id
        self.in_service = in_service
        self.emergency_only = emergency_only
        self.special_access = special_access

    @property
    def intersect_coords(self) -> Tuple[int, int]:
        """
        Return the point where the navigation network intersects with this
        door. If no intersect is found, the midpoint is returned.

        :return: the intersect or midpoint coordinates
        :rtype: Tuple[int, int]
        """
        if self._intersect_coords:
            return self._intersect_coords
        return self.midpoint_coords

    @intersect_coords.setter
    def intersect_coords(self, value: Tuple[int, int]) -> None:
        """
        Set the value of the intersect coordinates with the navnet.

        :param value: The intersect coordinates.
        :type value: Tuple[int, int]
        """
        self._intersect_coords = value

    @property
    def midpoint(self) -> Point:
        """
        Return the midpoint of this door, generally used as where the navnet
        would intersect this door.

        :return: The mid point of this door.
        :rtype: Point
        """
        return Point(
            x=round(self.path.point(0.5).real),
            y=round(self.path.point(0.5).imag),
        )

    @property
    def midpoint_coords(self) -> Tuple[int, int]:
        """
        The xy coordinates of the mid-point of this door.

        :return: xy coordinates of the mid-point
        :rtype: Tuple[int, int]
        """
        return self.midpoint.x, self.midpoint.y

    def is_intersect_and_midpoint_same(self) -> bool:
        """
        Check whether the mid-point and the intersect with the navnet are the
        same.

        :return: Whether they are the same or not.
        :rtype: bool
        """
        return self.intersect_coords == self.midpoint_coords

    def __str__(self):
        str_repr = "\nPath: " + str(self.path) + "\n"
        if self.space1 is not None:
            str_repr += "Space 1: " + str(self.space1.unique_name) + "\n"
        else:
            str_repr += "Space 1: None" + "\n"
        if self.space2 is not None:
            str_repr += "Space 2: " + str(self.space2.unique_name) + "\n"
        else:
            str_repr += "Space 2: None" + "\n"

        return str_repr

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return id(self)

    def _as_dict(self) -> Dict[str, Any]:
        """
        Return this class as a dictionary, useful for JSON serialization.

        Note that only the space ids are kept in the dictionary and not the
        spaces themselves.

        :return: this door represented as a dictionary
        :rtype: Dict[str, Any]
        """
        d = {}
        d["path"] = self.path
        d["space1_id"] = None
        if self.space1:
            d["space1_id"] = self.space1.id
        d["space2_id"] = None
        if self.space2:
            d["space2_id"] = self.space2.id
        d["in_service"] = self.in_service
        d["emergency_only"] = self.emergency_only
        d["special_access"] = self.special_access
        return d
