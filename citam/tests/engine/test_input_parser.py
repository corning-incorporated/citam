import pytest
from citam.engine.io.input_parser import (
    parse_csv_metadata_file,
    parse_svg_floorplan_file,
    parse_input_file,
    parse_standalone_svg_floorplan_file,
)

import os


def test_parse_csv_metadata_file_file_not_found():
    csv_file = "test_inputs/non_existent.csv"
    with pytest.raises(FileNotFoundError):
        parse_csv_metadata_file(csv_file)


def test_parse_csv_metadata_file_missing_column(datadir):
    # Test if missing column is handled
    csv_file = datadir.join("missing_column.csv")
    with pytest.raises(ValueError):
        parse_csv_metadata_file(csv_file)


def test_parse_csv_metadata_file_missing_value(datadir):
    # Test if missing value is handled
    csv_file = datadir.join("missing_value.csv")
    with pytest.raises(ValueError):
        parse_csv_metadata_file(csv_file)


def test_parse_csv_metadata_file_invalid_value(datadir):
    # Test if invalid value for space function is handled well
    csv_file = datadir.join("invalid_value.csv")
    with pytest.raises(ValueError):
        parse_csv_metadata_file(csv_file)


def test_parse_csv_metadata_file_correct_number_of_rows(datadir):
    # Test if correct number of rows is returned
    csv_file = datadir.join("good_data.csv")
    data = parse_csv_metadata_file(csv_file)
    assert len(data) == 2
    assert len(data[0]) == 5


def test_parse_csv_metadata_file_optional_columns_support(datadir):
    # Test if optional column values are returned
    csv_file = datadir.join("with_optional_columns.csv")
    data = parse_csv_metadata_file(csv_file)
    assert len(data) == 1
    assert len(data[0]) == 9


def parse_svg_floorplan_file_not_found():
    svg_file = "non_existent.svg"
    with pytest.raises(FileNotFoundError):
        parse_svg_floorplan_file(svg_file)


def parse_svg_floorplan_good_file(datadir):
    svg_file = "good_floorplan.svg"
    data = parse_svg_floorplan_file(svg_file)
    assert len(data) == 3
    assert len(data[0]) == 214
    assert len(data[1]) == 214


def parse_svg_floorplan_bad_file_no_path_id(datadir):
    svg_file = "bad_floorplan.svg"
    data = parse_svg_floorplan_file(svg_file)
    assert len(data[0]) == 0


def test_parse_input_file_no_issues(datadir):
    inputfile = os.path.join(datadir, "example_sim_inputs.json")
    res = parse_input_file(inputfile)
    assert res is not None
    assert len(res) == 18


def test_parse_input_file_missing_values(datadir):
    inputfile = os.path.join(datadir, "missing_value.json")
    with pytest.raises(TypeError):
        parse_input_file(inputfile)


def test_parse_input_file_file_not_found(datadir):
    inputfile = os.path.join(datadir, "test_json_inexistent.json")
    with pytest.raises(FileNotFoundError):
        parse_input_file(inputfile)


def test_parse_input_file_invalid_daylength(datadir):
    inputfile = os.path.join(datadir, "bad_daylength.json")
    with pytest.raises(TypeError):
        parse_input_file(inputfile)


def test_parse_svg_map_file_no_issues(datadir):
    inputfile = os.path.join(datadir, "svg_with_space_metadata.svg")
    (
        space_paths,
        space_attr,
        door_paths,
    ) = parse_standalone_svg_floorplan_file(inputfile)

    assert len(space_paths) == len(space_attr)
    assert len(space_attr) == 525
    assert len(door_paths) == 200

    for sattr in space_attr:
        assert "unique_name" in sattr
        assert "id" in sattr
        assert "space_function" in sattr
        assert "building" in sattr


def test_parse_svg_map_file_no_building(datadir):
    inputfile = os.path.join(
        datadir, "svg_with_space_metadata_no_building.svg"
    )

    with pytest.raises(ValueError):
        parse_standalone_svg_floorplan_file(inputfile)


def test_parse_svg_map_file_no_space(datadir):
    inputfile = os.path.join(datadir, "svg_with_space_metadata_no_space.svg")

    with pytest.raises(ValueError):
        parse_standalone_svg_floorplan_file(inputfile)


def test_parse_svg_map_file_no_space_function(datadir):
    inputfile = os.path.join(
        datadir, "svg_with_space_metadata_no_space_function.svg"
    )

    with pytest.raises(ValueError):
        parse_standalone_svg_floorplan_file(inputfile)


def test_parse_svg_map_file_invalid_building(datadir):
    inputfile = os.path.join(
        datadir, "svg_with_space_metadata_invalid_building.svg"
    )

    with pytest.raises(ValueError):
        parse_standalone_svg_floorplan_file(inputfile)
