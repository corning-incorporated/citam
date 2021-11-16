from typing import Dict, List, Optional, OrderedDict, Tuple, Union

from citam.engine.calculators.calculator import Calculator
from citam.engine.facility.indoor_facility import Facility
from citam.engine.core.agent import Agent
import citam.engine.calculators.contacts as cev

import numpy as np
import scipy.spatial.distance
import os
import json
import xml.etree.ElementTree as ET
from matplotlib import cm


ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


class CloseContactsCalculator(Calculator):
    def __init__(
        self,
        facility: Facility,
        contact_distance: float = 6.0,
    ) -> None:
        super().__init__(facility)
        self.facility = facility
        self.contact_distance = contact_distance

        # Object to keep track of contact events
        self.contact_events = cev.ContactEvents()

        # list used to keep track of total contact events per xy location per
        #  floor
        self.step_contact_locations: List[Dict[Tuple[int, int], int]] = [
            {} for _ in facility.floorplans
        ]
        self.data_outfiles = []

    def initialize(
        self,
        agents: OrderedDict[int, Agent],
        workdir: Optional[Union[os.PathLike, str]] = None,
    ):
        for a in agents.values():
            # Make sure another calculator is not setting
            #  the contact duration property
            if "contact_duration" in a.cumulative_properties:
                raise ValueError(
                    "The close contacts calculator is clashing with another "
                    "calculator. Please double check."
                )
            a.cumulative_properties["contact_duration"] = 0

        # Opening output files
        self.data_outfiles = []
        if not workdir:
            return
        for floor_number in range(self.facility.number_of_floors):
            directory = os.path.join(workdir, "floor_" + str(floor_number))
            contact_file = os.path.join(directory, "contacts.txt")
            self.data_outfiles.append(open(contact_file, "w"))

    def run(
        self,
        current_step: int,
        active_agents: List[Agent],
    ) -> None:
        """
        Iterate over agents, compute whether they fall within the contact
        distance or not and verify that they are indeed making contact (based
        on whether they are in the same space or not).

        :param agents: list of agents under consideration for contact
            statistics
        :type agents: List[Agent]
        :param contact_outfiles: Files to write contact data, one per floor,
                defaults to None
        :type contact_outfiles: List[TextIO], optional
        """
        # Immediately discard contact event if either:
        # 1. agents are in different floors
        # 2. agents are in different spaces but only if the spaces
        #    are not neighbors in the hallway graphs

        self.step_contact_locations = [
            {}
        ] * self.facility.number_of_floors  # One per floor

        # At least 2 agents required.
        if len(active_agents) <= 1:
            return

        # Only consider active agents
        agents = [a for a in active_agents if a.current_location is not None]

        if len(agents) == 0:
            # Nothing to do
            return

        positions_vector = np.array([a.pos for a in agents])
        proximity_indices = self.identify_xy_proximity(positions_vector)

        for i, j in proximity_indices:
            if i >= j:  # only consider upper right side of symmetric matrix
                continue
            agent1 = agents[i]
            agent2 = agents[j]

            if (
                agent1.current_location is None
                or agent2.current_location is None
            ):
                continue

            if agent1.current_floor == agent2.current_floor:
                fn = agent1.current_floor
                if agent1.current_location == agent2.current_location:
                    self.add_contact_event(current_step, agent1, agent2)

                else:
                    self.verify_and_add_contact(
                        current_step, fn, agent1, agent2
                    )

        if self.data_outfiles:
            for fn in range(self.facility.number_of_floors):

                n_contact_loc = len(self.step_contact_locations[fn])
                self.data_outfiles[fn].write(
                    str(n_contact_loc) + "\nstep :" + str(current_step) + "\n"
                )

                for cl, nc in self.step_contact_locations[fn].items():
                    self.data_outfiles[fn].write(
                        str(cl[0]) + "\t" + str(cl[1]) + "\t" + str(nc) + "\n"
                    )

    def finalize(
        self,
        agents: List[Agent],
        work_directory: Optional[Union[str, bytes, os.PathLike]] = None,
    ) -> None:
        for cof in self.data_outfiles:
            cof.close()
        if work_directory:
            self.save_to_files(
                agents,
                work_directory,
            )

    def identify_xy_proximity(
        self, positions_vector: np.ndarray
    ) -> np.ndarray:
        """
        Compute pairwise distances, given a vector of xy positions, and
        return the indices of the ones that fall within the given contact
        distance.

        :param positions_vector: Array of current xy positions of all active
                agents
        :type positions_vector: np.ndarray
        :return: Array of indices of agents that are within the contact
            distance of each other
        :rtype: np.ndarray
        """
        # Compute pairwise distances and find indices of agents within
        # contact distance
        dists = scipy.spatial.distance.pdist(positions_vector)
        dist_matrix = scipy.spatial.distance.squareform(dists)
        return np.argwhere(dist_matrix < self.contact_distance)

    def verify_and_add_contact(
        self,
        current_step: int,
        floor_number: int,
        agent1: Agent,
        agent2: Agent,
    ):
        """
        Verify if agents are in nearby hallways before creating contact event.

        :param floor_number: [description]
        :type floor_number: int
        :param agent1: First agent
        :type agent1: Agent
        :param agent2: Second agent
        :type agent2: Agent
        """
        hallways_graph = self.facility.navigation.hallways_graph_per_floor[
            floor_number
        ]
        floorplan = self.facility.floorplans[floor_number]
        space1 = floorplan.spaces[agent1.current_location]
        space2 = floorplan.spaces[agent2.current_location]
        if (
            hallways_graph is None
            or not space1.is_space_a_hallway()
            or not space2.is_space_a_hallway()
        ):
            return
        if hallways_graph.has_edge(space1.unique_name, space2.unique_name):
            self.add_contact_event(current_step, agent1, agent2)

    def add_contact_event(
        self, current_step: int, agent1: Agent, agent2: Agent
    ) -> None:
        """
        Record contact event between agent1 and agent2.

        :param agent1: The first agent.
        :type agent1: Agent
        :param agent2: The second agent.
        :type agent2: Agent
        """

        dx = (agent2.pos[0] - agent1.pos[0]) / 2.0
        dy = (agent2.pos[1] - agent1.pos[1]) / 2.0
        contact_pos = (agent1.pos[0] + dx, agent1.pos[1] + dy)
        agent1.cumulative_properties["contact_duration"] += 1
        agent2.cumulative_properties["contact_duration"] += 1
        self.contact_events.add_contact(
            agent1, agent2, current_step, contact_pos
        )
        if (
            contact_pos
            not in self.step_contact_locations[agent1.current_floor]
        ):
            self.step_contact_locations[agent1.current_floor][contact_pos] = 1
        else:
            self.step_contact_locations[agent1.current_floor][contact_pos] += 1

    def extract_contact_distribution_per_agent(
        self, agents: List[Agent]
    ) -> Tuple[List[str], List[int]]:
        """
        Compute and return total contacts per agent.

        :return: List of agent ids and their total contacts
        :rtype: Tuple[List[int], List[int]]
        """

        agent_ids, n_contacts = [], []
        for unique_id, agent in agents.items():
            agent_ids.append("ID_" + str(unique_id + 1))
            n_contacts.append(agent.cumulative_properties["contact_duration"])

        return agent_ids, n_contacts

    def save_to_files(
        self,
        agents: List[Agent],
        work_directory: Union[str, bytes, os.PathLike],
    ):
        """
        Write output files to the output directory

        :param work_directory: directory where all output files are to be
            saved.
        :type work_directory: str
        """

        # TODO: Don't overwrite existing file

        # Total contacts per agent
        agent_ids, n_contacts = self.extract_contact_distribution_per_agent(
            agents
        )
        filename = os.path.join(work_directory, "contact_dist_per_agent.csv")
        with open(filename, "w") as outfile:
            outfile.write("agent_ID,Number_of_Contacts\n")
            for eid, nc in zip(agent_ids, n_contacts):
                outfile.write(str(eid) + "," + str(nc) + "\n")

        # Pair contacts
        filename = os.path.join(work_directory, "pair_contact.csv")
        self.contact_events.save_pairwise_contacts(filename)

        # Raw contact data
        filename = os.path.join(work_directory, "raw_contact_data.ccd")
        self.contact_events.save_raw_contact_data(filename)

        # Statistics
        statistics = self.contact_events.extract_statistics()
        statistics_dict = {
            "data": statistics,
        }
        filename = os.path.join(work_directory, "statistics.json")
        with open(filename, "w") as json_file:
            json.dump(statistics_dict, json_file)

        # Per-floor outputs
        for floor_number in range(self.facility.number_of_floors):

            # Distribution of contact locations

            floor_directory = os.path.join(
                work_directory, "floor_" + str(floor_number)
            )

            coord_contact_dist_filename = os.path.join(
                floor_directory, "contact_dist_per_coord.csv"
            )

            contacts_per_coord = (
                self.contact_events.get_contacts_per_coordinates(floor_number)
            )

            with open(coord_contact_dist_filename, "a") as outfile:
                outfile.write("x,y,n_contacts\n")
                for pos in contacts_per_coord:
                    x, y = pos
                    dur = contacts_per_coord[pos]
                    outfile.write(
                        str(x) + "," + str(y) + "," + str(dur) + "\n"
                    )

            self.create_svg_heatmap(contacts_per_coord, floor_directory)

    def create_svg_heatmap(
        self,
        contacts_per_coord: Dict[Tuple[int, int], int],
        floor_directory: str,
    ) -> None:
        """
        Create and save a heatmap from coordinate contact data.

        :param contacts_per_coord: dictionary where each key is an (x,y )
                tuple and values are the number of contacts in that location.
        :type contacts_per_coord: Dict[Tuple[int, int], int]
        :param floor_directory: directory to save the heatmap file.
        :type floor_directory: str
        :raises FileNotFoundError: if the floor svg map file is not found.
        """

        heatmap_file = os.path.join(floor_directory, "heatmap.svg")
        map_file = os.path.join(floor_directory, "map.svg")

        if not os.path.isfile(map_file):
            raise FileNotFoundError(map_file)

        max_contacts = 0
        if len(contacts_per_coord.values()) > 0:
            max_contacts = max(contacts_per_coord.values())
        tree = ET.parse(map_file)

        root = tree.getroot()[0]

        filter_elem = ET.Element("filter")
        filter_elem.set("id", "blurMe")
        filter_elem.set("width", str(self.contact_distance * 2))
        filter_elem.set("height", str(self.contact_distance * 2))
        filter_elem.set("x", "-100%")
        filter_elem.set("y", "-100%")

        blur_elem = ET.Element("feGaussianBlur")
        blur_elem.set("in", "SourceGraphic")
        blur_elem.set("stdDeviation", str(self.contact_distance * 0.4))
        blur_elem.set("edgeMode", "duplicate")

        filter_elem.append(blur_elem)
        root.append(filter_elem)
        color_scale = cm.get_cmap("RdYlGn")

        for key, v in contacts_per_coord.items():
            x, y = key
            color = color_scale(1.0 - v * 1.0 / max_contacts)
            new_elem = ET.Element("circle")
            new_elem.set("cx", str(x))
            new_elem.set("cy", str(y))
            new_elem.set("r", str(self.contact_distance))
            new_elem.set("fill", color)
            new_elem.set("fill-opacity", str(0.2))
            new_elem.set("filter", "url(#blurMe)")
            root.append(new_elem)

        tree.write(heatmap_file)
