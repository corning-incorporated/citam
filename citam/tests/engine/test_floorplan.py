import os
import json

import pytest

from citam.engine.serializer import serializer
from citam.engine.floorplan import floorplan_from_directory


# @pytest.fixture
# def floorplan_pickle(simple_facility_floorplan, tmp_path):
#     pkl_path = os.path.join(tmp_path, "floorplan.pkl")
#     simple_facility_floorplan.export_data_to_pickle_file(pkl_path)
#     return pkl_path


# def test_floorplan_from_directory(floorplan_pickle):
#     (
#         spaces,
#         doors,
#         walls,
#         special_walls,
#         aisles,
#         width,
#         height,
#         scale,
#     ) = pickle.load(open(floorplan_pickle, "rb"))

#     pickle_dir = os.path.dirname(floorplan_pickle)
#     fp = floorplan_from_directory(pickle_dir, "floor_0")
#     assert fp.spaces == spaces
#     assert fp.doors == doors
#     assert fp.walls == walls
#     assert fp.special_walls == special_walls
#     assert fp.aisles == aisles
#     assert fp.width == width
#     assert fp.height == height
#     assert fp.scale == scale


# def test_floorplan_from_directory_custom_floor_name(floorplan_pickle):
#     (
#         spaces,
#         doors,
#         walls,
#         special_walls,
#         aisles,
#         width,
#         height,
#         scale,
#     ) = pickle.load(open(floorplan_pickle, "rb"))

#     fn = "foo_floor_19862"
#     pickle_dir = os.path.dirname(floorplan_pickle)
#     fp = floorplan_from_directory(pickle_dir, fn)
#     assert fp.spaces == spaces
#     assert fp.doors == doors
#     assert fp.walls == walls
#     assert fp.special_walls == special_walls
#     assert fp.aisles == aisles
#     assert fp.width == width
#     assert fp.height == height
#     assert fp.scale == scale
#     assert fp.floor_name == fn


# def test_floorplan_from_directory_with_kwargs(floorplan_pickle):
#     (
#         spaces,
#         doors,
#         walls,
#         special_walls,
#         aisles,
#         width,
#         height,
#         scale,
#     ) = pickle.load(open(floorplan_pickle, "rb"))

#     custom_scale = 24

#     pickle_dir = os.path.dirname(floorplan_pickle)
#     fp = floorplan_from_directory(pickle_dir, "floor_0", scale=custom_scale)
#     assert fp.spaces == spaces
#     assert fp.doors == doors
#     assert fp.walls == walls
#     assert fp.special_walls == special_walls
#     assert fp.aisles == aisles
#     assert fp.width == width
#     assert fp.height == height
#     assert fp.scale == custom_scale


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
            assert enc_door == dec_door
            # assert enc_door.path == dec_door.path
            # assert enc_door.space1.id == dec_door.space1.id
            # assert enc_door.space2 == dec_door.space2


def test_to_json_file(x_floorplan, tmpdir):
    json_file = os.path.join(tmpdir, 'test.json')
    x_floorplan.to_json_file(json_file)
    assert os.path.isfile(json_file)


def test_export_to_svg(x_floorplan, tmpdir):
    svg_file = os.path.join(tmpdir, 'test.svg')
    x_floorplan.export_to_svg(svg_file)
    assert os.path.isfile(svg_file)