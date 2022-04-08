import pytest
from copy import deepcopy

from citam.engine.schedulers.meetings import MeetingSchedule, Meeting
from citam.engine.map.space import Space


@pytest.fixture
def sample_policy_params():

    return {
        # Meetings duration
        "min_meeting_duration": 15 * 60,  # 15 min
        "max_meeting_length": 7200,  # 2 hours
        "meeting_duration_increment": 15 * 60,  # 15 min
        # Meetings frequency
        "avg_meetings_per_room": 3,
        "percent_meeting_rooms_used": 0.5,  # Less than 1.0
        # Meetings participants
        "avg_meetings_per_person": 3,
        "min_attendees_per_meeting": 3,
        # Meeting timing
        "min_buffer_between_meetings": 0,
        "max_buffer_between_meetings": 3600,
    }


@pytest.fixture
def sample_meeting_schedule(sample_policy_params, simple_facility_floorplan):

    meeting_rooms = [
        space
        for space in simple_facility_floorplan.spaces
        if not space.is_space_a_hallway()
    ]

    for space in meeting_rooms:
        space.capacity = 25

    meeting_schedule = MeetingSchedule(
        meeting_rooms=[meeting_rooms],
        agent_ids=[0, 1, 2],
        daylength=3600 * 8,
        policy_params=sample_policy_params,
    )

    return meeting_schedule


def test__init(sample_policy_params, simple_facility_floorplan):

    meeting_rooms = [
        space
        for space in simple_facility_floorplan.spaces
        if not space.is_space_a_hallway()
    ]
    for space in meeting_rooms:
        space.capacity = 25

    agent_ids = [0, 1, 2]
    meeting_schedule = MeetingSchedule(
        meeting_rooms=[meeting_rooms],
        agent_ids=agent_ids,
        daylength=8 * 3600,
        policy_params=sample_policy_params,
    )
    assert len(meeting_schedule.attendee_pool) == len(agent_ids)
    assert len(meeting_schedule.meeting_rooms[0]) == len(meeting_rooms)
    assert meeting_schedule.daylength == 8 * 3600
    assert (
        meeting_schedule.min_meeting_duration
        == sample_policy_params["min_meeting_duration"]
    )
    assert (
        meeting_schedule.max_meeting_length
        == sample_policy_params["max_meeting_length"]
    )
    assert (
        meeting_schedule.meeting_duration_increment
        == sample_policy_params["meeting_duration_increment"]
    )
    assert (
        meeting_schedule.avg_meetings_per_person
        == sample_policy_params["avg_meetings_per_room"]
    )
    assert (
        meeting_schedule.percent_meeting_rooms_used
        == sample_policy_params["percent_meeting_rooms_used"]
    )
    assert (
        meeting_schedule.avg_meetings_per_person
        == sample_policy_params["avg_meetings_per_person"]
    )
    assert (
        meeting_schedule.min_attendees_per_meeting
        == sample_policy_params["min_attendees_per_meeting"]
    )
    assert (
        meeting_schedule.min_buffer_between_meetings
        == sample_policy_params["min_buffer_between_meetings"]
    )
    assert (
        meeting_schedule.max_buffer_between_meetings
        == sample_policy_params["max_buffer_between_meetings"]
    )


def test_create_all_meetings(sample_meeting_schedule, sample_policy_params):

    # Verify that no attendee is overbooked
    # Verify that the meeting rooms are from the right list
    # Verify that the number of meetings per room is acceptable
    # Verify that the number of meetings per person is acceptable

    for _ in range(5):
        policy = deepcopy(sample_meeting_schedule)
        policy.build()

        attendees = set()
        meetings_per_person = {}
        for meeting in policy.meetings:
            assert len(set(meeting.attendees)) == len(meeting.attendees)
            for a in meeting.attendees:
                attendees.add(a)
                if a in meetings_per_person:
                    meetings_per_person[a] += 1
                else:
                    meetings_per_person[a] = 1
        avg_meetings_per_person = sum(meetings_per_person.values()) / len(
            meetings_per_person
        )
        rooms_with_meeting = len(
            set([meeting.location for meeting in policy.meetings])
        )
        assert (
            rooms_with_meeting / 3.0
            <= sample_policy_params["percent_meeting_rooms_used"] + 1
        )
        assert (
            abs(avg_meetings_per_person - policy.avg_meetings_per_person) <= 3
        )


def test__update_attendee_pool(sample_meeting_schedule):

    sample_meeting_schedule.attendee_pool[0] = 25
    sample_meeting_schedule._update_attendee_pool()

    assert len(sample_meeting_schedule.attendee_pool) == 2


def test__update_attendee_pool_2(sample_meeting_schedule):

    sample_meeting_schedule.attendee_pool[0] = 9
    sample_meeting_schedule._update_attendee_pool()

    assert len(sample_meeting_schedule.attendee_pool) == 3


def test_get_daily_meetings(sample_meeting_schedule):

    meetings = sample_meeting_schedule.get_daily_meetings(0)
    assert not meetings

    meetings = sample_meeting_schedule.get_daily_meetings(1)
    assert not meetings

    meetings = sample_meeting_schedule.get_daily_meetings(2)
    assert not meetings


def test_get_daily_meetings_2(sample_meeting_schedule):

    sample_meeting_schedule.meetings.append(
        Meeting(
            location=0,
            floor_number=0,
            start_time=0,
            end_time=2500,
            attendees=[0, 1],
        )
    )

    meetings = sample_meeting_schedule.get_daily_meetings(0)
    assert len(meetings) == 1

    meetings = sample_meeting_schedule.get_daily_meetings(1)
    assert len(meetings) == 1

    meetings = sample_meeting_schedule.get_daily_meetings(2)
    assert not meetings


def test__find_potential_attendees(sample_meeting_schedule):

    assert len(sample_meeting_schedule._find_potential_attendees(0, 3600)) == 3


def test__find_potential_attendees_2(sample_meeting_schedule):

    sample_meeting_schedule.meetings.append(
        Meeting(
            location=0,
            floor_number=0,
            start_time=0,
            end_time=2500,
            attendees=[0, 1],
        )
    )

    assert len(sample_meeting_schedule._find_potential_attendees(0, 3600)) == 1


def test__generate_meeting_attendee_list(sample_meeting_schedule):

    meeting_room = Space("", "", "", "", "", "", capacity=25)

    attendees = sample_meeting_schedule._generate_meeting_attendee_list(
        meeting_room, 0, 3600
    )
    assert len(attendees) == 3


def test__generate_meeting_attendee_list2(sample_meeting_schedule):

    meeting_room = Space("", "", "", "", "", "", capacity=5)
    sample_meeting_schedule.attendee_pool.update(
        {4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    )

    attendees = sample_meeting_schedule._generate_meeting_attendee_list(
        meeting_room, 0, 3600
    )
    assert len(attendees) <= 5


def test__create_meetings_for_room(sample_meeting_schedule):
    n_meetings = 0
    for _ in range(5):
        meeting_room = Space("", "", "", "", "", "", capacity=5)
        sample_meeting_schedule._create_meetings_for_room(meeting_room, 0)
        n_meetings += len(sample_meeting_schedule.meetings)

    assert n_meetings / 5.0 > 0