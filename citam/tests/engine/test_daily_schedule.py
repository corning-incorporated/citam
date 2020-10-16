from citam.engine.daily_schedule import Schedule, ScheduleItem
from citam.engine.navigation import Navigation
from citam.engine.meeting_policy import Meeting
from citam.engine.constants import (
    DEFAULT_SCHEDULING_RULES,
    OFFICE_WORK,
    MEETING
)
import os
import pytest


@pytest.fixture
def sample_empty_schedule_object(
    simple_facility_floorplan, request, monkeypatch
):

    filename = request.module.__file__
    test_dir = os.path.dirname(filename)
    datadir = os.path.join(test_dir, "data_navigation")
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    navigation = Navigation(
        floorplans=[simple_facility_floorplan],
        facility_name="test_simple_facility",
        traffic_policy=None,
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


def test_build_schedule_item_not_enough_time(sample_empty_schedule_object):
    """Not enough time before next meeting, raise error"""
    sched = sample_empty_schedule_object
    with pytest.raises(ValueError):
        sched.build_schedule_item(
            purpose=OFFICE_WORK,
            next_meeting_start_time=100,
        )


def test_build_schedule_item(sample_empty_schedule_object):
    sched = sample_empty_schedule_object
    item = sched.build_schedule_item(
        purpose=OFFICE_WORK,
        next_meeting_start_time=None,
    )

    assert isinstance(item, ScheduleItem)
    assert item.purpose == OFFICE_WORK
    assert item.duration >= sched.scheduling_rules[OFFICE_WORK]["min_duration"]
    assert item.duration <= sched.scheduling_rules[OFFICE_WORK]["max_duration"]


# Test build schedule item, office work happens in assigned office space


def test_find_next_schedule_item_first_item(sample_empty_schedule_object):
    """If no upcoming meeting, start schedule with office work"""
    sched = sample_empty_schedule_object
    item = sched.find_next_schedule_item()

    assert isinstance(item, ScheduleItem)
    assert item.purpose == OFFICE_WORK


def test_find_next_schedule_item_upcoming_meeting(
    sample_empty_schedule_object
):
    """upcoming meeting found, just return it"""
    sched = sample_empty_schedule_object
    upcoming_meeting = Meeting(
        location=10,
        floor_number=0,
        attendees=[0],
        start_time=10,
        end_time=90
    )
    sched.meetings.append(upcoming_meeting)
    item = sched.find_next_schedule_item()

    assert isinstance(item, ScheduleItem)
    assert item.floor_number == 0
    assert item.location == 10
    assert item.purpose == MEETING
    assert item.duration == 80


def test_find_next_schedule_item_existing_item(
    sample_empty_schedule_object
):
    sched = sample_empty_schedule_object
    sched.schedule_items.append([])
    item = sched.find_next_schedule_item()

    assert isinstance(item, ScheduleItem)


# test_choose_valid_scheduling_purpose

# test_get_pace

# test_update_itinerary

# test_build