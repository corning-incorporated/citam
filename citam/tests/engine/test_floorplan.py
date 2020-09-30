import os
import pickle

import pytest

from citam.engine.floorplan import floorplan_from_directory


@pytest.fixture
def floorplan_pickle(simple_facility_floorplan, tmp_path):
    pkl_path = os.path.join(tmp_path, 'floorplan.pkl')
    simple_facility_floorplan.export_data_to_pickle_file(pkl_path)
    return pkl_path


def test_floorplan_from_directory(floorplan_pickle):
    (spaces, doors, walls, special_walls, aisles,
     width, height, scale) = pickle.load(open(floorplan_pickle, 'rb'))

    pickle_dir = os.path.dirname(floorplan_pickle)
    fp = floorplan_from_directory(pickle_dir, 'floor_0')
    assert fp.spaces == spaces
    assert fp.doors == doors
    assert fp.walls == walls
    assert fp.special_walls == special_walls
    assert fp.aisles == aisles
    assert fp.width == width
    assert fp.height == height
    assert fp.scale == scale


def test_floorplan_from_directory_custom_floor_name(floorplan_pickle):
    (spaces, doors, walls, special_walls, aisles,
     width, height, scale) = pickle.load(open(floorplan_pickle, 'rb'))

    fn = 'foo_floor_19862'
    pickle_dir = os.path.dirname(floorplan_pickle)
    fp = floorplan_from_directory(pickle_dir, fn)
    assert fp.spaces == spaces
    assert fp.doors == doors
    assert fp.walls == walls
    assert fp.special_walls == special_walls
    assert fp.aisles == aisles
    assert fp.width == width
    assert fp.height == height
    assert fp.scale == scale
    assert fp.floor_name == fn


def test_floorplan_from_directory_with_kwargs(floorplan_pickle):
    (spaces, doors, walls, special_walls, aisles,
     width, height, scale) = pickle.load(open(floorplan_pickle, 'rb'))

    custom_scale = 24

    pickle_dir = os.path.dirname(floorplan_pickle)
    fp = floorplan_from_directory(pickle_dir, 'floor_0', scale=custom_scale)
    assert fp.spaces == spaces
    assert fp.doors == doors
    assert fp.walls == walls
    assert fp.special_walls == special_walls
    assert fp.aisles == aisles
    assert fp.width == width
    assert fp.height == height
    assert fp.scale == custom_scale
