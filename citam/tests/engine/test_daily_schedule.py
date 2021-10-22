from citam.engine.schedulers.schedule import Schedule, ScheduleItem
from citam.engine.facility.navigation import Navigation
from citam.engine.schedulers.meetings import Meeting
from citam.engine.constants import (
    DEFAULT_SCHEDULING_RULES,
    OFFICE_WORK,
    MEETING,
    CAFETERIA_VISIT,
    RESTROOM_VISIT,
)
import os
import pytest


@pytest.fixture
def sample_empty_schedule_object(
    simple_facility_floorplan,
    request,
    monkeypatch,
    rect_floorplan_ingester_data,
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
        entrance_door=simple_facility_floorplan.doors[0],  # door object
        entrance_floor=0,  # int
        exit_door=simple_facility_floorplan.doors[0],  # door object
        exit_floor=0,
        office_location=2,
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


# Add build_schedule_item test to make sure office work happens
# in assigned office space


def test_find_next_schedule_item_first_item(sample_empty_schedule_object):
    """If no upcoming meeting, start schedule with office work"""
    sched = sample_empty_schedule_object
    item = sched.find_next_schedule_item()

    assert isinstance(item, ScheduleItem)
    assert item.purpose == OFFICE_WORK


def test_find_next_schedule_item_upcoming_meeting(
    sample_empty_schedule_object,
):
    """upcoming meeting found, just return it"""
    sched = sample_empty_schedule_object
    upcoming_meeting = Meeting(
        location=10, floor_number=0, attendees=[0], start_time=10, end_time=90
    )
    sched.meetings.append(upcoming_meeting)
    item = sched.find_next_schedule_item()

    assert isinstance(item, ScheduleItem)
    assert item.floor_number == 0
    assert item.location == 10
    assert item.purpose == MEETING
    assert item.duration == 80


def test_find_next_schedule_item_existing_item(sample_empty_schedule_object):
    sched = sample_empty_schedule_object
    item = ScheduleItem(
        purpose=OFFICE_WORK, location=10, floor_number=0, duration=60
    )
    sched.schedule_items.append(item)
    item = sched.find_next_schedule_item()

    assert isinstance(item, ScheduleItem)


def test_choose_valid_scheduling_purpose(sample_empty_schedule_object):

    shed = sample_empty_schedule_object
    purpose = shed.choose_valid_scheduling_purpose(None)

    assert purpose == OFFICE_WORK


def test_find_possible_purposes(sample_empty_schedule_object):

    sched = sample_empty_schedule_object
    purposes = sched.find_possible_purposes()

    assert isinstance(purposes, list)
    assert len(purposes) == 2
    for purp in purposes:
        assert purp in [OFFICE_WORK, CAFETERIA_VISIT]


def test_get_valid_purposes_from_possible_purposes(
    sample_empty_schedule_object,
):

    sched = sample_empty_schedule_object
    valid_purposes = sched.get_valid_purposes_from_possible_purposes(None)

    assert isinstance(valid_purposes, list)
    assert len(valid_purposes) == 1
    assert valid_purposes == [OFFICE_WORK]


def test_get_valid_purposes_no_consecutive_restroom_visits(
    sample_empty_schedule_object,
):
    sched = sample_empty_schedule_object
    item = ScheduleItem(
        purpose=RESTROOM_VISIT, location=10, floor_number=0, duration=60
    )
    # Arbitrarily add RESTROOM VISIT to list of possible purposes
    sched.possible_purposes.append(RESTROOM_VISIT)
    sched.schedule_items.append(item)
    valid_purposes = sched.get_valid_purposes_from_possible_purposes(None)

    assert isinstance(valid_purposes, list)
    assert len(valid_purposes) == 1
    assert valid_purposes == [OFFICE_WORK]


def test_get_pace(sample_empty_schedule_object):

    sched = sample_empty_schedule_object
    pace = sched.get_pace(1.0)
    assert pace < 6.0 and pace > 2.0


def test_update_itinerary(sample_empty_schedule_object):

    route = [(0, 0, 0), (5, 0, 0), (10, 0, 0)]
    schedule_item = ScheduleItem(
        purpose=OFFICE_WORK, location=2, floor_number=0, duration=60
    )
    sched = sample_empty_schedule_object
    sched.update_itinerary(route, schedule_item)

    assert len(sched.itinerary) == 64
    assert sched.itinerary[:3] == route
    assert sched.itinerary[-60:] == [sched.itinerary[-1]] * 60
    assert len(sched.schedule_items) == 1


def test_update_itinerary_route_is_none(sample_empty_schedule_object):

    route = None
    schedule_item = ScheduleItem(
        purpose=OFFICE_WORK, location=2, floor_number=0, duration=60
    )
    sched = sample_empty_schedule_object
    with pytest.raises(ValueError):
        sched.update_itinerary(route, schedule_item)


def test_update_schedule_continue_last_item(sample_empty_schedule_object):

    sched = sample_empty_schedule_object
    schedule_item = ScheduleItem(
        purpose=OFFICE_WORK, location=2, floor_number=0, duration=60
    )
    sched.schedule_items.append(schedule_item)
    sched.update_schedule_items(schedule_item)

    assert len(sched.schedule_items) == 1
    assert sched.schedule_items[0].duration == 120


def test_update_schedule_items_add(sample_empty_schedule_object):

    sched = sample_empty_schedule_object
    schedule_item = ScheduleItem(
        purpose=OFFICE_WORK, location=2, floor_number=0, duration=60
    )
    sched.schedule_items.append(schedule_item)
    schedule_item2 = ScheduleItem(
        purpose=OFFICE_WORK, location=3, floor_number=0, duration=60
    )
    sched.update_schedule_items(schedule_item2)

    assert len(sched.schedule_items) == 2


def test_build(sample_empty_schedule_object):

    sched = sample_empty_schedule_object

    sched.build()

    assert (
        len(sched.itinerary) + sched.shortest_purpose_duration
        >= sched.exit_time
    )
    assert len(sched.schedule_items) > 0
