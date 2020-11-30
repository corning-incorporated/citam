from citam.engine.map.updater import FloorplanUpdater
from svgpathtools import Line
from copy import deepcopy


def test_read_updated_SVG_file(datadir):
    # svg_file = datadir.join('rect_floorplan_edited.svg')
    return


def test_update_from_SVG_data(rect_floorplan, datadir):

    door_paths = [
        Line(start=complex(0, 20), end=complex(0, 60)),
        Line(start=complex(125, 20), end=complex(125, 60)),
    ]
    wall_paths = [
        Line(start=complex(125, 0), end=complex(125, 80)),
        Line(start=complex(0, 0), end=complex(250, 0)),
        Line(start=complex(250, 0), end=complex(250, 80)),
        Line(start=complex(250, 80), end=complex(0, 80)),
        Line(start=complex(0, 80), end=complex(0, 0)),
    ]
    orginal_fp = deepcopy(rect_floorplan)
    svg_file = datadir.join("rect_floorplan_edited.svg")
    fp_updater = FloorplanUpdater(rect_floorplan, svg_file=svg_file)
    fp_updater.update_from_SVG_data(wall_paths, door_paths)

    walls_removed = [
        w for w in orginal_fp.walls if w not in fp_updater.floorplan.walls
    ]

    assert len(walls_removed) == 3  # 2 walls removed
    assert len(fp_updater.floorplan.walls) == 7  # 4 walls added leading to 7
    assert len(fp_updater.floorplan.doors) == 2  # Existing door is removed
    assert len(fp_updater.floorplan.special_walls) == 3  # 2 new walls found


def test_update_from_CSV_data(datadir):

    return
