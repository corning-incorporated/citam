from citam.engine.floorplan_ingester import FloorplanIngester


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


# def test_read_input_files(datadir):

#     svg_file = datadir + '/good_floorplan.svg'
#     csv_file = datadir + '/TF1.csv'
#     scale = 0.8
#     fi = FloorplanIngester(svg_file,
#                            csv_file,
#                            scale,
#                            extract_doors_from_file=True
#                            )

#     fi.read_input_files()
#     assert len(fi.space_paths) == 214
#     assert len(fi.door_paths) == 0
#     assert len(fi.space_attributes) == 214
#     assert len(fi.space_data) == 214


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
