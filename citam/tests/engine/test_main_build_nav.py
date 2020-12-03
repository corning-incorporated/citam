import os

import citam.engine.main as main


def test_build_navigation_network_no_issues(datadir, monkeypatch):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    main.build_navigation_network(facility="TEST", floor="0")
    floor_dir = os.path.join(datadir, "floorplans_and_nav_data")
    floor_dir = os.path.join(floor_dir, "TEST")
    floor_dir = os.path.join(floor_dir, "floor_0")
    nav_file = os.path.join(floor_dir, "routes.json")

    assert os.path.isfile(nav_file)
