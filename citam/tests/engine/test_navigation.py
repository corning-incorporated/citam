from citam.engine.navigation import (
    Navigation,
    unroll_route,
    remove_unnecessary_coords,
)
import pytest
import os


def test_get_corresponding_vertical_space_bad_method_naming(
    simple_facility_floorplan_2_floors, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="naming",
    )
    my_space = None
    for space in nav.floorplans[0].spaces:
        if space.unique_name == "5":
            my_space = space
            break

    if my_space is not None:
        dest_space_id, dest_space = nav.get_corresponding_vertical_space(
            my_space, 1
        )
    assert dest_space_id is None
    assert dest_space is None


def test_get_corresponding_vertical_space(
    simple_facility_floorplan_2_floors, monkeypatch, datadir
):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="xy",
    )
    my_space = None
    for i, space in enumerate(nav.floorplans[0].spaces):
        if space.unique_name == "5":
            my_space = space
            my_space_id = i
            break

    expected_space = nav.floorplans[1].spaces[my_space_id]
    dest_space_id, dest_space = nav.get_corresponding_vertical_space(
        my_space, 1
    )
    assert dest_space == expected_space


def test_add_vertical_edges_no_edges(
    simple_facility_floorplan_2_floors, datadir, monkeypatch
):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="xy",
    )
    n_vert_edges = nav.add_vertical_edges(0, 1)

    assert n_vert_edges == 0


def test_add_vertical_edges_no_matching_stairs(
    simple_facility_floorplan_2_floors, datadir, monkeypatch
):
    # This is expected lead to a vertical edge as only the space in the
    # starting floor is checked for the correct function.
    simple_facility_floorplan_2_floors[0].spaces[1].space_function = "stairs"
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="xy",
    )
    n_vert_edges = nav.add_vertical_edges(0, 1)

    assert n_vert_edges == 0


def test_add_vertical_edges_2_edges(
    simple_facility_floorplan_2_floors, datadir, monkeypatch
):

    simple_facility_floorplan_2_floors[0].spaces[1].space_function = "stairs"
    simple_facility_floorplan_2_floors[1].spaces[1].space_function = "stairs"

    simple_facility_floorplan_2_floors[0].spaces[5].space_function = "stairs"
    simple_facility_floorplan_2_floors[1].spaces[5].space_function = "stairs"

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="xy",
    )
    n_vert_edges = nav.add_vertical_edges(0, 1)

    assert n_vert_edges == 2


def test_load_floor_oneway_net_file_not_found(
    simple_facility_floorplan, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation([simple_facility_floorplan], "test_simple_facility", None)

    with pytest.raises(FileNotFoundError):
        nav.load_floor_oneway_net(datadir)


def test_init_hallway_graph_not_found(
    simple_facility_floorplan, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    floor_dir = os.path.join(
        datadir, "floorplans_and_nav_data/test_simple_facility/floor_0/"
    )
    os.remove(os.path.join(floor_dir, "hallways_graph.json"))

    with pytest.raises(FileNotFoundError):

        Navigation([simple_facility_floorplan], "test_simple_facility", None)


def test_init_navnet_not_found(
    simple_facility_floorplan, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    os.remove(
        os.path.join(
            datadir,
            "floorplans_and_nav_data/test_simple_facility/floor_0/routes.json",
        )
    )
    with pytest.raises(FileNotFoundError):

        Navigation([simple_facility_floorplan], "test_simple_facility", None)


def test_init(simple_facility_floorplan, monkeypatch, datadir):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation([simple_facility_floorplan], "test_simple_facility", None)
    assert len(nav.navnet_per_floor) == 1
    assert len(nav.hallways_graph_per_floor) == 1
    assert nav.traffic_policy is None


def test_init_2_floors(
    simple_facility_floorplan_2_floors, monkeypatch, datadir
):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors, "test_simple_facility", None
    )
    assert nav.multifloor_navnet is not None
    assert len(nav.navnet_per_floor) == 2
    assert nav.traffic_policy is None
    assert len(nav.hallways_graph_per_floor) == 2


def test_set_policy_for_aisle(simple_facility_floorplan, monkeypatch, datadir):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    policy = [{"floor": "0", "segment_id": "0", "direction": -1}]

    nav = Navigation(
        [simple_facility_floorplan], "test_simple_facility", policy
    )

    n_edges2 = nav.navnet_per_floor[0].number_of_edges()

    assert len(nav.oneway_network_per_floor) == 1
    assert n_edges2 == 56 - 5
    # TODO: Verify that the right edges have been removed
    # TODO: Create a similar test for a diagonal nav segment


def test_oneway_policy_missing_network(
    simple_facility_floorplan_2_floors, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    policy = [{"floor": "1", "segment_id": "0", "direction": -1}]

    with pytest.raises(FileNotFoundError):
        Navigation(
            simple_facility_floorplan_2_floors, "test_simple_facility", policy
        )


def test_get_best_possible_routes_same_floor(
    simple_facility_floorplan, monkeypatch, datadir
):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation([simple_facility_floorplan], "test_simple_facility", None)
    floor_number = 0
    current_location = 1
    destination = 8
    routes = nav.get_best_possible_routes_same_floor(
        floor_number, current_location, destination
    )
    assert len(routes) == 1
    assert len(routes[0]) == 8


def test_get_best_possible_routes_multifloor_no_stairs(
    simple_facility_floorplan_2_floors, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="xy",
    )

    starting_floor_number = 0
    starting_location = 1
    destination = 8
    destination_floor_number = 1

    routes = nav.get_best_possible_routes_multifloor(
        starting_location,
        starting_floor_number,
        destination,
        destination_floor_number,
    )
    assert routes == []


def test_get_best_possible_routes_multifloor(
    simple_facility_floorplan_2_floors, monkeypatch, datadir
):

    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    simple_facility_floorplan_2_floors[0].spaces[4].space_function = "stairs"
    simple_facility_floorplan_2_floors[1].spaces[4].space_function = "stairs"
    nav = Navigation(
        simple_facility_floorplan_2_floors,
        "test_simple_facility",
        None,
        multifloor_type="xy",
    )

    starting_floor_number = 0
    starting_location = 1
    destination = 8
    destination_floor_number = 1

    routes = nav.get_best_possible_routes_multifloor(
        starting_location,
        starting_floor_number,
        destination,
        destination_floor_number,
    )
    assert len(routes) == 1
    assert len(routes[0]) == 11


def test_remove_unnecessary_coords_same_floor():
    route = [(0, 0), (10, 0), (15, 0), (15, 20)]
    route = remove_unnecessary_coords(route)
    assert len(route) == 3


def test_remove_unnecessary_coords_same_floor2():
    route = [(0, 0), (10, 0), (10, 20), (15, 20), (25, 20)]
    route = remove_unnecessary_coords(route)
    assert len(route) == 4


def test_remove_unnecessary_coords_2_floors():
    route = [(0, 0, 0), (10, 0, 0), (10, 0, 1), (15, 0, 1), (15, 20, 1)]
    route = remove_unnecessary_coords(route)
    assert len(route) == 5


def test_remove_unnecessary_coords_2_floors2():
    route = [
        (0, 0, 0),
        (5, 0, 0),
        (10, 0, 0),
        (10, 0, 1),
        (15, 0, 1),
        (15, 20, 1),
    ]
    route = remove_unnecessary_coords(route)
    assert len(route) == 5


def test_unroll_route():
    route = [(0, 0), (0, 50), (25, 50), (26, 51)]
    new_route = unroll_route(route, 2.0)
    assert len(new_route) == 25 + 12 + 2


def test_unroll_route_2_floors():
    route = [(0, 0, 0), (0, 50, 0), (0, 50, 1), (25, 50, 1), (26, 51, 1)]
    new_route = unroll_route(route, 2.0)
    assert len(new_route) == 25 + 12 + 3
