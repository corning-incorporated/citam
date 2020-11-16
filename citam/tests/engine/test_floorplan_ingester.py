from citam.engine.floorplan_ingester import FloorplanIngester
from svgpathtools import parse_path

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
    rect_floorplan_ingester_data.create_spaces()
    assert len(rect_floorplan_ingester_data.spaces) == 10
    assert len(rect_floorplan_ingester_data.doors) == 0
    assert len(rect_floorplan_ingester_data.walls) == 0
    assert (len(rect_floorplan_ingester_data.buildings)) == 1


def test_run_correct_number_of_objects(rect_floorplan_ingester_data):
    rect_floorplan_ingester_data.run()

    assert len(rect_floorplan_ingester_data.doors) == 10
    assert len(rect_floorplan_ingester_data.spaces) == 10
    assert len(rect_floorplan_ingester_data.walls) == 42


def test_find_walls_and_create_doors(rect_floorplan_ingester):
    (
        room_walls,
        valid_hw_walls,
    ) = rect_floorplan_ingester.find_valid_walls_and_create_doors("TF1")

    assert len(room_walls) == 36
    assert len(valid_hw_walls) == 3


def test_find_min_and_max_coordinates(rect_floorplan_ingester):

    rect_floorplan_ingester.run()
    rect_floorplan_ingester.find_min_and_max_coordinates()

    assert rect_floorplan_ingester.minx == 0
    assert rect_floorplan_ingester.maxx == 350
    assert rect_floorplan_ingester.miny == -120
    assert rect_floorplan_ingester.maxy == 200


def test__find_all_overlapping_walls(rect_floorplan_ingester):
    door_path_str = "M 0,20 L 0,60"
    door_line = parse_path(door_path_str)
    results = rect_floorplan_ingester._find_all_overlapping_walls(door_line)

    assert len(results) == 1

def test__find_all_overlapping_walls2(rect_floorplan_ingester):
    door_path_str = "M 60,80 L 80,80"
    door_line = parse_path(door_path_str)
    results = rect_floorplan_ingester._find_all_overlapping_walls(door_line)

    assert len(results) == 2
