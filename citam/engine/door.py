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
from typing import Tuple

from citam.engine.point import Point
from citam.engine.serializer import serializer


@serializer
class Door:
    _intersect_coords: tuple = None

    def __init__(
        self,
        path,
        space1,
        space2=None,
        in_service=True,
        emergency_only=False,
        special_access=False,
    ):

        self.path = path
        self.space1 = space1
        self.space2 = space2
        self.in_service = in_service
        self.emergency_only = emergency_only
        self.special_access = special_access

    @property
    def intersect_coords(self) -> tuple:
        if self._intersect_coords:
            return self._intersect_coords
        return self.midpoint_coords

    @intersect_coords.setter
    def intersect_coords(self, value: tuple):
        self._intersect_coords = value

    @property
    def midpoint(self) -> Point:
        return Point(
            x=round(self.path.point(0.5).real),
            y=round(self.path.point(0.5).imag),
        )

    @property
    def midpoint_coords(self) -> Tuple[float, float]:
        return self.midpoint.x, self.midpoint.y

    def is_intersect_and_midpoint_same(self):
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

    def _as_dict(self):
        d = {}
        d['path'] = self.path
        d['space1'] = None
        if self.space1:
            d['space1'] = self.space1.id
        d['space2'] = None
        if self.space2:
            d['space2'] = self.space2.id
        d['in_service'] = self.in_service
        d['.emergency_only'] = self.emergency_only
        d['special_access'] = special_access
        return d
