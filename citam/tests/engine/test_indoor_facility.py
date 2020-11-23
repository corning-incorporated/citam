import os
import pytest

from citam.engine.facility.indoor_facility import Facility


@pytest.fixture
def simple_facility(simple_facility_floorplan, monkeypatch, request):
    filename = request.module.__file__
    test_dir = os.path.dirname(filename)
    datadir = os.path.join(test_dir, "data_navigation")
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    facility = Facility(
        [simple_facility_floorplan],
        facility_name="test_simple_facility",
        entrances=[{"name": "1", "floor": "0"}],
        traffic_policy=None,
    )

    return facility


def test_init(simple_facility):

    assert simple_facility.total_offices == 8
    assert len(simple_facility.entrances) == 1

    assert len(simple_facility.cafes) == 1
    assert len(simple_facility.cafes[0]) == 1

    assert len(simple_facility.meeting_rooms) == 1
    assert len(simple_facility.meeting_rooms[0]) == 0