import pytest
import citam.engine.main as main

import os


def test_update_floorplan_from_svg_file_file_not_found(tmpdir, monkeypatch):
    svg_file = os.path.join(tmpdir, 'inexistent.svg')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(tmpdir))

    with pytest.raises(FileNotFoundError):
        main.update_floorplan_from_svg_file(facility="TEST",
                                              floor="0",
                                              map=svg_file
                                              )


def test_update_floorplan_from_svg_file_floorplan_not_found(tmpdir,
                                                            monkeypatch
                                                            ):
    svg_file = os.path.join(tmpdir, 'test.svg')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(tmpdir))

    with pytest.raises(FileNotFoundError):
        main.update_floorplan_from_svg_file(facility="TEST",
                                            floor="0",
                                            map=svg_file
                                            )


def test_update_floorplan_from_svg_file_no_issues(datadir,
                                                  tmpdir,
                                                  monkeypatch
                                                  ):
    svg_file = os.path.join(datadir, 'TF1_edited.svg')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    main.update_floorplan_from_svg_file(facility="TEST",
                                        floor="0",
                                        map=svg_file
                                        )
    floor_dir = os.path.join(datadir, 'floorplans_and_nav_data')
    floor_dir = os.path.join(floor_dir, 'TEST')
    floor_dir = os.path.join(floor_dir, 'floor_0')
    outputfile = os.path.join(floor_dir, 'updated_floorplan.pkl')

    assert os.path.isfile(outputfile)


def test_export_floorplan_to_svg_invalid_output_location(datadir, monkeypatch):
    outputfile = os.path.join('H:/Invalid Location/test.svg')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    with pytest.raises(FileNotFoundError):
        main.export_floorplan_to_svg(facility="TEST",
                                     floor="0",
                                     outputfile=outputfile
                                     )


def test_export_floorplan_to_svg_no_issues(datadir, tmpdir, monkeypatch):
    outputfile = os.path.join(tmpdir, 'test.svg')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))
    res = main.export_floorplan_to_svg(facility="TEST",
                                       floor="0",
                                       outputfile=outputfile
                                       )

    assert os.path.isfile(outputfile)