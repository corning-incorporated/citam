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


import numpy as np
import itertools
import sys

import citam.engine.geometry_and_svg_utils as gsu
from citam.engine.point import Point


class Space:

    def __init__(self, path, boundaries, **attributes):

        self.boundaries = boundaries
        self.path = path
        for key in attributes:
            setattr(self, key, attributes[key])
        self.pick_weight = 1.0
        self.doors = []

        if 'capacity' not in attributes:
            if self.is_space_a_meeting_room():
                # TODO: Use square footage instead, if available
                self.capacity = np.random.randint(25)
            else:
                self.capacity = None

        return

    def __str__(self):

        return str(self.__dict__.items())

    def __sizeof__(self):

        size = sys.getsizeof(self.path)
        for key in self.__dict__:
            size += sys.getsizeof(self.__dict__[key])
            size += sys.getsizeof(key)
        size += sys.getsizeof(self.doors)

        return size

    def is_point_on_space_walls(self, test_point):

        for wall in self.path:
            if wall.length() > 1.0:
                if gsu.is_point_on_line(wall, test_point):
                    return True

        return False

    def is_point_on_space_boundaries(self, test_point):

        for bound_line in self.boundaries:
            if bound_line.length() > 1.0:
                if gsu.is_point_on_line(bound_line, test_point):
                    return True

        return False

    def is_point_inside_space(self,
                              test_point,
                              include_boundaries=False,
                              verbose=False
                              ):

        # check if point is outside bounding box

        minx, maxx, miny, maxy = self.path.bbox()
        if test_point.x < round(minx) or test_point.x > round(maxx):
            if verbose:
                print('X is outside bounds')
            return False
        elif test_point.y < round(miny) or test_point.y > round(maxy):
            if verbose:
                print('Y is outside bounds')
            return False

        # Check if point is on the door line, for a room
        if not self.is_space_a_hallway() and len(self.doors) > 0:
            for door in self.doors:
                start_door = Point(complex_coords=door.start)
                end_door = Point(complex_coords=door.end)
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
        extreme_points = [Point(x=inf, y=test_point.y + 5.0),
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
                intersects = gsu.do_intersect(start_segment,
                                              end_segment,
                                              test_point,
                                              extreme
                                              )
                if intersects:
                    count += 1

            # Return true if count is odd, false otherwise
            if count % 2 == 1:
                if verbose:
                    print('Count is: ', count)
                return True

        if verbose:
            print('Final count is: ', count)

        return False

    def get_random_internal_point(self):

        xmin, xmax, ymin, ymax = self.path.bbox()
        found = False
        while not found:
            x = np.random.randint(round(xmin)+1, round(xmax))
            y = np.random.randint(round(ymin)+1, round(ymax))
            inside_point = Point(x=x, y=y)
            if self.is_point_inside_space(inside_point):
                found = True

        return inside_point

    def is_space_a_hallway(self):

        if 'circulation' in self.space_function.lower() or \
                'aisle' in self.space_function.lower() or \
                'lobby' in self.space_function.lower() or \
                'vestibule' in self.space_function.lower():
            return True
        else:
            return False

    def is_space_an_office(self):

        if 'office' in self.space_function.lower() or \
                'workstation' in self.space_function.lower():
            return True
        else:
            return False

    def is_space_a_cafeteria(self):

        if 'cafe' in self.space_function.lower():
            return True
        else:
            return False

    def is_space_a_lab(self):

        if 'lab' in self.space_function.lower():
            return True
        else:
            return False

    def is_space_a_meeting_room(self):

        if 'conference' in self.space_function.lower() \
                or 'meeting' in self.space_function.lower():
            return True
        else:
            return False

    def is_space_a_restroom(self):

        if 'restroom' in self.space_function.lower():
            return True
        else:
            return False

    def is_space_vertical(self):

        if ('stair' in self.space_function.lower() or
                'elev' in self.space_function.lower()) and \
                'evac' not in self.space_function.lower():
            return True
        else:
            return False

    def get_space_coords(self):  # Use geometric center of the space
        """Compute coordinates of the geometric center of this space

        Parameters
        ------------

        Returns
        --------
        float, float
            x and y coordinates
        """
        xmin, xmax, ymin, ymax = self.path.bbox()

        x = int((xmax-xmin)/2.0)
        y = int((ymax-ymin)/2.0)

        return (x, y)

    def get_all_points_inside_space(self):

        inside_points = []
        xmin, xmax, ymin, ymax = self.path.bbox()

        x_range = range(round(xmin), round(xmax)+1)
        y_range = range(round(ymin), round(ymax)+1)

        for x, y in itertools.product(x_range, y_range):
            p = Point(x=x, y=y)
            if self.is_point_inside_space(p):
                inside_points.append((x, y))

        return inside_points
