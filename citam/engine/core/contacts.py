#  Copyright 2020. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
#  ==========================================================================

from citam.engine.core.agent import Agent

from typing import Tuple, Dict, List, Union, Hashable, Any
import typing


def update_data_dictionary(
    datadict: dict, key: Hashable, data: Union[float, int]
) -> dict:
    """
    Utility function to update a dictionary to add data to existing value if
    the key exist or create new key:value pair if not

    :param dict datadict: the dictionary to update
    :param str key: key for the value to update
    :param float or int data: the value to add to current value
    :return: the updated dictionary
    :rtype: dict
    """
    if key not in datadict:
        datadict[key] = data
    else:
        datadict[key] += data

    return datadict


class ContactEvent:
    """
    A contact event object keeps track of the initial timestep and total
    duration as well as the list of xy positions, locations and floor numbers
    of a contact (e.g. two people walking together).
    """

    def __init__(
        self,
        floor_number: int,
        location: int,
        position: Tuple[int, int],
        current_step: int,
    ):
        """
        Initialize a new contact event object.

        :param floor_number: floor number of the contact
        :type floor_number: int
        :param location: id of the space where the contact occurred
        :type location: int
        :param position: xy position of the contact
        :type position: Tuple[int, int]
        :param current_step: the current timestep in the simulation
        :type current_step: int
        """
        self.locations = [location]
        self.floor_numbers = [floor_number]
        self.positions = [position]
        self.start_step = current_step
        self.duration = 1


class ContactEvents:
    """Class to keep track of every time 2 agents come in close proximity"""

    def __init__(self):  # TODO: maybe make this a dict subclass
        """
        Dict-like container to keep track of contact events. Each contact event
        is identified by a custom key made of the ids of the two agents
        involved.

        ..note:: contact events always take place between two agents.
        """

        # Will keep track of the data in a dictionary instead of a matrix so
        # we don't waste space for agents that never come into contact with
        # each other. The key will be made with the unique IDs of agent 1 and
        # agent 2 in "increasing" order (i.e. the smallest always comes first)

        self.contact_data = {}

    def add_contact(
        self,
        agent1: Agent,
        agent2: Agent,
        current_step: int,
        position: Tuple[int, int],
    ) -> None:
        """
        Add single contact event between two agents. If there was a contact
        event in the previous step, update its duration and list of locations.
        The floor number is extracted from the first agent's position.

        ..note: a contact event is identified

        :param agent1: First agent involved in this contact event.
        :type agent1: Agent
        :param agent2: Second agent involved in this contact event.
        :type agent2: Agent
        :param current_step: Current timestep of the simulation
        :type current_step: int
        :param position: xy position of contact
        :type position: Tuple[int, int]
        :raises ValueError: If the two agents have the same ID.
        """
        floor_number = agent1.current_floor
        # TODO: find location of contacts based on xy position
        location = agent1.current_location
        new_contact_event = ContactEvent(
            floor_number, location, position, current_step
        )

        if agent1.unique_id == agent2.unique_id:
            raise ValueError("Agents must be different.")

        if agent1.unique_id < agent2.unique_id:
            key = str(agent1.unique_id) + "-" + str(agent2.unique_id)
        else:
            key = str(agent2.unique_id + "-" + str(agent1.unique_id))

        if key in self.contact_data:
            last_contact = self.contact_data[key][-1]
            if last_contact.start_step + last_contact.duration == current_step:
                # This is the same contact event that's continuing
                self.contact_data[key][-1].duration += 1
                self.contact_data[key][-1].positions.append(position)
                self.contact_data[key][-1].locations.append(location)
                self.contact_data[key][-1].floor_numbers.append(floor_number)
            else:  # This is a new contact event
                self.contact_data[key].append(new_contact_event)
        else:
            self.contact_data[key] = [new_contact_event]

    def count(self) -> int:
        """compute the total number of unique contact events. A unique contact
        event involves two specific agents and has a start and end time.

        ..Note: two agents can have more than 1 unique contact event.

        :return: total number of unique contact events
        :rtype: int
        """
        return sum(len(self.contact_data[key]) for key in self.contact_data)

    def save_pairwise_contacts(self, filename: str) -> None:
        """
        Save pairwise contact data to file. The file is saved in a CSV format
        with the following columns: Agent1, Agent2, total contacts and total
        contact duration.

        ..note: this is an aggregate over all the contacts between two agents.

        :param filename: name of the file
        :type filename: str
        """
        with open(filename, "w") as outfile:
            outfile.write("Agent1,Agent2,N_Contacts,TotalContactDuration\n")
            for key in self.contact_data:
                agent1 = key.split("-")[0]
                agent2 = key.split("-")[1]
                n_contacts = str(len(self.contact_data[key]))
                cont_durations = [ce.duration for ce in self.contact_data[key]]
                total_duration = str(sum(cont_durations))
                outfile.write(
                    agent1
                    + ","
                    + agent2
                    + ","
                    + n_contacts
                    + ","
                    + total_duration
                    + "\n"
                )

    @typing.no_type_check
    def extract_statistics(self) -> List[Dict[str, Any]]:
        """Extract important contact statistics from contact data.

        :return: list of dictionaries of important statistics. Each stat is
                given by its name, value and unit.
        :rtype: list[dict[str, Dict]]
        """
        statistics = []

        # total number of people an agent has contact with
        n_others: Dict[str, int] = {}
        # total contacts of a given agent (an agent may have multiple contacts
        #  with the same person)
        total_contacts_per_agent: Dict[str, int] = {}
        # total contact duration of this agent with everyone in the facility.
        # This value can be really large (e.g. if someone goes to a 30-min
        # meeting with 10 other people, the total contact for this person is
        # 300 min)
        total_contact_duration_per_agent: Dict[str, int] = {}
        overall_total_contact_duration = 0
        for key in self.contact_data:
            agent1 = key.split("-")[0]
            agent2 = key.split("-")[1]
            n_contacts = len(self.contact_data[key])
            cont_durations = [ce.duration for ce in self.contact_data[key]]
            overall_total_contact_duration += sum(cont_durations)

            total_contacts_per_agent = update_data_dictionary(
                total_contacts_per_agent, agent1, n_contacts
            )

            total_contacts_per_agent = update_data_dictionary(
                total_contacts_per_agent, agent2, n_contacts
            )

            total_contact_duration_per_agent = update_data_dictionary(
                total_contact_duration_per_agent, agent1, sum(cont_durations)
            )
            total_contact_duration_per_agent = update_data_dictionary(
                total_contact_duration_per_agent, agent2, sum(cont_durations)
            )

            n_others = update_data_dictionary(n_others, agent1, 1)

        statistics.append(
            {
                "name": "overall_total_contact_duration",
                "value": round(overall_total_contact_duration / 60.0, 2),
                "unit": "min",
            }
        )

        n_agents_with_contact = len(total_contacts_per_agent)
        avg_n_contacts_per_agent = 0
        if n_agents_with_contact > 0:
            avg_n_contacts_per_agent = (
                sum(total_contacts_per_agent.values()) / n_agents_with_contact
            )
        statistics.append(
            {
                "name": "avg_n_contacts_per_agent",
                "value": round(avg_n_contacts_per_agent, 2),
                "unit": "",
            }
        )

        total_contact_duration = sum(total_contact_duration_per_agent.values())
        avg_contact_duration_per_agent = 0
        if n_agents_with_contact > 0:
            avg_contact_duration_per_agent = total_contact_duration / (
                n_agents_with_contact * 2.0
            )
        statistics.append(
            {
                "name": "avg_contact_duration_per_agent",
                "value": round(avg_contact_duration_per_agent / 60.0, 2),
                "unit": "min",
            }
        )

        statistics.append(
            {
                "name": "n_agents_with_contacts",
                "value": n_agents_with_contact,
                "unit": "",
            }
        )

        avg_number_of_people_per_agent = 0
        if n_agents_with_contact > 0:
            avg_number_of_people_per_agent = (
                sum(n_others.values()) / n_agents_with_contact
            )
        statistics.append(
            {
                "name": "avg_number_of_people_per_agent",
                "value": round(avg_number_of_people_per_agent, 2),
                "unit": "",
            }
        )

        max_contacts = 0
        if len(total_contacts_per_agent) > 0:
            max_contacts = max(total_contacts_per_agent.values())
        statistics.append(
            {"name": "max_contacts", "value": max_contacts, "unit": ""}
        )

        return statistics

    def get_floor_contact_coords(
        self, key: str, floor_number: int
    ) -> List[Tuple[int, int]]:
        """
        Iterate over all contact events associated with key (referring to two
        specific agents), and return the ones that took place on given floor
        number.

        :param key: the pair of agents given by a key of the form
            <agent1_id>-<agent2_id> where agent1_id < agent2_id.
        :type key: str
        :param floor_number: index of the floor of interest.
        :type floor_number: int
        :return: the xy coordinates of where contacts took place
        :rtype: List[Tuple[int, int]]
        """

        floor_positions = []
        for ce in self.contact_data[key]:
            for i, pos in enumerate(ce.positions):
                if ce.floor_numbers[i] == floor_number:
                    floor_positions.append(pos)

        return floor_positions

    def get_contacts_per_coordinates(
        self, step: int, floor_number: int
    ) -> Dict[Tuple[int, int], int]:
        """
        Save per coordinate contact data to file.

        :param step: Simulation step for which to extract contact data.
        :type step: int
        :param floor_number: Floor number for which to extract data.
        :type floor_number: int
        :return: Dictionary of contacts per location with xy positions as keys
        :rtype: Dict[Tuple[int, int], int]
        """

        contacts_per_location: Dict[Tuple[int, int], int] = {}

        for key in self.contact_data:
            floor_positions = self.get_floor_contact_coords(key, floor_number)
            unique_positions = list(set(floor_positions))
            for pos in unique_positions:
                count = floor_positions.count(pos)

                contacts_per_location = update_data_dictionary(
                    contacts_per_location, pos, count
                )
        return contacts_per_location

    def save_raw_contact_data(self, filename: str) -> None:
        """
        Save all contact data to file.

        This will write all the contact information in this simulation to file
        (can be big). The data will be converted to a dictionary of list of
        dictionaries where the top dictionary is keyed by agent_id - agent_id
        with their corresponding list of contacts. Each contact event is
        represented by a dictionary with property names and values of the
        ContactEvent class.

        :param filename: The file path to save the data
        :type filename: str
        """
        data_to_save = {
            key: [v.__dict__ for v in value]
            for key, value in self.contact_data.items()
        }

        with open(filename, "w") as outfile:
            outfile.write(str(data_to_save))

    # TODO: create function to add 2 contact_events objects
