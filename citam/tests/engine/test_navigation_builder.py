from citam.engine.navigation_builder import NavigationBuilder
from citam.engine.point import Point
from svgpathtools import Line

import networkx as nx
import os


def test__init(x_floorplan):

    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)

    assert isinstance(nav_builder.floor_navnet, type(nx.Graph()))
    assert nav_builder.current_floorplan == x_floorplan
    assert isinstance(nav_builder.hallways_graph, type(nx.Graph()))


def test_find_valid_boundaries(x_floorplan):
    space = x_floorplan.spaces[0]
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    valid_boundaries = nav_builder._find_valid_boundaries(space)

    assert len(valid_boundaries) == len(space.boundaries)


def test__find_location_of_point_1(rect_floorplan):
    nav_builder = NavigationBuilder(rect_floorplan)
    test_point = Point(125, 40)
    point_space, space_id = nav_builder._find_location_of_point(test_point)

    assert point_space is not None
    assert space_id == 0
    assert point_space.unique_name == "test"


def test__find_location_of_point_2(rect_floorplan):
    nav_builder = NavigationBuilder(rect_floorplan)
    test_point = Point(0, 40)
    point_space, space_id = nav_builder._find_location_of_point(test_point)

    assert point_space is None
    assert space_id is None


def test__find_location_of_point_3(x_floorplan):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    test_point = Point(0, -100)
    point_space, space_id = nav_builder._find_location_of_point(test_point)

    assert point_space is None
    assert space_id is None


def test__aisle_has_nav_segment_1(x_floorplan, aisle_from_x_floorplan):
    space = x_floorplan.spaces[0]
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    has_seg = nav_builder._aisle_has_nav_segment(aisle_from_x_floorplan, space)

    assert has_seg is False


def test__find_location_of_point(x_floorplan):
    space = x_floorplan.spaces[0]
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    test_point = Point(x=0, y=0)
    space, space_id = nav_builder._find_location_of_point(test_point)

    assert space is not None
    assert space.unique_name == "test"
    assert space_id == 0


def test_compute_nav_segments_starting_point_on_wall(rect_floorplan):
    # Allowing this for now until space boundaries and walls are fully treated
    # differently in the Space class.
    nav_builder = NavigationBuilder(rect_floorplan)
    first_point = Point(x=0, y=40)
    direction_vector = complex(1, 0)
    width = 10
    segments, seg_spaces = nav_builder.compute_nav_segments(
        first_point, direction_vector, width
    )

    assert len(seg_spaces) == 1
    assert len(segments) == 1


def test_compute_nav_segments_overlap_with_wall(rect_floorplan):
    # Starting from one wall and going in same direction
    nav_builder = NavigationBuilder(rect_floorplan)
    first_point = Point(x=0, y=40)
    direction_vector = complex(0, 1)
    width = 10
    segments, seg_spaces = nav_builder.compute_nav_segments(
        first_point, direction_vector, width
    )

    assert len(seg_spaces) == 0
    assert len(segments) == 0


def test_compute_nav_segments_starts_from_mid_aisle_no_issue(rect_floorplan):
    # starting from the middle of the aisle and going in same dir as intented
    nav_builder = NavigationBuilder(rect_floorplan)
    first_point = Point(x=125, y=40)
    direction_vector = complex(1, 0)
    width = 10
    segments, seg_spaces = nav_builder.compute_nav_segments(
        first_point, direction_vector, width
    )

    assert len(seg_spaces) == 2
    assert len(segments) == 2
    assert len(segments[0]) == 125
    assert len(segments[1]) == 125


def test_compute_nav_segments_across_spaces(rect_floorplan2):
    nav_builder = NavigationBuilder(rect_floorplan2)
    first_point = Point(x=50, y=40)
    direction_vector = complex(1, 0)
    width = 10
    segments, seg_spaces = nav_builder.compute_nav_segments(
        first_point, direction_vector, width
    )

    assert len(seg_spaces) == 3
    assert len(list(set(seg_spaces))) == 2
    assert len(segments) == 3
    assert len(segments[-1]) == 125


def test_create_nav_segment_for_aisle_1(rect_floorplan):
    space = rect_floorplan.spaces[0]
    nav_builder = NavigationBuilder(rect_floorplan, add_all_nav_points=False)
    wall1 = list(space.boundaries)[0]
    wall2 = list(space.boundaries)[2]
    aisle = (wall1, wall2)
    nav_builder.create_nav_segment_for_aisle(aisle)

    n_nodes = nav_builder.floor_navnet.number_of_nodes()

    n_one_neighbor = 0
    n_three_neighbors = 0
    for node in list(nav_builder.floor_navnet.nodes):
        neighbors = list(nav_builder.floor_navnet.neighbors(node))
        if len(neighbors) == 1:
            n_one_neighbor += 1
        if len(neighbors) == 3:
            n_three_neighbors += 1

    assert n_nodes == 3
    assert n_one_neighbor == 2
    assert n_three_neighbors == 0


def test_create_nav_segment_for_aisle_2(rect_floorplan):
    space = rect_floorplan.spaces[0]
    nav_builder = NavigationBuilder(rect_floorplan, add_all_nav_points=True)
    wall1 = list(space.boundaries)[0]
    wall2 = list(space.boundaries)[2]
    aisle = (wall1, wall2)
    nav_builder.create_nav_segment_for_aisle(aisle)

    n_nodes = nav_builder.floor_navnet.number_of_nodes()

    n_one_neighbor = 0
    n_three_neighbors = 0
    n_zero_neighbor = 0
    for node in list(nav_builder.floor_navnet.nodes):
        neighbors = list(nav_builder.floor_navnet.neighbors(node))
        if len(neighbors) == 1:
            n_one_neighbor += 1
        if len(neighbors) == 3:
            n_three_neighbors += 1
        if len(neighbors) == 0:
            n_zero_neighbor += 1

    assert n_nodes == 249
    assert n_one_neighbor == 2
    assert n_three_neighbors == 0
    assert n_zero_neighbor == 0


def test__aisle_has_nav_segment_2(rect_floorplan):
    space = rect_floorplan.spaces[0]
    nav_builder = NavigationBuilder(rect_floorplan)
    wall1 = list(space.boundaries)[0]
    wall2 = list(space.boundaries)[2]
    aisle = (wall1, wall2)
    nav_builder.create_nav_segment_for_aisle(aisle)
    has_seg = nav_builder._aisle_has_nav_segment(aisle, space)

    assert has_seg is True


def test_simplify_navigation_network_1(x_floorplan, aisle_from_x_floorplan):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.create_nav_segment_for_aisle(aisle_from_x_floorplan)
    nav_builder.simplify_navigation_network()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    assert n_nodes == 2


def test_simplify_navigation_network_2(x_floorplan, aisle_from_x_floorplan2):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.create_nav_segment_for_aisle(aisle_from_x_floorplan2)
    nav_builder.simplify_navigation_network()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    assert n_nodes == 2
    assert n_edges == 1


def test_simplify_navigation_network_3(
    x_floorplan, aisle_from_x_floorplan, aisle_from_x_floorplan2
):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.create_nav_segment_for_aisle(aisle_from_x_floorplan)
    nav_builder.create_nav_segment_for_aisle(aisle_from_x_floorplan2)
    nav_builder.simplify_navigation_network()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    assert n_nodes == 5
    assert n_edges == 4


def test_sanitize_graph(
    x_floorplan, aisle_from_x_floorplan, aisle_from_x_floorplan2
):

    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.create_nav_segment_for_aisle(aisle_from_x_floorplan)
    nav_builder.create_nav_segment_for_aisle(aisle_from_x_floorplan2)
    nav_builder.simplify_navigation_network()
    nav_builder.sanitize_graph()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    assert n_nodes == 5


def test_sanitize_graph_2(rect_floorplan):
    space = rect_floorplan.spaces[0]
    nav_builder = NavigationBuilder(rect_floorplan)
    wall1 = list(space.boundaries)[0]
    wall2 = list(space.boundaries)[2]
    aisle = (wall1, wall2)
    nav_builder.create_nav_segment_for_aisle(aisle)
    rect_floorplan.special_walls = [
        Line(start=complex(125, 0), end=complex(125, 80))
    ]
    nav_builder.simplify_navigation_network()
    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()
    assert n_nodes == 2
    assert n_edges == 1

    nav_builder.sanitize_graph()
    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()
    assert n_nodes == 4
    assert n_edges == 2


def test_build_x(x_floorplan):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.build()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    assert n_nodes == 12
    assert n_edges == 24


def test_build_navnet_for_rect_space(rect_floorplan):
    nav_builder = NavigationBuilder(rect_floorplan)
    nav_builder.build()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    assert (125.0, 0.0) in list(nav_builder.floor_navnet.nodes())
    assert n_edges == 8
    assert n_nodes == 5


def test_build_navnet_for_2_adjacent_rect_spaces(rect_floorplan2):
    nav_builder = NavigationBuilder(rect_floorplan2, add_all_nav_points=False)
    nav_builder.build()

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    n_edges2 = nav_builder.hallways_graph.number_of_edges()

    assert n_nodes == 8
    assert n_edges == 14
    assert n_edges2 == 1


def test_export_navdata_to_pkl(x_floorplan, tmp_path):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)

    d = tmp_path / "sub"
    d.mkdir()
    navnet_file = d / "navnet.pkl"
    hallway_graph_file = d / "hallway_graph.pkl"

    nav_builder.export_navdata_to_pkl(navnet_file, hallway_graph_file)

    assert os.path.isfile(navnet_file)
    assert os.path.isfile(hallway_graph_file)


def test_export_navnet_to_svg(x_floorplan, tmp_path):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.floor_navnet.add_node((0, 40))
    nav_builder.floor_navnet.add_node((250, 40))
    nav_builder.floor_navnet.add_edge((0, 0), (250, 40), half_width="40")

    d = tmp_path / "sub"
    d.mkdir()
    svg_file = d / "navnet.svg"

    nav_builder.export_navnet_to_svg(svg_file)

    assert os.path.isfile(svg_file)


def test_load_navdata_from_pkl_files_1(x_floorplan, tmp_path):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.floor_navnet.add_node((0, 40))
    nav_builder.floor_navnet.add_node((250, 40))
    nav_builder.floor_navnet.add_edge((0, 40), (250, 40), half_width="40")

    d = tmp_path / "sub"
    d.mkdir()
    navnet_file = d / "navnet.pkl"
    hallway_graph_file = d / "hallway_graph.pkl"
    nav_builder.export_navdata_to_pkl(navnet_file, hallway_graph_file)
    nav_builder.floor_navnet.clear()
    load_result = nav_builder.load_navdata_from_pkl_files(
        navnet_file, hallway_graph_file
    )

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    assert load_result is True
    assert n_nodes == 2
    assert n_edges == 1


def test_load_navdata_from_pkl_files_2(x_floorplan, tmp_path):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    d = tmp_path / "sub"
    d.mkdir()
    navnet_file = d / "ntest.pkl"
    hallway_graph_file = d / "htest.pkl"
    load_result = nav_builder.load_navdata_from_pkl_files(
        navnet_file, hallway_graph_file
    )

    assert load_result is False


def test_load_navdata_from_pkl_files_3(x_floorplan, tmp_path):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.build()
    d = tmp_path / "sub"
    d.mkdir()
    navnet_file = d / "navnet.pkl"
    hallway_graph_file = d / "hallway_graph.pkl"
    load_result = nav_builder.load_navdata_from_pkl_files(
        navnet_file, hallway_graph_file
    )

    assert load_result is False


def test_load_nav_segments_from_svg_file(x_floorplan):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    dir_name = os.path.dirname(os.path.realpath(__file__))
    test_svg_file = dir_name + "/sample_results/new_nav_seg.svg"
    segs = nav_builder.load_nav_segments_from_svg_file(test_svg_file)

    assert len(segs) == 2


def test_update_network_from_svg_file(x_floorplan):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.build()
    dir_name = os.path.dirname(os.path.realpath(__file__))
    test_svg_file = dir_name + "/sample_results/new_nav_seg.svg"
    res = nav_builder.update_network_from_svg_file(test_svg_file)

    n_nodes = nav_builder.floor_navnet.number_of_nodes()
    n_edges = nav_builder.floor_navnet.number_of_edges()

    # svg_file = 'test_nav_seg.svg'
    # nav_builder.export_navnet_to_svg(svg_file)

    assert res is True
    assert n_nodes == 12 + 10
    assert n_edges == 60


def test__add_spaces_to_hallway_graph(x_floorplan, x_space, rect_space):
    nav_builder = NavigationBuilder(x_floorplan, add_all_nav_points=False)
    nav_builder.build()
    nav_builder._add_spaces_to_hallway_graph([rect_space, x_space])

    n_nodes = nav_builder.hallways_graph.number_of_nodes()
    n_edges = nav_builder.hallways_graph.number_of_edges()

    assert n_nodes == 3
    assert n_edges == 1
