from citam.engine.calculators.contacts import ContactEvents, ContactEvent
from citam.engine.core.agent import Agent

import pytest
from copy import deepcopy
import os


@pytest.fixture
def sample_contacts():

    contact = ContactEvent(
        floor_number=0, location=0, position=(1, 1), current_step=0
    )

    contacts = ContactEvents()
    contacts.contact_data["0-1"] = [deepcopy(contact)]
    contacts.contact_data["0-2"] = [deepcopy(contact)]
    contacts.contact_data["1-2"] = [contact]

    return contacts


def test_init():

    contacts = ContactEvents()

    assert isinstance(contacts.contact_data, dict)
    assert len(contacts.contact_data) == 0


def test_add_contact_simple():

    agent1 = Agent(1, None)
    agent2 = Agent(2, None)
    position = (10, 10)

    contacts = ContactEvents()
    contacts.add_contact(agent1, agent2, current_step=0, position=position)

    key = "1-2"
    assert len(contacts.contact_data) == 1
    assert key in contacts.contact_data
    assert len(contacts.contact_data[key]) == 1
    assert contacts.contact_data[key][0].duration == 1
    assert contacts.contact_data[key][0].start_step == 0
    assert contacts.contact_data[key][0].positions == [position]


def test_add_contact_extend():

    agent1 = Agent(1, None)
    agent2 = Agent(2, None)
    position1 = (10, 10)
    position2 = (12, 15)

    contacts = ContactEvents()
    contacts.add_contact(agent1, agent2, current_step=0, position=position1)

    contacts.add_contact(agent1, agent2, current_step=1, position=position2)

    key = "1-2"
    assert len(contacts.contact_data) == 1
    assert key in contacts.contact_data
    assert len(contacts.contact_data[key]) == 1
    assert len(contacts.contact_data[key][0].positions) == 2
    assert contacts.contact_data[key][0].positions == [position1, position2]
    assert contacts.contact_data[key][0].duration == 2


def test_add_contact_extend2(sample_contacts):

    agent1 = Agent(1, None)
    agent2 = Agent(2, None)
    position = (10, 10)

    sample_contacts.add_contact(
        agent1, agent2, current_step=3, position=position
    )

    key = "1-2"
    assert len(sample_contacts.contact_data) == 3
    assert len(sample_contacts.contact_data[key]) == 2
    assert len(sample_contacts.contact_data[key][0].positions) == 1


def test_count(sample_contacts):
    ncontacts = sample_contacts.count()
    assert ncontacts == 3


def test_count_no_contact():
    ncontacts = ContactEvents().count()
    assert ncontacts == 0


def test_save_pairwise_contacts(tmpdir, sample_contacts):

    filename = os.path.join(tmpdir, "test.txt")
    sample_contacts.save_pairwise_contacts(filename)

    assert os.path.isfile(filename)
    n = 0
    with open(filename, "r") as infile:
        infile.readline()
        for line in infile:
            data = line.strip().split(",")
            n += 1
            assert int(data[-1]) == 1
    assert n == 3


def test_save_pairwise_contacts2(tmpdir):

    filename = os.path.join(tmpdir, "test2.txt")
    agent1 = Agent("1", None)
    agent2 = Agent("2", None)

    contacts = ContactEvents()
    contacts.add_contact(agent1, agent2, 0, (10, 12))
    contacts.add_contact(agent1, agent2, 1, (10, 15))
    contacts.add_contact(agent1, agent2, 2, (10, 20))
    contacts.add_contact(agent1, agent2, 4, (15, 20))

    contacts.save_pairwise_contacts(filename)

    assert os.path.isfile(filename)
    n = 0
    with open(filename, "r") as infile:
        infile.readline()
        for line in infile:
            data = line.strip().split(",")
            n += 1
            assert int(data[-1]) == 4
    assert n == 1


def test_extract_statistics(sample_contacts):

    agent1 = Agent("1", None)
    agent2 = Agent("2", None)
    sample_contacts.add_contact(agent1, agent2, 1, (10, 12))
    sample_contacts.add_contact(agent1, agent2, 2, (10, 22))

    stats = sample_contacts.extract_statistics()

    assert len(stats) == 6
    for stat in stats:
        assert "name" in stat
        assert "value" in stat
        assert "unit" in stat

    assert stats[0]["name"] == "overall_total_contact_duration"
    assert stats[0]["value"] == round(5 / 60.0, 2)  # in minutes

    assert stats[1]["name"] == "avg_n_contacts_per_agent"
    assert stats[1]["value"] == 2.0

    assert stats[2]["name"] == "avg_contact_duration_per_agent"
    assert stats[2]["value"] == round(5 / (3 * 60), 2)  # in minutes

    assert stats[3]["name"] == "n_agents_with_contacts"
    assert stats[3]["value"] == 3

    assert stats[4]["name"] == "avg_number_of_people_per_agent"
    assert stats[4]["value"] == 1

    assert stats[5]["name"] == "max_contacts"
    assert stats[5]["value"] == 2


def test_extract_statistics_no_data():

    contacts = ContactEvents()
    stats = contacts.extract_statistics()

    assert len(stats) == 6
    for stat in stats:
        assert "name" in stat
        assert "value" in stat
        assert "unit" in stat

    assert stats[0]["name"] == "overall_total_contact_duration"
    assert stats[0]["value"] == 0  # in minutes

    assert stats[1]["name"] == "avg_n_contacts_per_agent"
    assert stats[1]["value"] == 0

    assert stats[2]["name"] == "avg_contact_duration_per_agent"
    assert stats[2]["value"] == 0  # in minutes

    assert stats[3]["name"] == "n_agents_with_contacts"
    assert stats[3]["value"] == 0

    assert stats[4]["name"] == "avg_number_of_people_per_agent"
    assert stats[4]["value"] == 0

    assert stats[5]["name"] == "max_contacts"
    assert stats[5]["value"] == 0


def test_get_floor_contact_coords(sample_contacts):
    floor_positions = sample_contacts.get_floor_contact_coords("1-2", 0)

    assert len(floor_positions) == 1
    assert floor_positions == [(1, 1)]


def test_get_floor_contact_coords_2(sample_contacts):

    agent1 = Agent("1", None)
    agent2 = Agent("2", None)
    agent1.current_floor = 0
    sample_contacts.add_contact(agent1, agent2, 1, (10, 12))
    sample_contacts.add_contact(agent1, agent2, 2, (10, 22))
    floor_positions = sample_contacts.get_floor_contact_coords("1-2", 0)

    assert len(floor_positions) == 3
    assert floor_positions == [(1, 1), (10, 12), (10, 22)]


def test_get_floor_contact_coords_3(sample_contacts):

    agent1 = Agent("1", None)
    agent2 = Agent("2", None)

    agent1.current_floor = 1
    sample_contacts.add_contact(agent1, agent2, 1, (10, 12))

    agent1.current_floor = 2
    sample_contacts.add_contact(agent1, agent2, 2, (10, 22))

    floor_positions = sample_contacts.get_floor_contact_coords("1-2", 0)
    assert len(floor_positions) == 1
    assert floor_positions == [(1, 1)]

    floor_positions = sample_contacts.get_floor_contact_coords("1-2", 1)
    assert len(floor_positions) == 1
    assert floor_positions == [(10, 12)]

    floor_positions = sample_contacts.get_floor_contact_coords("1-2", 2)
    assert len(floor_positions) == 1
    assert floor_positions == [(10, 22)]


def test_get_contacts_per_coordinates(sample_contacts):

    contacts_per_location = sample_contacts.get_contacts_per_coordinates(0, 0)

    assert len(contacts_per_location) == 1
    assert (1, 1) in contacts_per_location
    assert contacts_per_location[(1, 1)] == 3


def test_save_raw_contact_data(tmpdir, sample_contacts):
    filename = os.path.join(tmpdir, "test.dat")
    sample_contacts.save_raw_contact_data(filename)

    assert os.path.isfile(filename)
