import os
import json


MAP_SVG_FILE = "map.svg"


def test_create_sim_hash(simple_facility_model):
    model = simple_facility_model
    model.create_sim_hash()

    name1 = model.simulation_hash

    model.create_sim_hash()
    name2 = model.simulation_hash

    assert isinstance(name1, str)
    assert name1 == name2


def test_create_agents(simple_facility_model):

    model = simple_facility_model
    model.create_agents()

    assert len(model.agents) == simple_facility_model.n_agents
    for agent in model.agents.values():
        assert agent.schedule is not None


def test_step(simple_facility_model):

    model = simple_facility_model
    model.step()

    assert model.current_step == 1
    assert len(model.calculators[0].step_contact_locations) == 1
    assert len(model.calculators[0].step_contact_locations[0]) == 0


def test_run_serial(simple_facility_model, tmpdir):

    model = simple_facility_model
    model.run_serial(tmpdir, "sim_name", "run_name")

    assert len(model.agents) == model.n_agents
    for agent in model.agents.values():
        assert agent.schedule is not None
    assert model.current_step == model.total_timesteps
    assert os.path.isfile(os.path.join(tmpdir, "manifest.json"))
    assert os.path.isfile(os.path.join(tmpdir, "trajectory.txt"))
    assert os.path.isfile(os.path.join(tmpdir, "floor_0", MAP_SVG_FILE))
    assert os.path.isfile(os.path.join(tmpdir, "floor_0", "contacts.txt"))


def test_save_manifest(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_manifest(tmpdir, "sim_name", "run_name")
    manifest_file = os.path.join(tmpdir, "manifest.json")
    assert os.path.isfile(manifest_file)

    with open(manifest_file, "r") as infile:
        data = json.load(infile)

    assert "RunID" in data
    assert "RunName" in data
    assert "SimulationName" in data
    assert "SimulationHash" in data
    assert "TimestepInSec" in data
    assert "NumberOfFloors" in data
    assert "NumberOfOneWayAisles" in data
    assert "NumberOfAgents" in data
    assert data["NumberOfAgents"] == 2
    assert "SimulationName" in data
    assert "FacilityName" in data
    assert "MaxRoomOccupancy" in data
    assert "NumberOfShifts" in data
    assert "NumberOfEntrances" in data
    assert "NumberOfExits" in data
    assert "EntranceScreening" in data
    assert "TrajectoryFile" in data
    assert "Floors" in data
    assert len(data["Floors"]) == 1
    assert "ScaleMultiplier" in data
    assert "Timestep" in data


def test_save_maps(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_maps(tmpdir)
    assert os.path.isfile(os.path.join(tmpdir, "floor_0", MAP_SVG_FILE))
