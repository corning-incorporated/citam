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

import citam.engine.geometry_and_svg_utils as gsu
from citam.engine.point import Point
from citam.engine.map.space import Space

from svgpathtools import Line


def find_closest_parallel_wall(space_boundaries, ref_wall):
    """For a given wall, find other walls in same space that are
    parallel to this (with some x or y overlap) and return the
    closest wall.

    Test cases: aisles (svg paths) with shapes that resemble these letters
                    X, Z, H, L, I, M

    Parameters
    -----------
    space: Space
        The hallway object under consideration
    ref_wall: Line
        The reference wall for which to find closest parallel wall

    Returns
    --------
    Line
        The closest parallel wall
    """
    best_wall = None  # The closest parallel wall to return
    min_dist = 1e10  # Initialize to very large number
    for wall in space_boundaries:
        if wall == ref_wall:
            continue
        if wall.length() <= 1.0:
            continue
        x_overlap, y_overlap = gsu.calculate_x_and_y_overlap(ref_wall, wall)
        if x_overlap == 0 and y_overlap == 0:
            continue
        dot_prod = gsu.calculate_dot_product_between_walls(ref_wall, wall)

        if abs(dot_prod - 1.0) < 0.1:
            # This wall is parallel to ref wall
            dist = gsu.calculate_distance_between_walls(ref_wall, wall)
            if dist < min_dist:
                best_wall = wall
                min_dist = dist

    return best_wall


def find_aisles(space, valid_boundaries, no_repeat=True):
    """Given the svg path of the boundaries of a space,
    find all pairs of 2 walls that define an aisle

    For each wall, find the closest other wall, verify that they
    form an aisle .

    :param Space space:
        The space (hallway) of interest
    :param bool no_repeat:
        Whether to allow a wall to appear in multiple aisles or not
    :return: List of aisles where each aisle is a tuple of 2 walls
    :rtype: list[(Line, Line)]
    """
    aisles = []

    for wall1 in valid_boundaries:
        if wall1.length() <= 1.0:
            continue
        if no_repeat and is_this_wall_part_of_an_aisle(wall1, aisles):
            continue

        wall2 = find_closest_parallel_wall(valid_boundaries, wall1)

        if not wall2:
            continue

        if wall2.length() <= 1.0:
            continue

        if no_repeat and is_this_wall_part_of_an_aisle(wall2, aisles):
            continue

        if (wall1, wall2) in aisles or (wall2, wall1) in aisles:
            continue

        if is_this_an_aisle(wall1, wall2, space):
            aisles.append((wall1, wall2))

    return aisles


def is_this_wall_part_of_an_aisle(wall, aisles):
    """Verify if wall already belongs to an aisle

    Parameters
    -----------
    wall: Line
        The wall of interest
    aisles: list of tuples
        List of aisles

    Returns
    --------
    bool
        Whether this wall is already part of an aisle or not
    """

    return any(wall in [aisle[0], aisle[1]] for aisle in aisles)


def get_aisle_center_point_and_width(aisle):
    """Find the center point and the width of an aisle

    Parameters
    -----------
    aisle: tuple
        Tuple of wall1 and wall2

    Returns
    --------
    Point
        The center point calculated from wall 1
    float
        The width of the aisle
    """

    # Perpendicular vector between the two walls
    V_perp = gsu.calculate_perpendicular_vector(aisle[0], aisle[1])
    # Half way between the two walls from the middle of the first wall
    mid_point = aisle[0].point(0.5)
    center_point = Point(
        x=int(round(mid_point.real + V_perp[0] / 2.0)),
        y=int(round(mid_point.imag + V_perp[1] / 2.0)),
    )
    # Width of aisle
    width = (V_perp[0] ** 2 + V_perp[1] ** 2) ** 0.5

    return center_point, width


def is_this_an_aisle(wall1: Line, wall2: Line, space: Space):
    """Verify that 2 walls form an aisle

    Works by verifying that the center point of this aisle is part
    of the same space

    Parameters
    -----------
    aisle: tuple
        Tuple of wall 1 and wall 2
    space: Space
        The space object where the aisle would be located

    Returns
    --------
    bool
        Whether the 2 walls form an aisle or not
    """
    if wall1 is None or wall2 is None:
        return False

    aisle = (wall1, wall2)
    center_point, _ = get_aisle_center_point_and_width(aisle)
    return bool(space.is_point_inside_space(center_point))


def compute_bounding_box(walls):
    """Computes the bounding box of the floorplan given by all its walls.

    Parameters
    -----------
    No parameter

    Returns
    --------
    xmin: float
        The minimum x value
    ymin: float
        The minimum y value
    xmax: float
        The maximum x value
    ymax: float
        The maximum y value
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
