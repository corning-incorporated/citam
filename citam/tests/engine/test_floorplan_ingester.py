from citam.engine.floorplan_ingester import FloorplanIngester
from svgpathtools import parse_path
from citam.engine.space import Space

import pytest
import copy


@pytest.fixture
def rect_floorplan_ingester_data():
    """Basic rect floorplan with one main aisle, 4 office spaces on each side
    and a big room at the end of the hallway
    """
    rect_fi = FloorplanIngester(None, 1.0, csv_file="")
    rect_fi.space_data = []
    rect_fi.space_paths = []
    rect_fi.space_attributes = []

    # Main aisle
    space_id = 1
    rect_fi.space_attributes.append({"id": space_id})
    aisle = parse_path("M 0,0 L 250,0 L 250,80 L 0,80 Z")
    rect_fi.space_paths.append(aisle)
    rect_fi.space_data.append(
        {
            "id": space_id,
            "facility": "TF",
            "building": "TF1",
            "unique_name": str(space_id),
            "space_function": "aisle",
        }
    )

    # Rooms
    for i in range(5):
        if i == 2:
            continue
        x = i * 50
        space_id += 1
        path_str = (
            "M "
            + str(x)
            + ",0"
            + " L "
            + str(x)
            + ",-120 "
            + "L "
            + str(x + 50)
            + ",-120"
            + " L "
            + str(x + 50)
            + ",0 Z"
        )
        rect_fi.space_paths.append(parse_path(path_str))
        rect_fi.space_attributes.append({"id": space_id})
        rect_fi.space_data.append(
            {
                "id": space_id,
                "facility": "TF",
                "building": "TF1",
                "unique_name": str(space_id),
                "space_function": "office",
            }
        )

        space_id += 1
        path_str = (
            "M "
            + str(x)
            + ",80"
            + " L "
            + str(x)
            + ",200 "
            + "L "
            + str(x + 50)
            + ",200"
            + " L "
            + str(x + 50)
            + ",80 Z"
        )
        rect_fi.space_paths.append(parse_path(path_str))
        rect_fi.space_attributes.append({"id": space_id})
        rect_fi.space_data.append(
            {
                "id": space_id,
                "facility": "TF",
                "building": "TF1",
                "unique_name": str(space_id),
                "space_function": "office",
            }
        )

    # Main door
    door_path_str = "M 0,20 L 0,60"
    rect_fi.door_paths = [parse_path(door_path_str)]

    # big room door
    door_path_str = "M 250,20 L 250,60"
    rect_fi.door_paths.append(parse_path(door_path_str))

    # Office door
    door_path_str = "M 60,80 L 80,80"
    rect_fi.door_paths.append(parse_path(door_path_str))

    # Big room
    space_id += 1
    path_str = "M 250,-120 L 350,-120 L 350,200 L 250,200 Z"
    rect_fi.space_paths.append(parse_path(path_str))
    rect_fi.space_data.append(
        {
            "id": space_id,
            "facility": "TF",
            "building": "TF1",
            "unique_name": str(space_id),
            "space_function": "cafeteria",
        }
    )
    rect_fi.space_attributes.append({"id": space_id})

    return rect_fi


@pytest.fixture
def rect_floorplan_ingester_data_no_csv():
    """Basic rect floorplan with one main aisle, 4 office spaces on each side
    and a big room at the end of the hallway.
    """
    rect_fi = FloorplanIngester(None, 1.0)
    rect_fi.space_data = []
    rect_fi.space_paths = []
    rect_fi.space_attributes = []

    # Main aisle
    space_id = 1
    aisle = parse_path("M 0,0 L 250,0 L 250,80 L 0,80 Z")
    rect_fi.space_paths.append(aisle)
    rect_fi.space_attributes.append(
        {
            "id": space_id,
            "facility": "TF",
            "building": "TF1",
            "unique_name": str(space_id),
            "space_function": "aisle",
        }
    )

    # Rooms
    for i in range(5):
        if i == 2:
            continue
        x = i * 50
        space_id += 1
        path_str = (
            "M "
            + str(x)
            + ",0"
            + " L "
            + str(x)
            + ",-120 "
            + "L "
            + str(x + 50)
            + ",-120"
            + " L "
            + str(x + 50)
            + ",0 Z"
        )
        rect_fi.space_paths.append(parse_path(path_str))
        rect_fi.space_attributes.append(
            {
                "id": space_id,
                "facility": "TF",
                "building": "TF1",
                "unique_name": str(space_id),
                "space_function": "office",
            }
        )

        space_id += 1
        path_str = (
            "M "
            + str(x)
            + ",80"
            + " L "
            + str(x)
            + ",200 "
            + "L "
            + str(x + 50)
            + ",200"
            + " L "
            + str(x + 50)
            + ",80 Z"
        )
        rect_fi.space_paths.append(parse_path(path_str))
        rect_fi.space_attributes.append(
            {
                "id": space_id,
                "facility": "TF",
                "building": "TF1",
                "unique_name": str(space_id),
                "space_function": "office",
            }
        )

    # Main door
    door_path_str = "M 0,20 L 0,60"
    rect_fi.door_paths = [parse_path(door_path_str)]

    # big room door
    door_path_str = "M 250,20 L 250,60"
    rect_fi.door_paths.append(parse_path(door_path_str))

    # Office door
    door_path_str = "M 60,80 L 80,80"
    rect_fi.door_paths.append(parse_path(door_path_str))

    # Big room
    space_id += 1
    path_str = "M 250,-120 L 350,-120 L 350,200 L 250,200 Z"
    rect_fi.space_paths.append(parse_path(path_str))
    rect_fi.space_attributes.append(
        {
            "id": space_id,
            "facility": "TF",
            "building": "TF1",
            "unique_name": str(space_id),
            "space_function": "cafeteria",
        }
    )

    return rect_fi


@pytest.fixture
def rect_floorplan_ingester(rect_floorplan_ingester_data):
    rfid = rect_floorplan_ingester_data
    for path, data in zip(rfid.space_paths, rfid.space_data):
        space = Space(boundaries=path, path=copy.deepcopy(path), **data)
        rfid.spaces.append(space)

    return rfid


def test_init_correct_number_of_objects(datadir):

    svg_file = None  # datadir + '/TF1.svg'
    csv_file = None  # datadir + '/TF1.csv'
    scale = 0.8
    fi = FloorplanIngester(
        svg_file, csv_file, scale, extract_doors_from_file=True
    )

    assert fi.spaces == []
    assert fi.doors == []
    assert fi.walls == []


def test_create_spaces_correct_number_of_spaces(rect_floorplan_ingester_data):
    rect_floorplan_ingester_data.create_spaces_from_csv_and_svg_data()
    assert len(rect_floorplan_ingester_data.spaces) == 10
    assert len(rect_floorplan_ingester_data.doors) == 0
    assert len(rect_floorplan_ingester_data.walls) == 0
    assert (len(rect_floorplan_ingester_data.buildings)) == 1


def test_create_spaces_correct_number_of_spaces_no_csv(
    rect_floorplan_ingester_data_no_csv,
):
    rect_floorplan_ingester_data_no_csv.create_spaces_from_svg_data()
    assert len(rect_floorplan_ingester_data_no_csv.spaces) == 10
    assert len(rect_floorplan_ingester_data_no_csv.doors) == 0
    assert len(rect_floorplan_ingester_data_no_csv.walls) == 0
    assert (len(rect_floorplan_ingester_data_no_csv.buildings)) == 1


def test_run_correct_number_of_objects(rect_floorplan_ingester_data):
    rect_floorplan_ingester_data.run()

    assert len(rect_floorplan_ingester_data.doors) == 10
    assert len(rect_floorplan_ingester_data.spaces) == 10
    assert len(rect_floorplan_ingester_data.walls) == 42


def test_run_correct_number_of_objects_no_csv(
    rect_floorplan_ingester_data_no_csv,
):
    rect_floorplan_ingester_data_no_csv.run()

    assert len(rect_floorplan_ingester_data_no_csv.doors) == 10
    assert len(rect_floorplan_ingester_data_no_csv.spaces) == 10
    assert len(rect_floorplan_ingester_data_no_csv.walls) == 42


def test_find_walls_and_create_doors(rect_floorplan_ingester):
    (
        room_walls,
        valid_hw_walls,
    ) = rect_floorplan_ingester.find_valid_walls_and_create_doors("TF1")

    assert len(room_walls) == 36
    assert len(valid_hw_walls) == 3
