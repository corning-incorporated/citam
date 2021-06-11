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

from typing import Optional, Tuple, List

from svgpathtools import Line, Path

import citam.engine.map.geometry as g
from citam.engine.map.point import Point
from citam.engine.map.space import Space


def find_closest_parallel_wall(
    space_boundaries: List[Line], ref_wall: Line
) -> Line:
    """
    For a given wall, find other walls in same space that are
    parallel to this (with some x or y overlap) and return the
    closest wall.

    :param space_boundaries: The hallway object under consideration.
    :type space_boundaries: List[Line]
    :param ref_wall: Reference wall for which to find closest parallel wall.
    :type ref_wall: Line
    :return: The closest parallel wall
    :rtype: Line
    """

    best_wall = None  # The closest parallel wall to return
    min_dist = 1e10  # Initialize to very large number
    for wall in space_boundaries:
        if wall == ref_wall or wall.length() <= 1.0:
            continue
        x_overlap, y_overlap = g.calculate_x_and_y_overlap(ref_wall, wall)
        if x_overlap == 0 and y_overlap == 0:
            continue
        dot_prod = g.calculate_dot_product_between_walls(ref_wall, wall)

        if abs(dot_prod - 1.0) < 0.1:
            # This wall is parallel to ref wall
            dist = g.calculate_distance_between_walls(ref_wall, wall)
            if dist < min_dist:
                best_wall = wall
                min_dist = dist

    return best_wall


def is_wall_valid_for_aisle(
    no_repeat: bool, wall: Optional[Line], aisles: List[Tuple[Line, Line]]
) -> bool:
    """
    Check if a wall is valid to be apart of an aisle.

    :param no_repeat: Whether to consider walls that are already part of an
        aisle or not.
    :type no_repeat: bool
    :param wall: the wall of interst
    :type wall: Optional[Line]
    :param aisles: the list of all currently identified aisles.
    :type aisles: List[Tuple[Line, Line]]
    :return: whether this is a valid wall or not.
    :rtype: bool
    """
    if (
        wall is None
        or wall.length() <= 1.0
        or (no_repeat and is_this_wall_part_of_an_aisle(wall, aisles))
    ):
        return False

    return True


def find_aisles(
    space: Space, valid_boundaries: List[Line], no_repeat=True
) -> List[Tuple[Line, Line]]:
    """
    Given the svg path of the boundaries of a space, find all pairs of 2 walls
     that define an aisle (parallel walls with navigable space between them).

    :param space: The space of interest.
    :type space: Space
    :param valid_boundaries: List of valid boundaries to consider.
    :type valid_boundaries: List[Line]
    :param no_repeat: A wall cannot belong to two different aisles,
         defaults to True
    :type no_repeat: bool, optional
    :return: [description]
    :rtype: List[Tuple[Line, Line]]
    """

    aisles: List[Tuple[Line, Line]] = []

    for wall1 in valid_boundaries:
        if not is_wall_valid_for_aisle(no_repeat, wall1, aisles):
            continue
        wall2 = find_closest_parallel_wall(valid_boundaries, wall1)
        if not is_wall_valid_for_aisle(no_repeat, wall2, aisles):
            continue

        if (wall1, wall2) in aisles or (wall2, wall1) in aisles:
            continue

        if is_this_an_aisle(wall1, wall2, space):
            aisles.append((wall1, wall2))

    return aisles


def is_this_wall_part_of_an_aisle(
    wall: Line, aisles: List[Tuple[Line, Line]]
) -> bool:
    """
    Verify if a wall already belongs to an aisle.

    :param wall: The wall of interest.
    :type wall: Line
    :param aisles: List of aisles to check.
    :type aisles: List[Tuple[Line, Line]]
    :return: Whether this wall is part of an aisle or not.
    :rtype: bool
    """

    return any(wall in [aisle[0], aisle[1]] for aisle in aisles)


def get_aisle_center_point_and_width(
    aisle: Tuple[Line, Line]
) -> Tuple[Point, float]:
    """
    Find the center point and the width of an aisle.

    :param aisle: The aisle of interest.
    :type aisle: Tuple[Line, Line]
    :return: The center point and width of the aisle.
    :rtype: Tuple[Point, float]
    """

    # Perpendicular vector between the two walls
    v_perp = g.calculate_perpendicular_vector(aisle[0], aisle[1])
    # Half way between the two walls from the middle of the first wall
    mid_point = aisle[0].point(0.5)
    center_point = Point(
        x=int(round(mid_point.real + v_perp[0] / 2.0)),
        y=int(round(mid_point.imag + v_perp[1] / 2.0)),
    )
    # Width of aisle
    width = (v_perp[0] ** 2 + v_perp[1] ** 2) ** 0.5

    return center_point, width


def is_this_an_aisle(wall1: Line, wall2: Line, space: Space) -> bool:
    """
    Verify that 2 walls form an aisle. Works by verifying that the center point
     of this aisle is part of the same space. Note that this is a rather weak
     definition. Use accordingly.

    :param wall1: The first wall.
    :type wall1: Line
    :param wall2: The second wall.
    :type wall2: Line
    :param space: The space where this aisle would presumably fall.
    :type space: Space
    :return: Whether the two walls form an aisle or not.
    :rtype: bool
    """

    if wall1 is None or wall2 is None:
        return False

    aisle = (wall1, wall2)
    center_point, _ = get_aisle_center_point_and_width(aisle)
    return bool(space.is_point_inside_space(center_point))


def compute_bounding_box(
    walls: List[Line],
) -> Tuple[float, float, float, float]:
    """
    Computes the bounding box of the floorplan given by all its walls and
    return the min and max x and y values.

    :param walls: List of all the walls to consider.
    :type walls: List[Line]
    :return: The minimum and the maximum x and y values
    :rtype: Tuple[float, float, float, float]
    """

    xmin, ymin = 1e10, 1e10  # very large number
    xmax, ymax = 1e-10, 1e-10  # very small number

    for w in walls:
        for x in [w.start.real, w.end.real]:
            if x < xmin:
                xmin = x
            elif x > xmax:
                xmax = x
        for y in [w.start.imag, w.end.imag]:
            if y < ymin:
                ymin = y
            elif y > ymax:
                ymax = y

    return xmin, ymin, xmax, ymax


def generate_closed_path_for_aisle(aisle: Tuple[Line, Line]) -> Path:
    """
    Given an aisle (tuple of two walls), add new walls to create a closed
    path for this aisle.

    :param aisle: Aisle of interest.
    :type aisle: Tuple[Line, Line]
    :return: Closed path for this aisle
    :rtype: Path
    """

    path = Path()
    path += [aisle[0], aisle[1]]

    wall1 = aisle[0]
    wall2 = aisle[1]

    segment1 = Line(start=wall1.start, end=wall2.start)
    segment2 = Line(start=wall1.start, end=wall2.end)

    if segment1.length() <= segment2.length():
        path.append(segment1)
    else:
        path.append(segment2)

    segment3 = Line(start=wall1.end, end=wall2.start)
    segment4 = Line(start=wall1.end, end=wall2.end)

    if segment3.length() <= segment4.length():
        path.append(segment3)
    else:
        path.append(segment4)

    return path


def do_walls_overlap(
    wall1: Line, wall2: Line, max_distance: float = 1.0
) -> bool:
    """
    Verify if two walls overlap.

    Uses the start and end points of each line and verifies if either one
    of them falls on the other segment. If so, it checks if all 4 points
    are collinear and returns True if the dot product and the
    distance between the 2 walls are respectively ~1.0 and ~0.0.

    :param wall1:  line object corresponding to wall 1
    :type wall1: Line
    :param wall2: line object corresponding to wall 2
    :type wall2: Line
    :param max_distance: the max distance beyond which the walls are not
            considered overlapping, defaults to 1.0
    :type max_distance: float, optional
    :return: Whether the walls overlap or not
    :rtype: bool
    """

    x_overlap, y_overlap = g.calculate_x_and_y_overlap(wall1, wall2)

    p1, q1 = extract_end_points(wall1)
    p2, q2 = extract_end_points(wall2)

    if g.is_one_segment_within_the_other(p1, q1, p2, q2) or (
        (x_overlap > 0 or y_overlap > 0)
        and g.do_lines_intersect_at_endpoint(p1, q1, p2, q2)
    ):
        return check_for_collinearity(wall1, wall2, max_distance)

    return False


def extract_end_points(wall: Line) -> Tuple[Point, Point]:
    """
    Extract the end points of a wall returned as integer coordinates.

    :param wall: The wall of interest.
    :type wall: Line
    :return: The end points.
    :rtype: Tuple[Point, Point]
    """
    p = Point(x=round(wall.start.real), y=round(wall.start.imag))
    q = Point(x=round(wall.end.real), y=round(wall.end.imag))
    return p, q


def check_for_collinearity(
    wall1: Line, wall2: Line, max_distance: float
) -> bool:
    """
    Verify that two walls are collinear by making sure all end points are or
    by measuring the distance and angle between the walls.

    :param wall1: The first wall
    :type wall1: Line
    :param wall2: The second wall
    :type wall2: Line
    :param max_distance: The max distance to consider them to be collinear
    :type max_distance: float
    :return: Whether they are collinear or not
    :rtype: bool
    """
    p1, q1 = extract_end_points(wall1)
    p2, q2 = extract_end_points(wall2)

    # Check if all 4 point are collinear
    o1 = g.determine_orientation(p1, q1, p2)
    o2 = g.determine_orientation(p1, q1, q2)

    if o1 == o2 and o1 == 0:
        return True

    # only do this for walls that are diagonal
    tol = 1e-2
    if not (
        abs(p1.x - q1.x) < tol
        or abs(p1.y - q1.y) < tol
        or abs(p2.x - q2.x) < tol
        or abs(p2.y - q2.y) < tol
    ):
        (
            dot_product,
            distance,
        ) = g.calculate_dot_product_and_distance_between_walls(wall1, wall2)
        if (
            dot_product is not None
            and abs(dot_product - 1.0) < 1e-3
            and distance < max_distance
        ):
            return True

    return False
