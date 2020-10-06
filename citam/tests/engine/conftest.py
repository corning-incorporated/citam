from __future__ import unicode_literals

from svgpathtools import Path, Line, parse_path

from citam.engine.space import Space
from citam.engine.floorplan import Floorplan
from citam.engine.door import Door
from citam.engine.floorplan_ingester import FloorplanIngester

from distutils import dir_util
import pytest
import os
import copy
from copy import deepcopy

import pickle


@pytest.fixture
def x_floorplan():
    x_top_str = "M -10,0 L -46,36 L -36,36 L 0,10 L 36,36 L 46,36 L 10,0"
    x_top_path = parse_path(x_top_str)
    x_bottom = x_top_path.rotated(180)
    x_bottom = x_bottom.translated(complex(0, -20))
    x_str = x_top_str + x_bottom.d()
    x_boundaries = parse_path(x_str)
    x_space = Space(
        boundaries=x_boundaries,
        path=x_boundaries,
        unique_name="test",
        space_function="circulation",
        building="TEST",
    )
    walls = list(x_boundaries)
    doors = []
    aisles = []
    fp = Floorplan(1.0, [x_space], doors, walls, aisles, 200, 200)

    return fp


@pytest.fixture
def rect_floorplan():

    path_str = "M 0,0 L 250,0 L 250,80 L 0,80 z"
    rect_boundaries = parse_path(path_str)
    walls = Path(
        *[
            Line(start=complex(0, 0), end=complex(120, 0)),
            Line(start=complex(130, 0), end=complex(250, 0)),
            Line(start=complex(250, 0), end=complex(250, 80)),
            Line(start=complex(250, 80), end=complex(0, 80)),
            Line(start=complex(0, 80), end=complex(0, 0)),
        ]
    )
    rect_space = Space(
        boundaries=rect_boundaries,
        path=walls,
        unique_name="test",
        space_function="circulation",
        building="TEST",
    )

    door_path = Line(start=complex(120, 0), end=complex(130, 0))
    doors = [Door(path=door_path, space1=rect_space)]
    aisles = []
    fp = Floorplan(1.0, [rect_space], doors, walls, aisles, 200, 200)

    return fp


@pytest.fixture
def rect_floorplan2():
    path_str = "M 0,0 L 125,0 L 125,80 L 0,80 z"
    rect1_boundaries = parse_path(path_str)
    rect1_space = Space(
        boundaries=rect1_boundaries,
        path=rect1_boundaries,
        unique_name="rect1",
        space_function="circulation",
        building="TEST",
    )

    path_str = "M 125,0 L 250,0 L 250,80 L 125,80 z"
    rect2_boundaries = parse_path(path_str)
    rect2_space = Space(
        boundaries=rect2_boundaries,
        path=rect2_boundaries,
        unique_name="rect2",
        space_function="circulation",
        building="TEST",
    )

    walls = list(rect1_boundaries)
    del walls[1]
    walls2 = list(rect2_boundaries)
    del walls2[-1]
    walls += walls2
    doors = []
    aisles = []
    spaces = [rect1_space, rect2_space]
    fp = Floorplan(1.0, spaces, doors, walls, aisles, 200, 200)

    return fp


@pytest.fixture
def x_space():
    x_top_str = "M -10,0 L -46,36 L -36,36 L 0,10 L 36,36 L 46,36 L 10,0"
    x_top_path = parse_path(x_top_str)
    x_bottom = x_top_path.rotated(180)
    x_bottom = x_bottom.translated(complex(0, -20))
    x_str = x_top_str + x_bottom.d()
    x_boundaries = parse_path(x_str)
    x_space = Space(
        boundaries=x_boundaries,
        path=x_boundaries,
        unique_name="x_space",
        space_function="circulation",
        building="TEST",
    )

    return x_space


@pytest.fixture
def rect_space():
    path_str = "M 0,0 L 250,0 L 250,80 L 0,80 z"
    rect_boundaries = parse_path(path_str)
    rect_space = Space(
        boundaries=rect_boundaries,
        path=rect_boundaries,
        unique_name="rect_space",
        space_function="circulation",
        building="TEST",
    )

    return rect_space


@pytest.fixture
def datadir(tmpdir, request):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir


@pytest.fixture
def aisle_from_x_floorplan(x_floorplan):
    wall1 = list(x_floorplan.spaces[0].boundaries)[0]
    wall2 = list(x_floorplan.spaces[0].boundaries)[2]
    return (wall1, wall2)


@pytest.fixture
def aisle_from_x_floorplan2(x_floorplan):
    wall1 = list(x_floorplan.spaces[0].boundaries)[3]
    wall2 = list(x_floorplan.spaces[0].boundaries)[5]
    return (wall1, wall2)


@pytest.fixture
def simple_facility_floorplan(request, monkeypatch):
    filename = request.module.__file__
    test_dir = os.path.dirname(filename)

    datadir = os.path.join(
        test_dir, "test_navigation", "floorplans_and_nav_data"
    )
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    floorplan_pickle_file = os.path.join(
        datadir, "test_simple_facility/", "floor_0", "updated_floorplan.pkl"
    )
    with open(floorplan_pickle_file, "rb") as f:
        (
            spaces,
            doors,
            walls,
            special_walls,
            aisles,
            width,
            height,
            scale,
        ) = pickle.load(f)
    fp = Floorplan(scale, spaces, doors, walls, aisles, width, height)
    return fp


@pytest.fixture
def simple_facility_floorplan_2_floors(simple_facility_floorplan):

    fp2 = deepcopy(simple_facility_floorplan)
    for space in fp2.spaces:
        space.unique_name = space.unique_name + "_2"
    fp2.floor_name = "1"

    return [simple_facility_floorplan, fp2]
