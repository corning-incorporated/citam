import citam.engine.main as main

import os


def test_build_navigation_network_no_issues(datadir, monkeypatch):
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    res = main.build_navigation_network(facility="TEST",
                                        floor="0",
                                        )
    floor_dir = os.path.join(datadir, 'floorplans_and_nav_data')
    floor_dir = os.path.join(floor_dir, 'TEST')
    floor_dir = os.path.join(floor_dir, 'floor_0')
    nav_file = os.path.join(floor_dir, 'routes.pkl')
    if not os.path.isfile(nav_file):
        print('File not found: ', nav_file)
    assert os.path.isfile(nav_file)
    assert res
