import pytest

from citam.engine.meeting_policy import MeetingPolicy


@pytest.fixture
def sample_policy_params():

    return {
        # Meetings duration
        "min_meeting_duration": 15 * 60,  # 15 min
        "max_meeting_length": 7200,  # 2 hours
        "meeting_duration_increment": 15 * 60,  # 15 min
        # Meetings frequency
        "avg_meetings_per_room": 3,
        "avg_percent_meeting_rooms_used": 0.6,  # Less than 1.0
        # Meetings participants
        "avg_meetings_per_person": 3,
        "min_attendees_per_meeting": 3,
        # Meeting timing
        "min_buffer_between_meetings": 0,
        "max_buffer_between_meetings": 3600
    }


@pytest.fixture
def sample_meeting_policy(sample_policy_params):

    meeting_policy = MeetingPolicy(
                        meeting_rooms=[[1,2, 3]],
                        agent_ids=[0, 1, 2],
                        policy_params=sample_policy_params
                    )

    return meeting_policy


def test__init(sample_policy_params):

    meeting_rooms = [[1,2, 3]]
    agent_ids = [0, 1, 2]
    meeting_policy = MeetingPolicy(
                        meeting_rooms=meeting_rooms,
                        agent_ids=agent_ids,
                        policy_params=sample_policy_params
                    )

    assert len(meeting_policy.attendee_pool) == len(agent_ids)


def test_create_meetings(sample_meeting_policy):

    sample_meeting_policy.create_meetings()

    for meeting in sample_meeting_policy.meetings:
        print("One more meeting: ", meeting)

    assert len(sample_meeting_policy.meetings) == 0


def test__update_attendee_pool(sample_meeting_policy):

    sample_meeting_policy.attendee_pool[0] = 25
    sample_meeting_policy._update_attendee_pool()

    assert len(sample_meeting_policy.attendee_pool) == 2


def test__update_attendee_pool_2(sample_meeting_policy):

    sample_meeting_policy.attendee_pool[0] = 9
    sample_meeting_policy._update_attendee_pool()

    assert len(sample_meeting_policy.attendee_pool) == 3


def test_get_daily_meetings(sample_meeting_policy):

    meetings = sample_meeting_policy.get_daily_meetings(0)

    assert not meetings