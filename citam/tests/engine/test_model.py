from citam.engine.core.model import FacilityTransmissionModel
from citam.engine.core.agent import Agent

import os
import pytest
import numpy as np
import json


@pytest.fixture
def simple_facility_model(simple_facility_floorplan, monkeypatch, request):
    filename = request.module.__file__
    test_dir = os.path.dirname(filename)
    datadir = os.path.join(test_dir, "data_navigation")
    monkeypatch.setenv("CITAM_CACHE_DIRECTORY", str(datadir))

    model = FacilityTransmissionModel(
        [simple_facility_floorplan],
        daylength=3600,
        n_agents=2,
        occupancy_rate=None,
        buffer=100,
        timestep=1.0,
        entrances=[{"name": "1", "floor": "0"}],
        facility_name="test_simple_facility",
        contact_distance=6.0,
        shifts=[{"name": "1", "start_time": 0, "percent_workforce": 1.0}],
        meetings_policy_params=None,
        scheduling_policy=None,
        traffic_policy=None,
        dry_run=False,
    )

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

    assert indices.shape == (4, 2)
    assert (indices[0] == np.array([0, 0])).all()


def test_identify_contacts(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (5, 5)
    agent1.current_floor = 0
    agent1.current_location = 0

    agent2 = Agent("2", None)
    agent2.pos = (6, 5)
    agent2.current_floor = 0
    agent2.current_location = 0

    agent3 = Agent("3", None)
    agent3.pos = (16, 50)
    agent3.current_floor = 0
    agent3.current_location = 0

    model.identify_contacts([agent1, agent2, agent3])
    contact_pos = (5.5, 5.0)
    key = "1-2"
    # Only agents 1 and 2 make contact.
    assert len(model.contact_events.contact_data) == 1
    assert key in model.contact_events.contact_data
    assert len(model.contact_events.contact_data[key]) == 1
    assert model.contact_events.contact_data[key][0].positions == [contact_pos]
    assert len(model.step_contact_locations) == 1
    assert len(model.step_contact_locations[0]) == 1
    assert contact_pos in model.step_contact_locations[0]
    assert model.step_contact_locations[0][contact_pos] == 1


def test_identify_contacts_outside_facility(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (1, 1)
    agent1.current_floor = 0

    agent2 = Agent("2", None)
    agent2.pos = (1, 1)
    agent2.current_floor = 0
    agent2.current_location = 1

    model.identify_contacts([agent1, agent2])

    assert len(model.contact_events.contact_data) == 0
    assert len(model.step_contact_locations) == 1
    assert len(model.step_contact_locations[0]) == 0


def test_identify_contacts_wall_seperation(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (10, 1)
    agent1.current_floor = 0
    agent1.current_location = 0

    agent2 = Agent("2", None)
    agent2.pos = (10, -1)
    agent2.current_floor = 0
    agent2.current_location = 1

    model.identify_contacts([agent1, agent2])

    assert len(model.contact_events.contact_data) == 0
    assert len(model.step_contact_locations) == 1
    assert len(model.step_contact_locations[0]) == 0
    assert agent1.n_contacts == 0
    assert agent2.n_contacts == 0


def test_identify_contacts_3_way(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (5, 5)
    agent1.current_floor = 0
    agent1.current_location = 0

    agent2 = Agent("2", None)
    agent2.pos = (6, 5)
    agent2.current_floor = 0
    agent2.current_location = 0

    agent3 = Agent("3", None)
    agent3.pos = (6, 6)
    agent3.current_floor = 0
    agent3.current_location = 0

    model.identify_contacts([agent1, agent2, agent3])
    contact_positions = [(5.5, 5.0), (5.5, 5.5), (6.0, 5.5)]

    assert len(model.contact_events.contact_data) == 3
    assert len(model.step_contact_locations[0]) == 3
    assert agent1.n_contacts == 2
    assert agent2.n_contacts == 2
    assert agent3.n_contacts == 2

    for key, contact_pos in zip(["1-2", "1-3", "2-3"], contact_positions):
        assert key in model.contact_events.contact_data
        assert len(model.contact_events.contact_data[key]) == 1
        assert model.contact_events.contact_data[key][0].positions == [
            contact_pos
        ]
        assert contact_pos in model.step_contact_locations[0]
        assert model.step_contact_locations[0][contact_pos] == 1


def test_add_contact_event(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (5, 5)
    agent1.current_floor = 0

    agent2 = Agent("2", None)
    agent2.pos = (6, 5)
    agent2.current_floor = 0

    model.add_contact_event(agent1, agent2)
    contact_pos = (5.5, 5.0)
    key = "1-2"
    assert len(model.contact_events.contact_data) == 1
    assert key in model.contact_events.contact_data
    assert len(model.contact_events.contact_data[key]) == 1
    assert model.contact_events.contact_data[key][0].positions == [contact_pos]
    assert len(model.step_contact_locations) == 1
    assert contact_pos in model.step_contact_locations[0]
    assert model.step_contact_locations[0][contact_pos] == 1
    assert agent1.n_contacts == 1
    assert agent2.n_contacts == 1


def test_step(simple_facility_model):

    model = simple_facility_model
    model.step()

    assert model.current_step == 1
    assert len(model.contact_events.contact_data) == 0
    assert len(model.step_contact_locations) == 1
    assert len(model.step_contact_locations[0]) == 0


def test_run_serial(simple_facility_model, tmpdir):

    model = simple_facility_model
    model.run_serial(tmpdir)

    assert model.meeting_policy is not None
    assert len(model.agents) == model.n_agents
    for agent in model.agents.values():
        assert agent.schedule is not None
    assert model.current_step == model.daylength + model.buffer
    assert os.path.isfile(os.path.join(tmpdir, "manifest.json"))
    assert os.path.isfile(os.path.join(tmpdir, "trajectory.txt"))
    assert os.path.isfile(os.path.join(tmpdir, "floor_0", "map.svg"))
    assert os.path.isfile(os.path.join(tmpdir, "floor_0", "contacts.txt"))


def test_extract_contact_distribution_per_agent(simple_facility_model):

    model = simple_facility_model
    model.add_agents_and_build_schedules()
    agent_ids, n_contacts = model.extract_contact_distribution_per_agent()

    assert len(agent_ids) == 2
    assert len(n_contacts) == 2
    assert n_contacts == [0, 0]


def test_save_manifest(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_manifest(tmpdir)
    manifest_file = os.path.join(tmpdir, "manifest.json")
    assert os.path.isfile(manifest_file)

    with open(manifest_file, "r") as infile:
        data = json.load(infile)

    assert "SimulationID" in data
    assert "TimestepInSec" in data
    assert "NumberOfFloors" in data
    assert "NumberOfOneWayAisles" in data
    assert "NumberOfEmployees" in data
    assert data["NumberOfEmployees"] == 0
    assert "SimulationName" in data
    assert "Campus" in data
    assert "FacilityOccupancy" in data
    assert data["FacilityOccupancy"] is None
    assert "MaxRoomOccupancy" in data
    assert "NumberOfShifts" in data
    assert "NumberOfEntrances" in data
    assert "NumberOfExits" in data
    assert "EntranceScreening" in data
    assert "trajectory_file" in data
    assert "floors" in data
    assert len(data["floors"]) == 1
    assert "scaleMultiplier" in data
    assert "timestep" in data


def test_save_maps(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_maps(tmpdir)
    assert os.path.isfile(os.path.join(tmpdir, "floor_0", "map.svg"))


def test_create_svg_heatmap(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_maps(tmpdir)
    floor_dir = os.path.join(tmpdir, "floor_0")
    model.create_svg_heatmap({(1, 1): 10}, floor_dir)

    assert os.path.isfile(os.path.join(floor_dir, "heatmap.svg"))


def test_create_svg_heatmap_no_map(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_maps(tmpdir)
    with pytest.raises(FileNotFoundError):
        model.create_svg_heatmap({(1, 1): 10}, tmpdir)


def test_save_outputs(tmpdir, simple_facility_model):

    model = simple_facility_model
    floor_dir = os.path.join(tmpdir, "floor_0")

    if not os.path.isdir(floor_dir):
        os.mkdir(floor_dir)

    with open(os.path.join(floor_dir, "map.svg"), "w") as outfile:
        outfile.write("<svg> <g> </g> </svg>")

    model.save_outputs(tmpdir)

    assert os.path.isfile(os.path.join(tmpdir, "contact_dist_per_agent.csv"))
    assert os.path.isfile(os.path.join(tmpdir, "agent_ids.txt"))
    assert os.path.isfile(os.path.join(tmpdir, "pair_contact.csv"))
    assert os.path.isfile(os.path.join(tmpdir, "raw_contact_data.ccd"))

    assert os.path.isfile(
        os.path.join(floor_dir, "contact_dist_per_coord.csv")
    )

    # TODO: validate contents of each file


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
