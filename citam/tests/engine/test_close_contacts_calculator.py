from typing import OrderedDict
import numpy as np
import os
import pytest

from citam.engine.core.agent import Agent

MAP_SVG_FILE = "map.svg"


def test_save_outputs(tmpdir, simple_facility_model):

    model = simple_facility_model
    floor_dir = os.path.join(tmpdir, "floor_0")

    if not os.path.isdir(floor_dir):
        os.mkdir(floor_dir)

    with open(os.path.join(floor_dir, MAP_SVG_FILE), "w") as outfile:
        outfile.write("<svg> <g> </g> </svg>")

    model.calculators[0].finalize(OrderedDict(), work_directory=tmpdir)

    assert os.path.isfile(os.path.join(tmpdir, "contact_dist_per_agent.csv"))
    assert os.path.isfile(os.path.join(tmpdir, "pair_contact.csv"))
    assert os.path.isfile(os.path.join(tmpdir, "raw_contact_data.ccd"))

    assert os.path.isfile(
        os.path.join(floor_dir, "contact_dist_per_coord.csv")
    )


def test_extract_contact_distribution_per_agent(simple_facility_model):

    model = simple_facility_model
    model.create_agents()
    model.calculators[0].initialize(model.agents)
    agent_ids, n_contacts = model.calculators[
        0
    ].extract_contact_distribution_per_agent(model.agents)

    assert len(agent_ids) == 2
    assert len(n_contacts) == 2
    assert n_contacts == [0, 0]


def test_add_contact_event(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (5, 5)
    agent1.current_floor = 0

    agent2 = Agent("2", None)
    agent2.pos = (6, 5)
    agent2.current_floor = 0

    agents = OrderedDict()
    for i, a in enumerate([agent1, agent2]):
        agents[i] = a
    model.calculators[0].initialize(agents)
    model.calculators[0].add_contact_event(0, agent1, agent2)
    contact_pos = (5.5, 5.0)
    key = "1-2"
    assert len(model.calculators[0].contact_events.contact_data) == 1
    assert key in model.calculators[0].contact_events.contact_data
    assert len(model.calculators[0].contact_events.contact_data[key]) == 1
    assert model.calculators[0].contact_events.contact_data[key][
        0
    ].positions == [contact_pos]
    assert len(model.calculators[0].step_contact_locations) == 1
    assert contact_pos in model.calculators[0].step_contact_locations[0]
    assert model.calculators[0].step_contact_locations[0][contact_pos] == 1
    assert agent1.cumulative_properties["contact_duration"] == 1
    assert agent2.cumulative_properties["contact_duration"] == 1


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

    agents = OrderedDict()
    for i, a in enumerate([agent1, agent2, agent3]):
        agents[i] = a
    model.calculators[0].initialize(agents)
    model.calculators[0].run(0, agents.values())
    contact_positions = [(5.5, 5.0), (5.5, 5.5), (6.0, 5.5)]

    assert len(model.calculators[0].contact_events.contact_data) == 3
    assert len(model.calculators[0].step_contact_locations[0]) == 3
    assert agent1.cumulative_properties["contact_duration"] == 2
    assert agent2.cumulative_properties["contact_duration"] == 2
    assert agent3.cumulative_properties["contact_duration"] == 2

    for key, contact_pos in zip(["1-2", "1-3", "2-3"], contact_positions):
        assert key in model.calculators[0].contact_events.contact_data
        assert len(model.calculators[0].contact_events.contact_data[key]) == 1
        assert model.calculators[0].contact_events.contact_data[key][
            0
        ].positions == [contact_pos]
        assert contact_pos in model.calculators[0].step_contact_locations[0]
        assert model.calculators[0].step_contact_locations[0][contact_pos] == 1


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

    agents = OrderedDict()
    for i, a in enumerate([agent1, agent2]):
        agents[i] = a
    model.calculators[0].initialize(agents)
    model.calculators[0].run(0, agents.values())

    assert len(model.calculators[0].contact_events.contact_data) == 0
    assert len(model.calculators[0].step_contact_locations) == 1
    assert len(model.calculators[0].step_contact_locations[0]) == 0
    assert agent1.cumulative_properties["contact_duration"] == 0
    assert agent2.cumulative_properties["contact_duration"] == 0


def test_identify_contacts_outside_facility(simple_facility_model):

    model = simple_facility_model

    agent1 = Agent("1", None)
    agent1.pos = (1, 1)
    agent1.current_floor = 0

    agent2 = Agent("2", None)
    agent2.pos = (1, 1)
    agent2.current_floor = 0
    agent2.current_location = 1

    agents = OrderedDict()
    for i, a in enumerate([agent1, agent2]):
        agents[i] = a
    model.calculators[0].initialize(agents)
    model.calculators[0].run(0, agents.values())

    assert len(model.calculators[0].contact_events.contact_data) == 0
    assert len(model.calculators[0].step_contact_locations) == 1
    assert len(model.calculators[0].step_contact_locations[0]) == 0


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

    agents = OrderedDict()
    for i, a in enumerate([agent1, agent2, agent3]):
        agents[i] = a
    model.calculators[0].initialize(agents)
    model.calculators[0].run(0, agents.values())
    contact_pos = (5.5, 5.0)
    key = "1-2"
    # Only agents 1 and 2 make contact.
    assert len(model.calculators[0].contact_events.contact_data) == 1
    assert key in model.calculators[0].contact_events.contact_data
    assert len(model.calculators[0].contact_events.contact_data[key]) == 1
    assert model.calculators[0].contact_events.contact_data[key][
        0
    ].positions == [contact_pos]
    assert len(model.calculators[0].step_contact_locations) == 1
    assert len(model.calculators[0].step_contact_locations[0]) == 1
    assert contact_pos in model.calculators[0].step_contact_locations[0]
    assert model.calculators[0].step_contact_locations[0][contact_pos] == 1


def test_identify_xy_proximity_no_data(simple_facility_model):
    model = simple_facility_model

    positions_vector = np.array([[]])
    indices = model.calculators[0].identify_xy_proximity(positions_vector)

    assert indices.shape == (1, 2)


def test_identify_xy_proximity_same_coords(simple_facility_model):
    model = simple_facility_model
    positions_vector = np.array([[1, 1], [1, 1]])
    indices = model.calculators[0].identify_xy_proximity(positions_vector)

    assert indices.shape == (4, 2)
    assert (indices[0] == np.array([0, 0])).all()


def test_create_svg_heatmap(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_maps(tmpdir)
    floor_dir = os.path.join(tmpdir, "floor_0")
    model.calculators[0].create_svg_heatmap({(1, 1): 10}, floor_dir)

    assert os.path.isfile(os.path.join(floor_dir, "heatmap.svg"))


def test_create_svg_heatmap_no_map(tmpdir, simple_facility_model):
    model = simple_facility_model
    model.save_maps(tmpdir)
    with pytest.raises(FileNotFoundError):
        model.calculators[0].create_svg_heatmap({(1, 1): 10}, tmpdir)