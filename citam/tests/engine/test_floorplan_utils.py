import citam.engine.map.utils as fu

from svgpathtools import Line


def test_get_aisle_center_point_and_width_1(rect_floorplan):
    space = rect_floorplan.spaces[0]
    wall1 = list(space.boundaries)[0]
    wall2 = list(space.boundaries)[2]
    aisle = (wall1, wall2)
    c_point, width = fu.get_aisle_center_point_and_width(aisle)

    assert c_point is not None
    assert width == 80
    assert c_point.x == 125
    assert c_point.y == 40


def test_find_closest_parallel_wall_1(x_floorplan):
    space_boundaries = x_floorplan.spaces[0].boundaries
    ref_wall = list(space_boundaries)[0]
    cp_wall = fu.find_closest_parallel_wall(space_boundaries, ref_wall)

    assert cp_wall is not None
    assert cp_wall == list(space_boundaries)[2]


def test_find_closest_parallel_wall_2(x_floorplan):
    space_boundaries = x_floorplan.spaces[0].boundaries
    ref_wall = list(space_boundaries)[1]
    cp_wall = fu.find_closest_parallel_wall(space_boundaries, ref_wall)

    assert cp_wall is not None
    assert cp_wall == list(space_boundaries)[10]


def test_find_closest_parallel_wall_3(x_floorplan):
    space_boundaries = x_floorplan.spaces[0].boundaries
    ref_wall = list(space_boundaries)[3]
    cp_wall = fu.find_closest_parallel_wall(space_boundaries, ref_wall)

    assert cp_wall is not None
    assert cp_wall == list(space_boundaries)[5]


def test_find_aisles(x_floorplan):
    """Test cases: aisles with shapes that resemble these letters
    X, Z, H, L, I, M also inner and outer rectangles
    """
    valid_boundaries = x_floorplan.spaces[0].boundaries
    aisles = fu.find_aisles(x_floorplan.spaces[0], valid_boundaries)

    assert len(aisles) == 4


def test_get_aisle_center_point_and_width_2(x_floorplan):
    space = x_floorplan.spaces[0]
    wall1 = list(space.boundaries)[0]
    wall2 = list(space.boundaries)[2]
    aisle = (wall1, wall2)
    c_point, width = fu.get_aisle_center_point_and_width(aisle)

    assert c_point is not None
    assert round(width) == 7
    assert c_point.x == -26
    assert c_point.y == 20


def test_is_this_an_aisle(x_floorplan, aisle_from_x_floorplan):
    space = x_floorplan.spaces[0]
    wall1 = aisle_from_x_floorplan[0]
    wall2 = aisle_from_x_floorplan[1]
    is_aisle = fu.is_this_an_aisle(wall1, wall2, space)

    assert is_aisle is True


def test_compute_bounding_box():
    walls = [
        Line(start=complex(-250, 0), end=complex(965, 63)),
        Line(start=complex(69, 326), end=complex(-96, 682)),
        Line(start=complex(26.4, 68.3), end=complex(-96, 98.25)),
    ]
    minx, miny, maxx, maxy = fu.compute_bounding_box(walls)
    assert minx == -250
    assert miny == 0
    assert maxx == 965
    assert maxy == 682
