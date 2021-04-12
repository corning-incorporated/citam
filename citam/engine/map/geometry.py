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

"""
geometry_and_svg_utils.py

Author: Mardochee Reveil
Date Created: May 12, 2020

"""

import itertools
import numpy as np
import math
from typing import Tuple, Optional, List

from svgpathtools import Line, CubicBezier

from citam.engine.map.point import Point


def on_segment(p: Point, q: Point, r: Point) -> bool:
    """
    Given three points p, q, r, the function checks if point q lies on line
    segment 'pr'

    :param p: First point
    :type p: Point
    :param q: Second point
    :type q: Point
    :param r: Third point
    :type r: Point
    :return: Whether q falls on [pr] or not.
    :rtype: bool
    """

    if (
        q.x <= max(p.x, r.x)
        and q.x >= min(p.x, r.x)
        and q.y <= max(p.y, r.y)
        and q.y >= min(p.y, r.y)
    ):
        return True
    return False


def determine_orientation(p: Point, q: Point, r: Point) -> int:
    """
    Find orientation of ordered triplet (p, q, r).

    The function returns the following values:
      0 --> p, q and r are colinear
      1 --> Clockwise
      2 --> Counterclockwise

    :param p: The first point.
    :type p: Point
    :param q: The second point.
    :type q: Point
    :param r: The third point.
    :type r: Point
    :return: Orientation of the triplet
    :rtype: int
    """

    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)

    if val == 0:
        return 0  # colinear
    elif val > 0:
        return 1  # clockwise
    else:
        return 2  # counterclockwise


def do_intersect(p1: Point, q1: Point, p2: Point, q2: Point) -> bool:
    """
    Check if two segments as given by their respective end points intersect.

    :param p1: First endpoint of first segment.
    :type p1: Point
    :param q1: Second endpoint of first segment.
    :type q1: Point
    :param p2: First endpoint of second segment.
    :type p2: Point
    :param q2: Second endpoint of second segment.
    :type q2: Point
    :return: True if segments intersect, False otherwise.
    :rtype: bool
    """
    # Find the four orientations needed for general and special cases
    o1 = determine_orientation(p1, q1, p2)
    o2 = determine_orientation(p1, q1, q2)
    o3 = determine_orientation(p2, q2, p1)
    o4 = determine_orientation(p2, q2, q1)

    #  General case
    if o1 != o2 and o3 != o4:
        return True

    #  Special Cases
    #  p1, q1 and p2 are colinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1):
        return True

    #  p1, q1 and p2 are colinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1):
        return True

    #  p2, q2 and p1 are colinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2):
        return True

    #  p2, q2 and q1 are colinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2):
        return True

    return False  # Doesn't fall in any of the above cases


def is_one_segment_within_the_other(
    p1: Point, q1: Point, p2: Point, q2: Point
) -> bool:
    """
    Check if one of two lines defined by p1-q1 and p2-q2 respectively falls
    within the other.

    :param p1: The first endpoint of the first segment.
    :type p1: Point
    :param q1: The second endpoint of the first segment.
    :type q1: Point
    :param p2: The first endpoint of the second segment.
    :type p2: Point
    :param q2: The second endpoint of the second segment.
    :type q2: Point
    :return: True, if [p1q1] is included in [p2q2] or vice-versa
    :rtype: bool
    """
    return bool(
        (
            (on_segment(p1, p2, q1) and on_segment(p1, q2, q1))
            or (on_segment(p2, p1, q2) and on_segment(p2, q1, q2))
            or (p1 == p2 and q1 == q2)
            or (p1 == q2 and q1 == p2)
        )
    )


def do_lines_intersect_at_endpoint(
    p1: Point, q1: Point, p2: Point, q2: Point
) -> bool:
    """
    Check if one of the lines start or ends on the other line.

    :param p1: The first endpoint of the first segment.
    :type p1: Point
    :param q1: The second endpoint of the first segment.
    :type q1: Point
    :param p2: The first endpoint of the second segment.
    :type p2: Point
    :param q2: The second endpoint of the second segment.
    :type q2: Point
    :return: True, if p1 or q1 belongs to [p2q2] and vice-versa
    :rtype: bool
    """
    """

    """
    return bool(
        (
            on_segment(p1, p2, q1)
            or on_segment(p1, q2, q1)
            or on_segment(p2, p1, q2)
            or on_segment(p2, q1, q2)
        )
    )


def calculate_normal_vector_between_walls(
    wall1: Line, wall2: Line
) -> np.ndarray:
    """
    Given two Line objects, compute the normal vector between them (computed
    with respect to Wall 1).

    :param wall1: The first wall
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :return: the perpendicular vector
    :rtype: np.ndarray
    """
    vector_for_wall1, _, bridge_vector = _compute_key_vectors(wall1, wall2)

    # Projection of bredge vector onto wall1 vector
    coeff = np.dot(vector_for_wall1, bridge_vector) / (
        (np.linalg.norm(vector_for_wall1)) ** 2
    )
    wproj = vector_for_wall1 * coeff

    return bridge_vector - wproj


# Just a different name for the same function
calculate_perpendicular_vector = calculate_normal_vector_between_walls


def _compute_key_vectors(
    wall1: Line, wall2: Line
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Helper function used to compute the vector for wall1 and wall2 as well as
    an arbitrary vector W joining both lines.

    :param wall1: The first wall.
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :return: The key vectors.
    :rtype: Tuple[np.ndarray, np.ndarray, np.ndarray]
    """

    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))
    q2 = Point(x=round(wall2.end.real), y=round(wall2.end.imag))

    # Calculate distance between the 2 walls as well as their dot products
    V1 = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1
    V2 = np.array([q2.x - p2.x, q2.y - p2.y])  # Vector of wall 2
    # Arbitrary vector W joining wall 1 and wall 2 (let's use p1 and p2)
    W = np.array([p2.x - p1.x, p2.y - p1.y])

    return V1, V2, W


def calculate_dot_product_and_distance_between_walls(
    wall1: Line, wall2: Line
) -> Tuple[Optional[float], float]:
    """
    Compute the dot product and distance between two walls.

    :param wall1: The first wall
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :return: the dot product and the distance
    :rtype: Tuple[Optional[float], float]
    """

    return (
        calculate_dot_product_between_walls(wall1, wall2),
        calculate_distance_between_walls(wall1, wall2),
    )


def calculate_dot_product_between_walls(
    wall1: Line, wall2: Line
) -> np.ndarray:
    """
    Calculate the dot product between 2 walls. NB: If the 2 walls are parallel,
     the dot product will equal 1.0

    :param wall1: The first wall
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :return: The dot product value between the two walls
    :rtype: np.ndarray
    """

    dot_product = None

    V1, V2, W = _compute_key_vectors(wall1, wall2)
    norm_v1 = np.linalg.norm(V1)
    norm_v2 = np.linalg.norm(V2)

    if norm_v1 * norm_v2 != 0:
        dot_product = abs(np.dot(V1, V2) / (norm_v1 * norm_v2))

    return dot_product


def calculate_distance_between_walls(wall1: Line, wall2: Line) -> float:
    """
    Calculate distance between 2 walls.

    This function assumes the 2 walls are parallel but does not
    check for that. Calculate the dot product first to verify yourself.
    Calculate a vector perpendicular to both walls and returns its
    euclidian norm.

    :param wall1: The first wall
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :return: distance between the walls
    :rtype: float
    """
    v_perp = calculate_perpendicular_vector(wall1, wall2)
    return np.linalg.norm(v_perp)


def calculate_x_and_y_overlap(wall1: Line, wall2: Line) -> Tuple[float, float]:
    """
    Given two lines, calculate their x and y overlaps (e.g. if the x values
    for line 1 and 2 are [0, 6] and [3, 10] resp, the overlap is [3, 6] = 3).

    :param wall1: The first wall
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :return: The x and y overlaps in distance units
    :rtype: Tuple[float, float]
    """
    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))
    q2 = Point(x=round(wall2.end.real), y=round(wall2.end.imag))

    max1 = max(p1.x, q1.x)
    min1 = min(p1.x, q1.x)
    max2 = max(p2.x, q2.x)
    min2 = min(p2.x, q2.x)
    x_overlap = max(0, min(max1, max2) - max(min1, min2))

    max1 = max(p1.y, q1.y)
    min1 = min(p1.y, q1.y)
    max2 = max(p2.y, q2.y)
    min2 = min(p2.y, q2.y)
    y_overlap = max(0, min(max1, max2) - max(min1, min2))

    return x_overlap, y_overlap


def round_coords(wall: Line) -> Line:
    """
    Given a line, round the its start and end coordinates to the nearest
    integer.

    :param wall: The initial wall.
    :type wall: Line
    :return: The wall will rounded up coordinates.
    :rtype: Line
    """
    p = Point(complex_coords=wall.start)
    q = Point(complex_coords=wall.end)

    p.x = round(p.x)
    p.y = round(p.y)

    q.x = round(q.x)
    q.y = round(q.y)

    wall = Line(start=p.complex_coords, end=q.complex_coords)

    return wall


def sample_random_points_from_line(
    line: Line, npoints=10
) -> List[Tuple[int, int]]:
    """
    Sample n random points from line

    :param line: the line to sample from.
    :type line: Line
    :param npoints: The number of points to sample, defaults to 10
    :type npoints: int, optional
    :return: The list of points
    :rtype: List[Tuple[int, int]]
    """
    x1 = line.start.real
    y1 = line.start.imag

    x2 = line.end.real
    y2 = line.end.imag

    x = list(x1 + np.round((x2 - x1) * np.random.rand(npoints)))
    y = list(y1 + np.round((y2 - y1) * np.random.rand(npoints)))

    return list(itertools.product(x, y))[:npoints]


def create_parallel_line(line: Line, d=1) -> Line:
    """
    Create a parallel line at a distance 'd' from a reference line. Both x
    and y are changed by d.

    :param line: The reference line.
    :type line: Line
    :param d: The distance at which to create the parallel line,
         defaults to 1
    :type d: int, optional
    :return: [description]
    :rtype: Line
    """

    p1 = Point(x=round(line.start.real), y=round(line.start.imag))
    q1 = Point(x=round(line.end.real), y=round(line.end.imag))

    V = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1

    new_x1 = line.start.real + d
    new_y1 = line.start.imag + d

    return Line(
        start=complex(new_x1, new_y1),
        end=complex(new_x1 + V[0], new_y1 + V[1]),
    )


def compute_new_door_line(room_wall: Line, door_size=2.0) -> Line:
    """
    Compute a door line to add to a wall. This door line is computed from
    one of the end points of the wall.

    :param room_wall: The reference wall.
    :type room_wall: Line
    :param door_size: the size of the door, defaults to 2.0
    :type door_size: float, optional
    :return: The door line.
    :rtype: Line
    """
    # Add a door to room wall
    start_x = room_wall.start.real
    start_y = room_wall.start.imag

    # vector between start and end points
    vx = room_wall.end.real - room_wall.start.real
    vy = room_wall.end.imag - room_wall.start.imag
    v_norm = math.sqrt(vx ** 2 + vy ** 2)
    if v_norm == 0:
        return None

    # Unit vector
    vx = vx / v_norm
    vy = vy / v_norm

    # End point of door
    end_x = start_x + door_size * vx
    end_y = start_y + door_size * vy

    # Start and end points of door line
    p = Point(start_x, start_y)
    q = Point(end_x, end_y)

    return Line(start=p.complex_coords, end=q.complex_coords)


def find_door_line(cubic_bezier: CubicBezier) -> Line:
    """
    Given a cubic bezier, find the line that is most likely to corresponds to
    the door line.

    :param cubic_bezier: The cubic bezier to analyze.
    :type cubic_bezier: CubicBezier
    :return: The most likely door line.
    :rtype: Line
    """
    # start and end point

    ax = cubic_bezier.start.real
    ay = cubic_bezier.start.imag

    cx = cubic_bezier.end.real
    cy = cubic_bezier.end.imag

    # Midpoint of the arc

    bx = cubic_bezier.point(0.5).real
    by = cubic_bezier.point(0.5).imag

    # Let the center of the circle be x, y
    # The lines A to center, B to center and C to center all have the same
    # length (radius of the circle).
    # We use that relationship to calculate x and y

    a1 = ax - bx
    b1 = ay - by

    a2 = bx - cx
    b2 = by - cy

    d1 = 0.5 * (ax ** 2 - bx ** 2 + ay ** 2 - by ** 2)
    d2 = 0.5 * (bx ** 2 - cx ** 2 + by ** 2 - cy ** 2)

    y = (d2 - a2 * d1 / a1) / (b2 - a2 * b1 / a1)
    x = (d1 - b1 * y) / a1

    if abs(x - ax) < 3.0:
        x = ax
    elif abs(x - cx) < 3.0:
        x = cx

    if abs(y - ay) < 3.0:
        y = ay
    elif abs(y - cy) < 3.0:
        y = cy

    center = Point(round(x), round(y))
    arc_start = Point(x=round(ax), y=round(ay))
    arc_end = Point(x=round(cx), y=round(cy))

    # Finally, the line of interest is line 3 below based on
    # assuming that the start point of the bezier is where
    # the door starts

    door_line1 = Line(
        start=arc_start.complex_coords, end=center.complex_coords
    )

    door_line2 = Line(start=arc_end.complex_coords, end=center.complex_coords)

    return door_line1, door_line2


def align_to_reference(reference_line: Line, test_line: Line) -> Line:
    """
    Given a reference line, modify a test line to be parallel with the
    reference.

    :param reference_line: The reference line.
    :type reference_line: Line
    :param test_line: The test line.
    :type test_line: Line
    :return: The new line, translated to align with the reference.
    :rtype: Line
    """

    # This only works for horizontal or vertical lines
    dx = reference_line.end.real - reference_line.start.real
    dy = reference_line.end.imag - reference_line.start.imag

    if dx == 0:
        end_x = test_line.start.real  # end x is the same as start x
        end_y = test_line.end.imag  # end y remains as is
    elif dy == 0:
        end_y = test_line.start.imag  # end y is the same as start y
        end_x = test_line.end.real  # end x remains as is
    else:
        return test_line

    return Line(start=test_line.start, end=complex(end_x, end_y))


def is_point_on_line(line: Line, p_test: Point, tol: float = 1e-3) -> bool:
    """
    Verify if a test point is on a given Line.

    :param line: The Line of interest.
    :type line: Line
    :param p_test: The test point.
    :type p_test: Point
    :param tol: The tolerance within which the point is labeled as belonging
        to the line, defaults to 1e-3
    :type tol: float, optional
    :return: Whether the point falls on line or not.
    :rtype: bool
    """

    if complex(p_test.x, p_test.y) in [line.start, line.end]:
        return True

    p = Point(x=line.start.real, y=line.start.imag)
    q = Point(x=line.end.real, y=line.end.imag)
    if on_segment(p, p_test, q):
        test_line = Line(start=line.start, end=complex(p_test.x, p_test.y))
        normal1 = line.normal(0.5)
        normal2 = test_line.normal(0.5)
        if (
            abs(normal1.real - normal2.real) < tol
            and abs(normal1.imag - normal2.imag) < tol
        ):
            return True

    return False


def remove_segment_from_wall(wall: Line, segment: Line) -> List[Line]:
    """
    Given a wall, subtract an arbitrary segment from the wall and return the
    remaining wall segments.

    :param wall: The wall to subtract from.
    :type wall: Line
    :param segment: The segment to subtract.
    :type segment: Line
    :return: The remaining segments.
    :rtype: List[Line]
    """
    p_wall = Point(complex_coords=wall.start)
    q_wall = Point(complex_coords=wall.end)

    p_segment = Point(complex_coords=segment.start)
    q_segment = Point(complex_coords=segment.end)

    if p_segment == q_segment:  # This is just one point. Keep wall the same
        return [wall]

    line1 = Line(start=segment.start, end=wall.start)
    line2 = Line(start=segment.end, end=wall.end)
    line3 = Line(start=segment.start, end=wall.end)
    line4 = Line(start=segment.end, end=wall.start)

    valid_lines = []
    for line in [line1, line2, line3, line4]:
        p1 = Point(complex_coords=line.start)
        q1 = Point(complex_coords=line.end)
        if on_segment(p1, p_segment, q1) and on_segment(p1, q_segment, q1):
            # if both start and end of segment belong to
            # line or wall, it's invalid
            pass
        elif not on_segment(p_wall, p1, q_wall) or not on_segment(
            p_wall, q1, q_wall
        ):
            # If both start and end of line don't belong to wall, it's
            # invalid
            pass
        else:
            valid_lines.append(line)

    valid_lines = [vl for vl in valid_lines if vl.length() > 1]

    return valid_lines
