import pytest
import citam.engine.main as main

import os


def test_export_navigation_graph_to_svg_no_issue(datadir, tmpdir, monkeypatch):
    svg_file = os.path.join(tmpdir, 'routes.svg')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    main.export_navigation_graph_to_svg(facility="TEST",
                                        floor="0",
                                        outputfile=svg_file
                                        )
    assert os.path.isfile(svg_file) is True


def test_run_simulation_no_issues(datadir, tmpdir, monkeypatch):
    inputs_dict = {'upload_results': False,
                   'upload_location': None,
                   'facility_name': 'TEST',
                   'floors': ["0"],
                   'n_agents': 5,
                   'occupancy_rate': None,
                   'daylength': 3600,
                   'buffer': 100,
                   'timestep': 1.0,
                   'entrances': [{"floor": "0", "name": "aisle213"}],
                   'contact_distance': 6.0,
                   'shifts': [{"name": "1",
                               "start_time": 100,
                               "percent_workforce": 1.0
                               }],
                   'meetings_policy_params': None,
                   'scheduling_policy': None,
                   'output_directory': tmpdir
                   }
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    main.run_simulation(inputs_dict)

    traj_file = os.path.join(tmpdir, 'trajectory.txt')
    pair_contact_file = os.path.join(tmpdir, 'pair_contact.csv')
    statistics_file = os.path.join(tmpdir, 'statistics.json')
    manifest_file = os.path.join(tmpdir, 'manifest.json')
    floor_subdir = os.path.join(tmpdir, 'floor_0')
    map_file = os.path.join(floor_subdir, 'map.svg')
    heatmap_file = os.path.join(floor_subdir, 'heatmap.svg')
    contact_file = os.path.join(floor_subdir, 'contacts.txt')
    contact_dist_file = os.path.join(floor_subdir,
                                     'contact_dist_per_coord.csv'
                                     )

    assert os.path.isdir(floor_subdir)
    assert os.path.isfile(traj_file)
    assert os.path.isfile(pair_contact_file)
    assert os.path.isfile(statistics_file)
    assert os.path.isfile(manifest_file)
    assert os.path.isfile(map_file)
    assert os.path.isfile(heatmap_file)
    assert os.path.isfile(contact_file)
    assert os.path.isfile(contact_dist_file)
