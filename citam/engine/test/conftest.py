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


@pytest.fixture
def x_floorplan():
    x_top_str = 'M -10,0 L -46,36 L -36,36 L 0,10 L 36,36 L 46,36 L 10,0'
    x_top_path = parse_path(x_top_str)
    x_bottom = x_top_path.rotated(180)
    x_bottom = x_bottom.translated(complex(0, -20))
    x_str = x_top_str + x_bottom.d()
    x_boundaries = parse_path(x_str)
    x_space = Space(boundaries=x_boundaries,
                    path=x_boundaries,
                    unique_name='test',
                    space_function='circulation',
                    building='TEST'
                    )
    walls = list(x_boundaries)
    doors = []
    aisles = []
    fp = Floorplan(1.0, [x_space], doors, walls, aisles, 200, 200)

    return fp


@pytest.fixture
def rect_floorplan():

    path_str = 'M 0,0 L 250,0 L 250,80 L 0,80 z'
    rect_boundaries = parse_path(path_str)
    walls = Path(*[Line(start=complex(0, 0), end=complex(120, 0)),
                   Line(start=complex(130, 0), end=complex(250, 0)),
                   Line(start=complex(250, 0), end=complex(250, 80)),
                   Line(start=complex(250, 80), end=complex(0, 80)),
                   Line(start=complex(0, 80), end=complex(0, 0))
                   ]
                 )
    rect_space = Space(boundaries=rect_boundaries,
                       path=walls,
                       unique_name='test',
                       space_function='circulation',
                       building='TEST'
                       )

    door_path = Line(start=complex(120, 0), end=complex(130, 0))
    doors = [Door(path=door_path, space1=rect_space)]
    aisles = []
    fp = Floorplan(1.0, [rect_space], doors, walls, aisles, 200, 200)

    return fp


@pytest.fixture
def rect_floorplan2():
    path_str = 'M 0,0 L 125,0 L 125,80 L 0,80 z'
    rect1_boundaries = parse_path(path_str)
    rect1_space = Space(boundaries=rect1_boundaries,
                        path=rect1_boundaries,
                        unique_name='rect1',
                        space_function='circulation',
                        building='TEST'
                        )

    path_str = 'M 125,0 L 250,0 L 250,80 L 125,80 z'
    rect2_boundaries = parse_path(path_str)
    rect2_space = Space(boundaries=rect2_boundaries,
                        path=rect2_boundaries,
                        unique_name='rect2',
                        space_function='circulation',
                        building='TEST'
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
    x_top_str = 'M -10,0 L -46,36 L -36,36 L 0,10 L 36,36 L 46,36 L 10,0'
    x_top_path = parse_path(x_top_str)
    x_bottom = x_top_path.rotated(180)
    x_bottom = x_bottom.translated(complex(0, -20))
    x_str = x_top_str + x_bottom.d()
    x_boundaries = parse_path(x_str)
    x_space = Space(boundaries=x_boundaries,
                    path=x_boundaries,
                    unique_name='x_space',
                    space_function='circulation',
                    building='TEST'
                    )

    return x_space


@pytest.fixture
def rect_space():
    path_str = 'M 0,0 L 250,0 L 250,80 L 0,80 z'
    rect_boundaries = parse_path(path_str)
    rect_space = Space(boundaries=rect_boundaries,
                       path=rect_boundaries,
                       unique_name='rect_space',
                       space_function='circulation',
                       building='TEST'
                       )

    return rect_space


@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
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
def rect_floorplan_ingester_data():
    '''Basic rect floorplan with one main aisle, 4 office spaces on each side
    and a big room at the end of the hallway
    '''
    rect_fi = FloorplanIngester(None, None, 1.0)
    rect_fi.space_data = []
    rect_fi.space_paths = []
    rect_fi.space_attributes = []

    # Main aisle
    space_id = 1
    rect_fi.space_attributes.append({'id': space_id})
    aisle = parse_path("M 0,0 L 250,0 L 250,80 L 0,80 Z")
    rect_fi.space_paths.append(aisle)
    rect_fi.space_data.append({
        'id': space_id,
        'facility': 'TF',
        'building': 'TF1',
        'unique_name': space_id,
        'space_function': 'aisle'
    })

    # Rooms
    for i in range(5):
        if i == 2:
            continue
        x = i*50
        space_id += 1
        path_str = "M " + str(x) + ",0" + " L " + str(x) + ",-120 " +\
                   "L " + str(x+50) + ",-120" + " L " + str(x+50) + ",0 Z"
        rect_fi.space_paths.append(parse_path(path_str))
        rect_fi.space_attributes.append({'id': space_id})
        rect_fi.space_data.append({
            'id': space_id,
            'facility': 'TF',
            'building': 'TF1',
            'unique_name': space_id,
            'space_function': 'office'
        })

        space_id += 1
        path_str = "M " + str(x) + ",80" + " L " + str(x) + ",200 " +\
                   "L " + str(x+50) + ",200" + " L " + str(x+50) + ",80 Z"
        rect_fi.space_paths.append(parse_path(path_str))
        rect_fi.space_attributes.append({'id': space_id})
        rect_fi.space_data.append({
            'id': space_id,
            'facility': 'TF',
            'building': 'TF1',
            'unique_name': space_id,
            'space_function': 'office'
        })

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
    rect_fi.space_data.append({
            'id': space_id,
            'facility': 'TF',
            'building': 'TF1',
            'unique_name': space_id,
            'space_function': 'cafeteria'
        })
    rect_fi.space_attributes.append({'id': space_id})

    return rect_fi


@pytest.fixture
def rect_floorplan_ingester(rect_floorplan_ingester_data):
    rfid = rect_floorplan_ingester_data
    for path, data in zip(rfid.space_paths, rfid.space_data):
        space = Space(boundaries=path,
                      path=copy.deepcopy(path),
                      **data
                      )
        rfid.spaces.append(space)

    return rfid
