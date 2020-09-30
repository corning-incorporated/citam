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

"""
geometry_and_svg_utils.py

Author: Mardochee Reveil
Date Created: May 12, 2020

"""

import itertools
import numpy as np
import math
from svgpathtools import Line, Path, CubicBezier

from citam.engine.point import Point


def on_segment(p, q, r):
    """Given three colinear points p, q, r, the function checks if
       point q lies on line segment 'pr'
    """
    if (q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and
            q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y)):
        return True
    return False


#  To find orientation of ordered triplet (p, q, r).
#  The function returns following values
#  0 --> p, q and r are colinear
#  1 --> Clockwise
#  2 --> Counterclockwise

def determine_orientation(p, q, r):

    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)

    if val == 0:
        return 0   # colinear
    elif val > 0:
        return 1  # clockwise
    else:
        return 2  # counterclockwise


#  The function that returns true if line segment 'p1q1'
#  and 'p2q2' intersect.

def do_intersect(p1, q1, p2, q2):
    """Check if two lines as given by their respective end points intersect.
    """
    # Find the four orientations needed for general and
    # special cases
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
    if (o4 == 0 and on_segment(p2, q1, q2)):
        return True

    return False   # Doesn't fall in any of the above cases


def generate_closed_path_for_aisle(aisle):
    """Given an aisle (tuple of two walls), add new walls to create a closed
    path for this aisle.
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


def is_one_segment_within_the_other(p1, q1, p2, q2):
    """
    Check if one of two lines defined by p1-q1 and p2-q2 respectively falls
    within the other.
    """
    if (on_segment(p1, p2, q1) and on_segment(p1, q2, q1)) or \
            (on_segment(p2, p1, q2) and on_segment(p2, q1, q2)) or \
            (p1 == p2 and q1 == q2) or (p1 == q2 and q1 == p2):

        return True

    return False


def do_lines_intersect_at_endpoint(p1, q1, p2, q2):
    """
    Check if one of the lines start or ends on the other line.
    """
    if on_segment(p1, p2, q1) or on_segment(p1, q2, q1) or \
            on_segment(p2, p1, q2) or on_segment(p2, q1, q2):
        return True

    return False


def do_walls_overlap(wall1, wall2, max_distance=1.0, verbose=False):
    """
    Verifies if two walls overlap in space.

    Uses the start and end points of each line and verifies if either one
    of them falls on the other segment. If so, it checks if all 4 points
    are collinear and returns True if the dot product and the
    distance between the 2 walls are respectively ~1.0 and ~0.0.

    :param Line wall1:
        line object corresponding to wall 1
    :param Line wall2:
        line object corresponding to wall 2
    :return: do_overlap (True if walls overlap)
    :rtype: boolean
    """

    x_overlap, y_overlap = calculate_x_and_y_overlap(wall1, wall2)

    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))
    q2 = Point(x=round(wall2.end.real), y=round(wall2.end.imag))

    on_segment_test = False

    if is_one_segment_within_the_other(p1, q1, p2, q2):
        on_segment_test = True

    # only one point from line being on the other is necessary
    elif x_overlap > 0 or y_overlap > 0:
        if do_lines_intersect_at_endpoint(p1, q1, p2, q2):
            on_segment_test = True

    if on_segment_test:

        # Check if all 4 point are collinear
        o1 = determine_orientation(p1, q1, p2)
        o2 = determine_orientation(p1, q1, q2)

        if o1 == o2 and o1 == 0:
            return True

        # only do this for walls that are diagonal
        tol = 1e-2
        if abs(p1.x - q1.x) < tol or abs(p1.y - q1.y) < tol or \
                abs(p2.x - q2.x) < tol or abs(p2.y - q2.y) < tol:
            # At least one of the walls is horizontal or vertical
            pass
        else:
            dot_product, distance = \
                calculate_dot_product_and_distance_between_walls(wall1, wall2)
            if dot_product is not None:
                if abs(dot_product - 1.0) < 1e-3 and distance < max_distance:
                    return True

    return False


def calculate_normal_vector_between_walls(wall1, wall2):
    """Given two Line objects, compute the normal vector between them.
    """
    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))

    V1 = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1
    V1_norm = np.linalg.norm(V1)

    # Arbitrary vector W joining wall 1 and wall 2 (let's use p1 and p2)
    W = np.array([p2.x - p1.x, p2.y - p1.y])
    # Projection of W onto V1
    coeff = np.dot(V1, W)/((V1_norm)**2)
    W_proj = V1*coeff
    # Perpendicular vector between the two walls
    V_perp = W - W_proj

    return V_perp


def calculate_dot_product_and_distance_between_walls(wall1, wall2):

    dot_product = None

    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))
    q2 = Point(x=round(wall2.end.real), y=round(wall2.end.imag))

    # Calculate distance between the 2 walls as well as their dot products
    V1 = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1
    V1_norm = np.linalg.norm(V1)
    V2 = np.array([q2.x - p2.x, q2.y - p2.y])  # Vector of wall 2
    V2_norm = np.linalg.norm(V2)
    # Arbitrary vector W joining wall 1 and wall 2 (let's use p1 and p2)
    W = np.array([p2.x - p1.x, p2.y - p1.y])
    # Projection of W onto V1
    coeff = np.dot(V1, W)/((V1_norm)**2)
    W_proj = V1*coeff
    # Perpendicular vector between the two walls
    V_perp = W - W_proj
    # Distance and dot products of the 2 walls
    distance = np.linalg.norm(V_perp)

    if V1_norm*V2_norm != 0:
        dot_product = abs(np.dot(V1, V2)/(V1_norm*V2_norm))

    return dot_product, distance


def calculate_dot_product_between_walls(wall1, wall2):
    """Calculate the dot product between 2 walls.

    If the 2 walls are parallel, the dot product will equal 1.0

    Parameters
    -----------
    wall1: Line
        The first wall
    wall2: Line
        The second wall

    Returns
    --------
    float
        The dot product value between the two walls

    """
    dot_product = None

    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))
    q2 = Point(x=round(wall2.end.real), y=round(wall2.end.imag))

    # Calculate distance between the 2 walls as well as their dot products
    V1 = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1
    V1_norm = np.linalg.norm(V1)
    V2 = np.array([q2.x - p2.x, q2.y - p2.y])  # Vector of wall 2
    V2_norm = np.linalg.norm(V2)

    # if V1_norm*V2_norm != 0:
    dot_product = abs(np.dot(V1, V2)/(V1_norm*V2_norm))

    return dot_product


def calculate_perpendicular_vector(wall1, wall2):
    """Calculate a perpendicular vector between 2 walls.

    This function assumes the 2 walls are parallel but does not
    check for that. Calculate the dot product first to verify yourself.

    Parameters
    -----------
    wall1: Line
        The first wall
    wall2: Line
        The second wall

    Returns
    --------
    float: distance between the walls

    """

    p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
    q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))

    p2 = Point(x=round(wall2.start.real), y=round(wall2.start.imag))

    V1 = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1
    V1_norm = np.linalg.norm(V1)
    # Arbitrary vector W joining wall 1 and wall 2 (let's use p1 and p2)
    W = np.array([p2.x - p1.x, p2.y - p1.y])
    # Projection of W onto V1
    coeff = np.dot(V1, W)/((V1_norm)**2)
    W_proj = V1*coeff
    # Perpendicular vector between the two walls
    V_perp = W - W_proj

    return V_perp


def calculate_distance_between_walls(wall1, wall2):
    """Calculate distance between 2 walls.

    This function assumes the 2 walls are parallel but does not
    check for that. Calculate the dot product first to verify yourself.
    Calculate a vector perpendicular to both walls and returns its
    euclidian norm.

    Parameters
    -----------
    wall1: Line
        The first wall
    wall2: Line
        The second wall

    Returns
    --------
    float: distance between the walls
    """
    V_perp = calculate_perpendicular_vector(wall1, wall2)
    distance = np.linalg.norm(V_perp)

    return distance


def calculate_x_and_y_overlap(wall1, wall2):
    """Give two lines, calculate their x and y overlaps.
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


def round_coords(wall):
    """Given a line, round the its start and end coordinates
    """
    p = Point(complex_coords=wall.start)
    q = Point(complex_coords=wall.end)

    p.x = round(p.x)
    p.y = round(p.y)

    q.x = round(q.x)
    q.y = round(q.y)

    wall = Line(start=p.complex_coords, end=q.complex_coords)

    return wall


def subtract_walls(wall1, wall2):
    """
    Removes wall 2 from wall 1, assuming the 2 walls share the same start or
    end points and therefore returns only one wall segment.
    A more general version of this is remove overlap from wall
    which can returns multiple new segments.
    """

    line1 = Line(start=wall1.start, end=wall2.start)
    line2 = Line(start=wall1.end, end=wall2.end)
    line3 = Line(start=wall1.start, end=wall2.end)
    line4 = Line(start=wall1.end, end=wall2.start)

    p2 = Point(complex_coords=wall2.start)
    q2 = Point(complex_coords=wall2.end)
    valid_lines = []
    for line in [line1, line2, line3, line4]:
        p1 = Point(complex_coords=line.start)
        q1 = Point(complex_coords=line.end)
        if on_segment(p1, p2, q1) and on_segment(p1, q2, q1):
            # if both start and end of wall 2 belongs to line, it's invalid
            pass
        else:
            valid_lines.append(line)

    lengths = [v.length() for v in valid_lines]
    index = lengths.index(max(lengths))

    new_wall = valid_lines[index]

    return new_wall


# def is_this_an_aisle(wall1, wall2):
#     """Test if this tuple of walls correspond to an aisle.

#     If the center point between the two walls
#     """
#     max_aisle_width = 8.0

#     if wall1.length() < max_aisle_width or wall2.length() < max_aisle_width:
#         return False

#     x_overlap, y_overlap = calculate_x_and_y_overlap(wall1, wall2)
#     dot_product, distance = \
#         calculate_dot_product_and_distance_between_walls(wall1, wall2)

#     if dot_product is not None:
#         if x_overlap > 0 or y_overlap > 0:
#             if abs(dot_product - 1.0) < 1e-3 and \
#                 distance <= max_aisle_width and \
#                     distance > 1.0:

#                 return True

#     return False


def sample_random_points_from_line(line, npoints=10):
    """Sample n random points from line
    """
    x1 = line.start.real
    y1 = line.start.imag

    x2 = line.end.real
    y2 = line.end.imag

    x = list(x1 + np.round((x2 - x1)*np.random.rand(npoints)))
    y = list(y1 + np.round((y2 - y1)*np.random.rand(npoints)))

    return list(itertools.product(x, y))[:npoints]


def create_parallel_line(line, side=1):

    p1 = Point(x=round(line.start.real), y=round(line.start.imag))
    q1 = Point(x=round(line.end.real), y=round(line.end.imag))

    V = np.array([q1.x - p1.x, q1.y - p1.y])  # Vector of wall 1

    new_x1 = line.start.real + side
    new_y1 = line.start.imag + side

    new_line = Line(start=complex(new_x1, new_y1),
                    end=complex(new_x1 + V[0], new_y1 + V[1])
                    )
    return new_line


def create_door_in_room_wall(room_wall, door_size=2.0):

    # Add a door to room wall
    start_x = room_wall.start.real
    start_y = room_wall.start.imag

    # vector between start and end points

    Vx = room_wall.end.real - room_wall.start.real
    Vy = room_wall.end.imag - room_wall.start.imag
    V_norm = math.sqrt(Vx**2 + Vy**2)
    if V_norm == 0:
        return None

    Vx = Vx/V_norm
    Vy = Vy/V_norm

    end_x = start_x + door_size*Vx
    end_y = start_y + door_size*Vy

    p = Point(start_x, start_y)
    q = Point(end_x, end_y)

    door = Line(start=p.complex_coords, end=q.complex_coords)

    return door


def find_door_line(cubic_bezier):   # TODO: Create unit test for this function

    # start and end point

    Ax = cubic_bezier.start.real
    Ay = cubic_bezier.start.imag

    Cx = cubic_bezier.end.real
    Cy = cubic_bezier.end.imag

    # Midpoint of the arc

    Bx = cubic_bezier.point(0.5).real
    By = cubic_bezier.point(0.5).imag

    # Let the center of the circle be x, y
    # The lines A to center, B to center and C to center all have the same
    # length (radius of the circle).
    # We use that relationship to calculate x and y

    a1 = Ax - Bx
    b1 = Ay - By

    a2 = Bx - Cx
    b2 = By - Cy

    d1 = 0.5*(Ax**2 - Bx**2 + Ay**2 - By**2)
    d2 = 0.5*(Bx**2 - Cx**2 + By**2 - Cy**2)

    y = (d2 - a2*d1/a1) / (b2 - a2*b1/a1)
    x = (d1 - b1*y)/a1

    if abs(x - Ax) < 3.0:
        x = Ax
    elif abs(x - Cx) < 3.0:
        x = Cx

    if abs(y - Ay) < 3.0:
        y = Ay
    elif abs(y - Cy) < 3.0:
        y = Cy

    center = Point(round(x), round(y))
    arc_start = Point(x=round(Ax), y=round(Ay))
    arc_end = Point(x=round(Cx), y=round(Cy))

    # print('New control point: ', x, y)
    # Finally, the line of interest is line 3 below based on
    # assuming that the start point of the bezier is where
    # the door starts

    door_line1 = Line(start=arc_start.complex_coords,
                      end=center.complex_coords
                      )

    door_line2 = Line(start=arc_end.complex_coords,
                      end=center.complex_coords
                      )

    return door_line1, door_line2


def align_to_reference(reference_line, test_line):

    # This only works for horizontal or vertical lines
    dx = reference_line.end.real - reference_line.start.real
    dy = reference_line.end.imag - reference_line.start.imag

    if dx == 0:
        end_x = test_line.start.real   # end x is the same as start x
        end_y = test_line.end.imag   # end y remains as is
    elif dy == 0:
        end_y = test_line.start.imag  # end y is the same as start y
        end_x = test_line.end.real  # end x remains as is
    else:
        return test_line

    new_line = Line(start=test_line.start,
                    end=complex(end_x, end_y))

    return new_line


def is_point_on_line(line, p_test, tol=1e-3):
    """Verify if a test point is on a given Line

    Parameters
    -----------
    line: Line
        The line of interest
    p_test: Point
        The point of interest

    Returns
    --------
    bool
        Whether the point falls on the line or not
    """

    if complex(p_test.x, p_test.y) == line.start or \
            complex(p_test.x, p_test.y) == line.end:
        return True

    p = Point(x=line.start.real, y=line.start.imag)
    q = Point(x=line.end.real, y=line.end.imag)
    if on_segment(p, p_test, q):
        test_line = Line(start=line.start, end=complex(p_test.x, p_test.y))
        normal1 = line.normal(0.5)
        normal2 = test_line.normal(0.5)
        if abs(normal1.real - normal2.real) < tol and \
                abs(normal1.imag - normal2.imag) < tol:
            return True

    return False


def remove_segment_from_wall(wall, segment, verbose=False):

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
        if on_segment(p1, p_segment, q1) and\
                on_segment(p1, q_segment, q1):
            # if both start and end of segment belong to
            # line or wall, it's invalid
            pass
        elif not on_segment(p_wall, p1, q_wall) or\
                not on_segment(p_wall, q1, q_wall):
            # If both start and end of line don't belong to wall, it's
            # invalid
            pass
        else:
            valid_lines.append(line)

    valid_lines = [vl for vl in valid_lines if vl.length() > 1]

    return valid_lines


if __name__ == "__main__":

    cubic_bezier = CubicBezier(start=(3455.0684 + 2204.5262j),
                               control1=(3456.1214 + 2189.3597j),
                               control2=(3468.8934 + 2177.69j),
                               end=(3484.0928 + 2178.006j)
                               )

    door = find_door_line(cubic_bezier)

    print('Correct answer: 3455 to 3486 and y = 2208')

    pass
