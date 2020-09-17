import pytest
import citam.engine.main as main

import os


def test_ingest_floorplan_file_not_found():
    # Check if functions raises correct error when file not found.
    csv_file = 'test.csv'
    svg_file = 'test2.svg'
    facility_name = 'test'

    with pytest.raises(FileNotFoundError):
        main.ingest_floorplan(csv=csv_file,
                              svg=svg_file,
                              facility=facility_name
                              )


def test_ingest_floorplan_no_issues(datadir, tmpdir):
    csv_file = os.path.join(datadir, 'TF1.csv')
    svg_file = os.path.join(datadir, 'TF1.svg')
    facility_name = 'mytest'
    main.ingest_floorplan(csv=csv_file,
                          svg=svg_file,
                          facility=facility_name,
                          output_directory=tmpdir)
    output_filename = os.path.join(tmpdir, 'floorplan.pkl')
    assert os.path.isfile(output_filename)
