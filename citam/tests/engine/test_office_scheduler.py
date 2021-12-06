import os
from citam.engine.constants import DEFAULT_MEETINGS_POLICY
from citam.engine.schedulers.office_scheduler import OfficeScheduler


def test_no_meetings(simple_facility_model, request, tmpdir):

    office_scheduler = OfficeScheduler(
        simple_facility_model.facility,
        simple_facility_model.total_timesteps,
        shifts=[{"name": "test", "percent_agents": 1, "start_time": 0}],
    )
    office_scheduler.run(3)

    assert len(office_scheduler.meeting_schedule.meetings) == 0
    assert not os.path.isfile(os.path.join(tmpdir, "agents.csv"))
    assert not os.path.isfile(os.path.join(tmpdir, "meetings.txt"))


def test_save_to_files(simple_facility_model, request, tmpdir):

    office_scheduler = OfficeScheduler(
        simple_facility_model.facility,
        simple_facility_model.total_timesteps,
        shifts=[{"name": "test", "percent_agents": 1, "start_time": 0}],
    )
    office_scheduler.run(3)
    office_scheduler.save_to_files(tmpdir)

    assert os.path.isfile(os.path.join(tmpdir, "agents.csv"))
    assert os.path.isfile(os.path.join(tmpdir, "meetings.txt"))


def test_assign_office_preassigned(simple_facility_model):
    model = simple_facility_model
    office_scheduler = OfficeScheduler(
        model.facility,
        model.total_timesteps,
        preassigned_offices=[(1, 0), (5, 0), (4, 0)],
    )
    res = office_scheduler.assign_office()
    assert res == (1, 0)
    res = office_scheduler.assign_office()
    assert res == (5, 0)


# TODO Test that meeting schedule exists when required
# assert model.meeting_policy is not None
