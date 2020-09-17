# Copyright 2020. Corning Incorporated. All rights reserved.
#
# This software may only be used in accordance with the licenses granted by
# Corning Incorporated. All other uses as well as any copying, modification or
# reverse engineering of the software is strictly prohibited.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================

import logging


def update_data_dictionary(datadict: dict, key: str, data: float | int) -> dict:
    """
    Utility function to update a dictionary to add data to existing value if
    the key exist or create new key:value pair if not

    :param:
    """
    if key not in datadict:
        datadict[key] = data
    else:
        datadict[key] += data

    return datadict


class ContactEvent:

    def __init__(self, floor_number, location, position, current_step):
        super().__init__()
        self.locations = [location]
        self.floor_numbers = [floor_number]
        self.positions = [position]
        self.start_step = current_step
        self.duration = 1


class ContactEvents:
    """Class to keep track of every time 2 agents come in close proximity
    """

    def __init__(self):
        super().__init__()

        # Will keep track of the data in a dictionary instead of a matrix so
        # we don't waste space for agents that never come into contact with
        # each other. The key will be make with the unique ID of agent 1 and
        # unique ID or agent 2 in "increasing" order

        self.contact_data = {}

        return

    def add_contact(self,
                    agent1,
                    agent2,
                    current_step,
                    position
                    ):
        """Add single contact event to this.
        """
        floor_number = agent1.current_floor
        # TODO: find location of contacts based on xy position
        location = agent1.current_location
        new_contact_event = ContactEvent(floor_number,
                                         location,
                                         position,
                                         current_step)

        if agent1.unique_id == agent2.unique_id:
            raise ValueError('Agents must be different.')

        if agent1.unique_id < agent2.unique_id:
            key = str(agent1.unique_id) + '-' + str(agent2.unique_id)
        else:
            key = str(agent2.unique_id + '-' + str(agent1.unique_id))

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

        return

    def count(self):
        """compute the total number of contacts
        """
        n_contacts = 0
        for key in self.contact_data:
            n_contacts += len(self.contact_data[key])

        return n_contacts

    def save_pairwise_contacts(self, filename):
        """Output pairwise contact data to file
        """
        with open(filename, 'w') as outfile:
            outfile.write('Agent1,Agent2,N_Contacts,TotalContactDuration\n')
            for key in self.contact_data:
                agent1 = key.split('-')[0]
                agent2 = key.split('-')[1]
                n_contacts = str(len(self.contact_data[key]))
                cont_durations = [ce.duration for ce in self.contact_data[key]]
                total_duration = str(sum(cont_durations))
                outfile.write(agent1 + ',' + agent2 + ',' + n_contacts +
                              ',' + total_duration + '\n')

        return

    def exatract_statistics(self):
        """Extract key contact statistics from contact data
        """
        statistics = []

        n_others = {}
        total_contacts_per_agent = {}
        total_contact_duration_per_agent = {}
        overall_total_contact_duration = 0
        for key in self.contact_data:
            agent1 = key.split('-')[0]
            agent2 = key.split('-')[1]
            n_contacts = len(self.contact_data[key])
            cont_durations = [ce.duration for ce in self.contact_data[key]]
            overall_total_contact_duration += sum(cont_durations)

            total_contacts_per_agent = \
                update_data_dictionary(total_contacts_per_agent,
                                       agent1,
                                       n_contacts
                                       )

            total_contacts_per_agent = \
                update_data_dictionary(total_contacts_per_agent,
                                       agent2,
                                       n_contacts
                                       )

            total_contact_duration_per_agent = \
                update_data_dictionary(total_contact_duration_per_agent,
                                       agent1,
                                       sum(cont_durations)
                                       )
            total_contact_duration_per_agent = \
                update_data_dictionary(total_contact_duration_per_agent,
                                       agent2,
                                       sum(cont_durations)
                                       )

            n_others = update_data_dictionary(n_others, agent1, 1)

        stat = {'name': 'overall_total_contact_duration',
                'value': round(overall_total_contact_duration / 60.0, 2),
                'unit': 'min'
                }
        statistics.append(stat)

        n_agents_with_contact = len(total_contacts_per_agent)
        avg_n_contacts_per_agent = \
            sum(total_contacts_per_agent.values()) / n_agents_with_contact
        stat = {'name': 'avg_n_contacts_per_agent',
                'value': round(avg_n_contacts_per_agent, 2),
                'unit': ''
                }
        statistics.append(stat)

        total_contact_duration = sum(total_contact_duration_per_agent.values())
        avg_contact_duration_per_agent = \
            total_contact_duration / n_agents_with_contact
        stat = {'name': 'avg_contact_duration_per_agent',
                'value': round(avg_contact_duration_per_agent / 60.0, 2),
                'unit': 'min'
                }
        statistics.append(stat)

        stat = {'name': 'n_agents_with_contacts',
                'value': n_agents_with_contact,
                'unit': ''
                }

        avg_number_of_people_per_agent = \
            sum(n_others.values()) / n_agents_with_contact
        stat = {'name': 'avg_number_of_people_per_agent',
                'value': round(avg_number_of_people_per_agent, 2),
                'unit': ''
                }
        statistics.append(stat)

        return statistics

    def get_floor_contact_coords(self, key, floor_number):
        """
        Iterate over all contact events associated with key, and return
        the ones that correspond to floor number.
        """
        floor_positions = []
        for ce in self.contact_data[key]:
            for i, pos in enumerate(ce.positions):
                if ce.floor_numbers[i] == floor_number:
                    floor_positions.append(pos)

        return floor_positions

    def get_contacts_per_coordinates(self, step, floor_number):
        """Save per coordinate contact data to file
        """
        contacts_per_location = {}

        for key in self.contact_data:
            floor_positions = self.get_floor_contact_coords(key, floor_number)
            unique_positions = list(set(floor_positions))
            for pos in unique_positions:
                count = floor_positions.count(pos)

                contacts_per_location = \
                    update_data_dictionary(contacts_per_location,
                                           pos,
                                           count
                                           )
        return contacts_per_location

    def save_raw_contact_data(self, filename):
        """Save all contact data to file
        """
        # List of dictionaries (one dictionary for each contact event)
        contact_list = []
        for key in self.contact_data:
            for ce in self.contact_data[key]:
                contact_list.append(ce.__dict__)

        with open(filename, 'w') as outfile:
            outfile.write(str(contact_list))

        return

    # TODO: create function to add to concatenate 2 contact_events objects
