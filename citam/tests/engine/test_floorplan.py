import os
import json

import pytest

from citam.engine.io.serializer import serializer
from citam.engine.map.floorplan import floorplan_from_directory


@pytest.fixture
def floorplan_json(simple_facility_floorplan, tmp_path):
    pkl_path = os.path.join(tmp_path, "floorplan.json")
    simple_facility_floorplan.to_json_file(pkl_path)
    return pkl_path


def test_floorplan_from_directory(floorplan_json, simple_facility_floorplan):
    json_dir = os.path.dirname(floorplan_json)
    fp = floorplan_from_directory(json_dir, "floor_0")
    assert fp.spaces == simple_facility_floorplan.spaces
    assert fp.doors == simple_facility_floorplan.doors
    assert fp.walls == simple_facility_floorplan.walls
    assert fp.special_walls == simple_facility_floorplan.special_walls
    assert fp.aisles == simple_facility_floorplan.aisles
    assert fp.minx == simple_facility_floorplan.minx
    assert fp.maxx == simple_facility_floorplan.maxx
    assert fp.miny == simple_facility_floorplan.miny
    assert fp.maxy == simple_facility_floorplan.maxy
    assert fp.scale == simple_facility_floorplan.scale


def test_floorplan_from_directory_custom_floor_name(
    floorplan_json, simple_facility_floorplan
):

    fn = "foo_floor_19862"
    json_dir = os.path.dirname(floorplan_json)
    fp = floorplan_from_directory(json_dir, fn)
    assert fp.spaces == simple_facility_floorplan.spaces
    assert fp.doors == simple_facility_floorplan.doors
    assert fp.walls == simple_facility_floorplan.walls
    assert fp.special_walls == simple_facility_floorplan.special_walls
    assert fp.aisles == simple_facility_floorplan.aisles
    assert fp.minx == simple_facility_floorplan.minx
    assert fp.maxx == simple_facility_floorplan.maxx
    assert fp.miny == simple_facility_floorplan.miny
    assert fp.maxy == simple_facility_floorplan.maxy
    assert fp.scale == simple_facility_floorplan.scale
    assert fp.floor_name == fn


def test_floorplan_from_directory_with_kwargs(
    floorplan_json, simple_facility_floorplan
):
    custom_scale = 24
    json_dir = os.path.dirname(floorplan_json)
    fp = floorplan_from_directory(json_dir, "floor_0", scale=custom_scale)
    assert fp.spaces == simple_facility_floorplan.spaces
    assert fp.doors == simple_facility_floorplan.doors
    assert fp.walls == simple_facility_floorplan.walls
    assert fp.special_walls == simple_facility_floorplan.special_walls
    assert fp.aisles == simple_facility_floorplan.aisles
    assert fp.minx == simple_facility_floorplan.minx
    assert fp.maxx == simple_facility_floorplan.maxx
    assert fp.miny == simple_facility_floorplan.miny
    assert fp.maxy == simple_facility_floorplan.maxy
    assert fp.scale == custom_scale


def test_serialize(x_floorplan):

    obj = json.dumps(x_floorplan, default=serializer.encoder_default)
    fp_decoded = json.loads(obj, object_hook=serializer.decoder_hook)

    assert x_floorplan.spaces == fp_decoded.spaces
    assert x_floorplan.doors == fp_decoded.doors
    assert x_floorplan.walls == fp_decoded.walls
    assert x_floorplan.aisles == fp_decoded.aisles
    assert x_floorplan.special_walls == fp_decoded.special_walls
    assert x_floorplan.minx == fp_decoded.minx
    assert x_floorplan.maxx == fp_decoded.maxx
    assert x_floorplan.miny == fp_decoded.miny
    assert x_floorplan.maxy == fp_decoded.maxy
    assert x_floorplan.scale == fp_decoded.scale


def test_serialize2(rect_floorplan):

    obj = json.dumps(rect_floorplan, default=serializer.encoder_default)

    print("Done encoding: ", obj)

    fp_decoded = json.loads(obj, object_hook=serializer.decoder_hook)

    assert len(rect_floorplan.spaces) == len(fp_decoded.spaces)
    assert len(rect_floorplan.doors) == len(fp_decoded.doors)

    for enc_space, dec_space in zip(rect_floorplan.spaces, fp_decoded.spaces):
        assert enc_space.id == dec_space.id
        assert len(enc_space.doors) == len(dec_space.doors)
        for enc_door, dec_door in zip(enc_space.doors, dec_space.doors):
            print(enc_door, dec_door)
            assert enc_door.path == dec_door.path
            assert enc_door.space1.id == dec_door.space1.id
            assert enc_door.space2 == dec_door.space2
            # assert enc_door.path == dec_door.path
            # assert enc_door.space1.id == dec_door.space1.id
            # assert enc_door.space2 == dec_door.space2


def test_to_json_file(x_floorplan, tmpdir):
    json_file = os.path.join(tmpdir, "test.json")
    x_floorplan.to_json_file(json_file)
    assert os.path.isfile(json_file)


def test_export_to_svg(x_floorplan, tmpdir):
    svg_file = os.path.join(tmpdir, "test.svg")
    x_floorplan.export_to_svg(svg_file)
    assert os.path.isfile(svg_file)
