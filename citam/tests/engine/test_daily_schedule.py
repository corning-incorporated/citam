from citam.engine.daily_schedule import Schedule, ScheduleItem
from citam.engine.navigation import Navigation
from citam.engine.constants import (
    DEFAULT_SCHEDULING_RULES,
    OFFICE_WORK,
)
import os
import pytest


@pytest.fixture
def sample_empty_schedule_object(
    simple_facility_floorplan,
    request, monkeypatch
):

    filename = request.module.__file__
    test_dir = os.path.dirname(filename)
    datadir = os.path.join(test_dir, "data_navigation")
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    navigation = Navigation(
        floorplans=[simple_facility_floorplan],
        facility_name="test_simple_facility",
        traffic_policy=None
    )

    sched = Schedule(
        timestep=1.0,
        start_time=0,
        exit_time=3600,
        entrance_door=0,  # door object
        entrance_floor=0,  # int
        exit_door=0,  # door object
        exit_floor=0,
        office_location=15,
        office_floor=0,
        navigation=navigation,
        scheduling_rules=DEFAULT_SCHEDULING_RULES,
        meetings=None,
    )

    return sched


def test_build_schedule_item(sample_empty_schedule_object):
    sched = sample_empty_schedule_object
    item = sched.build_schedule_item(
        purpose=OFFICE_WORK,
        next_meeting_start_time=100,
    )

    assert isinstance(item, ScheduleItem)
