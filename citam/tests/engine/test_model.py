from citam.engine.model import FacilityTransmissionModel
from citam.engine.agent import Agent

import os
import pytest
import numpy as np


@pytest.fixture
def simple_facility_model(simple_facility_floorplan, monkeypatch, request):
    filename = request.module.__file__
    test_dir = os.path.dirname(filename)
    datadir = os.path.join(test_dir,
                           'test_navigation')
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    model = FacilityTransmissionModel([simple_facility_floorplan],
                                      daylength=3600,
                                      n_agents=2,
                                      occupancy_rate=None,
                                      buffer=100,
                                      timestep=1.0,
                                      entrances=[{"name": "1", "floor": "0"}],
                                      facility_name='test_simple_facility',
                                      contact_distance=6.0,
                                      shifts=[{"name": "1", "start_time": 0,
                                              "percent_workforce": 1.0}],
                                      meetings_policy_params=None,
                                      scheduling_policy=None,
                                      traffic_policy=None,
                                      dry_run=False)

    return model


def test_init(simple_facility_model):

    # TODO: this will be unnecessary when the facility class is created
    model = simple_facility_model

    assert model.total_offices == 8
    assert len(model.entrances) == 1

    assert len(model.cafes) == 1
    assert len(model.cafes[0]) == 1

    assert len(model.meeting_rooms) == 1
    assert len(model.meeting_rooms[0]) == 0


def test_create_simid(simple_facility_model):
    model = simple_facility_model
    model.create_simid()
    id1 = model.simid

    model.create_simid()
    id2 = model.simid

    assert isinstance(id1, str)
    assert id1 == id2


def test_add_agents_and_build_schedules(simple_facility_model):

    model = simple_facility_model
    model.add_agents_and_build_schedules()

    assert len(model.agents) == simple_facility_model.n_agents
    for agent in model.agents.values():
        assert agent.schedule is not None


def test_identify_xy_proximity_no_data(simple_facility_model):
    model = simple_facility_model

    positions_vector = np.array([[]])
    indices = model.identify_xy_proximity(positions_vector)

    assert indices.shape == (1, 2)


def test_identify_xy_proximity_same_coords(simple_facility_model):
    model = simple_facility_model
    positions_vector = np.array([[1, 1], [1, 1]])
    indices = model.identify_xy_proximity(positions_vector)

    print(indices)
    assert indices.shape == (4, 2)
    assert (indices[0] == np.array([0, 0])).all()


# def test_identify_contacts():


def test_add_contact_event(simple_facility_model):
    model = simple_facility_model
    agent1 = Agent('1', None)
    agent2 = Agent('2', None)
    model.add_contact_event(agent1, agent2)

    assert len(model.contact_events .contact_data)


# def test_step():

# def test_run_serial():

# def test_extract_contact_distribution_per_agent():

# def tet_save_manifest():

# def test_save_maps():

# def test_create_svg_heatmap():

# def test_save_outputs():


# TODO: Move the functions below to a new class called Facility

# def test_find_and_validate_offices():
# def test_group_remaining_spaces():
# def test_find_valid_floor_office_spaces():
# def test_remove_unreachable_rooms():
# def test_find_possible_entrance_doors():
# def test_find_space_by_name():
# def test_find_floor_by_name():
# def test_is_door_in_navnet():
# def test_validate_entrances():
# def test_choose_best_entrance():
