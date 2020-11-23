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

from typing import Dict, Tuple, List
import numpy as np
import scipy.spatial.distance
from collections import OrderedDict
import json
import os
import logging
import hashlib
import networkx as nx
from matplotlib import cm
from io import TextIOWrapper

from citam.engine.core.agent import Agent
from citam.engine.map.floorplan import Floorplan
from citam.engine.map.door import Door
from citam.engine.facility.navigation import Navigation
from citam.engine.policy.daily_schedule import Schedule
import citam.engine.io.visualization as bv
import citam.engine.core.contacts as cev
from citam.engine.policy.meetings import MeetingPolicy
from citam.engine.constants import DEFAULT_SCHEDULING_RULES
from citam.engine.facility.indoor_facility import Facility

import progressbar as pb

import xml.etree.ElementTree as ET

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

LOG = logging.getLogger(__name__)


class FacilityTransmissionModel:
    def __init__(
        self,
        facility: Facility,
        daylength: int,
        n_agents: int,
        occupancy_rate: float,
        buffer: int,
        timestep: float,
        contact_distance: float,
        shifts: List[Dict],
        meetings_policy_params=None,
        create_meetings=True,
        scheduling_policy=None,
        dry_run=False,
    ) -> None:

        self.facility = facility
        self.daylength = daylength
        self.buffer = buffer
        self.timestep = timestep
        self.contact_distance = contact_distance
        self.n_agents = n_agents
        self.occupancy_rate = occupancy_rate

        self.contact_events = cev.ContactEvents()
        self.current_step = 0
        self.agents = OrderedDict()
        self.shifts = shifts
        self.dry_run = dry_run
        self.simulation_name = None
        self.simid = None
        self.step_contact_locations = [{} for f in facility.floorplans]
        self.create_meetings = create_meetings

        # Handle scheduling rules
        if scheduling_policy is None:
            self.scheduling_rules = DEFAULT_SCHEDULING_RULES
        else:
            self.scheduling_rules = scheduling_policy

        self.meetings_policy_params = meetings_policy_params

    def create_simid(self):
        """Use simulation inputs, scheduling policy, meetings policy,
        navigation policy, floorplan and navigation data to generate a unique
        ID for each simulation.
        """
        # TODO: Add random number seed to sim ID hash data
        m = hashlib.blake2b(digest_size=10)
        data = [
            self.daylength,
            self.n_agents,
            self.occupancy_rate,
            self.buffer,
            self.timestep,
            self.facility.entrances,
            self.facility,
            self.contact_distance,
            self.shifts,
            self.meetings_policy_params,
            self.scheduling_rules,
            self.dry_run,
        ]
        m.update(repr(data).encode("utf-8"))

        for fp in self.facility.floorplans:
            fp_data = [
                fp.scale,
                fp.spaces,
                fp.doors,
                fp.walls,
                fp.aisles,
                fp.minx,
                fp.miny,
                fp.maxx,
                fp.maxy,
                fp.floor_name,
                fp.special_walls,
                fp.traffic_policy,
            ]
            m.update(repr(fp_data).encode("utf-8"))

        for nv, hg in zip(
            self.facility.navigation.navnet_per_floor,
            self.facility.navigation.hallways_graph_per_floor,
        ):
            data = nx.to_edgelist(nv)
            m.update(repr(data).encode("utf-8"))

            data = nx.to_edgelist(hg)
            m.update(repr(data).encode("utf-8"))

        self.simid = m.hexdigest()
        self.simulation_name = self.simid

    def run_serial(self, workdir: str) -> None:
        """Runs an citam simulation serially.

        :param str workdir: directory to save the files for this simulation
        """
        if self.n_agents is not None:
            self.occupancy_rate = round(
                self.n_agents * 1.0 / self.facility.total_offices, 2
            )
            if self.occupancy_rate > 1.0:
                LOG.warn(
                    "Occupancy rate is "
                    + str(self.occupancy_rate)
                    + " > 1.0 (Office spaces: "
                    + str(self.facility.total_offices)
                )
        else:
            if self.occupancy_rate < 0.0 or self.occupancy_rate > 1.0:
                raise ValueError("Invalid occupancy rate (must be > 0 & <=1")
            self.n_agents = round(self.occupancy_rate * self.total_offices)

        LOG.info("Running simulation serially")
        LOG.info("Total agents: " + str(self.n_agents))

        self.create_simid()
        self.save_manifest(workdir)
        self.save_maps(workdir)

        # Create meetings
        agent_ids = list(range(self.n_agents))
        meeting_room_objects = []
        for fn, floor_rooms in enumerate(self.facility.meeting_rooms):
            floor_room_objs = []
            for room_id in floor_rooms:
                room_obj = self.facility.floorplans[fn].spaces[room_id]
                floor_room_objs.append(room_obj)
            meeting_room_objects.append(floor_room_objs)
        self.meeting_policy = MeetingPolicy(
            meeting_room_objects,
            agent_ids,
            daylength=self.daylength,
            policy_params=self.meetings_policy_params,
        )

        n_meeting_rooms = sum(len(rooms) for rooms in meeting_room_objects)
        if n_meeting_rooms > 0 and self.create_meetings:
            self.meeting_policy.create_all_meetings()

        # Create schedule and itinerary for each agent
        self.add_agents_and_build_schedules()

        # open files
        traj_file = workdir + "/trajectory.txt"
        t_outfile = open(traj_file, "w")  # Keep the trajectory file open
        contact_outfiles = []
        for floor_number in range(self.facility.number_of_floors):
            directory = os.path.join(workdir, "floor_" + str(floor_number))
            if not os.path.isdir(directory):
                os.mkdir(directory)
            contact_file = os.path.join(directory, "contacts.txt")
            contact_outfiles.append(open(contact_file, "w"))

        # Run simulation
        pbar = pb.ProgressBar(max_value=self.daylength + self.buffer)
        for i in range(self.daylength + self.buffer):
            pbar.update(i)
            self.step(
                traj_outfile=t_outfile, contact_outfiles=contact_outfiles
            )
            if i % 1000 == 0:
                LOG.info("Current step is: " + str(i))

        LOG.info("Current step is: " + str(self.current_step))

        # Close files
        t_outfile.close()
        for cof in contact_outfiles:
            cof.close()
        LOG.info("Done with simulation.\n")

        return True

    def add_agents_and_build_schedules(self) -> None:
        """
        Add the specified number of agents to the facility and create a
        schedule and an itinerary for each of them.
        """
        LOG.info("Initializing with " + str(self.n_agents) + " agents...")
        total_agents = 0
        current_agent = 0
        agent_pool = list(range(self.n_agents))
        for shift in self.shifts:
            shift_start_time = shift["start_time"] + self.buffer
            n_shift_agents = round(shift["percent_workforce"] * self.n_agents)
            shift_agents = np.random.choice(agent_pool, n_shift_agents)
            agent_pool = [a for a in agent_pool if a not in shift_agents]
            total_agents += n_shift_agents

            LOG.info("Working with shift: " + shift["name"])
            LOG.info("\tNumber of agents: " + str(n_shift_agents))
            LOG.info("\tAverage starting step: " + str(shift_start_time))

            for _ in pb.progressbar(shift_agents):

                entrance_door = None

                while entrance_door is None:

                    office_floor = np.random.randint(
                        self.facility.number_of_floors
                    )
                    n_offices = len(
                        self.facility.all_office_spaces[office_floor]
                    )
                    rint = np.random.randint(n_offices)
                    office_id = self.facility.all_office_spaces[
                        office_floor
                    ].pop(rint)

                    # Choose the closest entrance to office
                    (
                        entrance_door,
                        entrance_floor,
                    ) = self.facility.choose_best_entrance(
                        office_floor, office_id
                    )

                # Sample start time and exit time from a poisson distribution
                start_time = -1
                while start_time < 0 or start_time > 2 * shift_start_time:
                    start_time = round(np.random.poisson(shift_start_time))

                exit_time = 0
                while (
                    exit_time == 0
                    or exit_time > self.daylength + self.buffer
                    or exit_time < self.daylength - self.buffer
                ):

                    exit_time = round(np.random.poisson(self.daylength))

                # Exit through the same door
                exit_door = entrance_door
                exit_floor = entrance_floor

                schedule = Schedule(
                    timestep=self.timestep,
                    start_time=start_time,
                    exit_time=exit_time,
                    entrance_door=entrance_door,
                    entrance_floor=entrance_floor,
                    exit_door=exit_door,
                    exit_floor=exit_floor,
                    office_location=office_id,
                    office_floor=office_floor,
                    navigation=self.facility.navigation,
                    scheduling_rules=self.scheduling_rules,
                )
                agent = Agent(current_agent, schedule)
                self.agents[agent.unique_id] = agent

                schedule.build()
                LOG.info("Schedule for agent: " + str(current_agent))
                LOG.info("\t" + str(schedule))

                current_agent += 1

    def identify_xy_proximity(
        self, positions_vector: np.ndarray
    ) -> np.ndarray:
        """Compute pairwise distances, given a vector of xy positions and
        return the indices of the ones that fall within the given contact
        distance.

        :param list[(x,y)] position_vector: list of current xy positions
            of all active agents
        :return: list of indices of agents that are within the contact
            distance of each other
        :rtype: np.ndarray
        """
        # Compute pairwise distances and find indices of agents within
        # contact distance
        dists = scipy.spatial.distance.pdist(positions_vector)
        dist_matrix = scipy.spatial.distance.squareform(dists)
        return np.argwhere(dist_matrix < self.contact_distance)

    def identify_contacts(self, agents: List[Agent]) -> None:
        """Iterate over agents, compute whether they fall within the contact
        distance or not and verify that they are indeed making contact (based
        on whether they are in the same space or not).

        :param list agents: list of agents under consideration for contact
            statistics
        """
        # Discard contact event if either:
        # 1. agents are in different floors
        # 2. agents are in different spaces but only if the spaces
        #    are not neighbors in the hallway graphs

        if not agents:
            return

        positions_vector = np.array([a.pos for a in agents])
        proximity_indices = self.identify_xy_proximity(positions_vector)

        for i, j in proximity_indices:
            if i < j:  # only consider upper right side of symmetric matrix
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
                        self.add_contact_event(agent1, agent2)

                    else:
                        hallways_graph = (
                            self.facility.navigation.hallways_graph_per_floor[
                                fn
                            ]
                        )
                        if hallways_graph is None:
                            continue
                        floorplan = self.facility.floorplans[fn]
                        space1 = floorplan.spaces[agent1.current_location]
                        space2 = floorplan.spaces[agent2.current_location]
                        if not space1.is_space_a_hallway():
                            continue
                        if not space2.is_space_a_hallway():
                            continue
                        if hallways_graph.has_edge(
                            space1.unique_name, space2.unique_name
                        ):
                            self.add_contact_event(agent1, agent2)

    def add_contact_event(self, agent1: Agent, agent2: Agent) -> None:
        """
        Record contact event between agent1 and agent2.
        """
        dx = (agent2.pos[0] - agent1.pos[0]) / 2.0
        dy = (agent2.pos[1] - agent1.pos[1]) / 2.0
        contact_pos = (agent1.pos[0] + dx, agent1.pos[1] + dy)
        agent1.n_contacts += 1
        agent2.n_contacts += 1
        self.contact_events.add_contact(
            agent1, agent2, self.current_step, contact_pos
        )
        if (
            contact_pos
            not in self.step_contact_locations[agent1.current_floor]
        ):
            self.step_contact_locations[agent1.current_floor][contact_pos] = 1
        else:
            self.step_contact_locations[agent1.current_floor][contact_pos] += 1

        return

    def step(
        self,
        traj_outfile: TextIOWrapper = None,
        contact_outfiles: List[TextIOWrapper] = None,
    ) -> None:
        """Move the simulation by one step"""
        self.step_contact_locations = [
            {}
        ] * self.facility.number_of_floors  # One per floor

        active_agents, moving_agents = self.move_agents()

        if len(moving_agents) > 1 and not self.dry_run:
            # At least 2 agents required
            moving_active_agents = [
                a for a in moving_agents if a.current_location is not None
            ]
            self.identify_contacts(moving_active_agents)

        if traj_outfile is not None:
            traj_outfile.write(
                str(len(active_agents))
                + "\nstep: "
                + str(self.current_step)
                + "\n"
            )
            for agent in active_agents:
                traj_outfile.write(
                    str(agent.unique_id)
                    + "\t"
                    + str(agent.pos[0])
                    + "\t"
                    + str(agent.pos[1])
                    + "\t"
                    + str(agent.current_floor)
                    + "\t"
                    + str(agent.n_contacts)
                    + "\n"
                )

        if contact_outfiles is not None:

            for fn in range(self.facility.number_of_floors):

                n_contact_loc = len(self.step_contact_locations[fn])
                contact_outfiles[fn].write(
                    str(n_contact_loc)
                    + "\nstep :"
                    + str(self.current_step)
                    + "\n"
                )

                for cl, nc in self.step_contact_locations[fn].items():
                    contact_outfiles[fn].write(
                        str(cl[0]) + "\t" + str(cl[1]) + "\t" + str(nc) + "\n"
                    )
        self.current_step += 1

    def move_agents(self) -> Tuple[List[Agent], List[Agent]]:
        """
        Iterate over agents and move them to the next position in their
        itinerary. Active agents are agents currently in the facility and
        moving agents are agents currently moving from one location to the
        next.

        :return list of active and moving agents
        :rtype: (list, list)
        """
        active_agents = []  # All agents currently within the facility

        # TODO: consider contacts for agents that are stationary as well
        moving_agents = []  # All employees that are currently moving

        for unique_id, agent in self.agents.items():
            has_moved = agent.step()

            if agent.pos is not None:
                active_agents.append(agent)
                if has_moved:
                    moving_agents.append(agent)

        return active_agents, moving_agents

    def extract_contact_distribution_per_agent(
        self,
    ) -> Tuple[List[int], List[int]]:
        """
        Compute total contacts per agent.

        :return: List of agent ids and list of corresponding number of
            contacts.
        """
        agent_ids, n_contacts = [], []
        for unique_id, agent in self.agents.items():
            agent_ids.append("ID_" + str(unique_id + 1))
            n_contacts.append(agent.n_contacts)

        return agent_ids, n_contacts

    def save_manifest(self, work_directory: str) -> None:
        """
        Save manifest file, used by the dashboard to show results.

        :param str work_directory: top level directory where all simulation
            outputs are saved.
        """
        floors = [
            {"name": str(floor), "directory": "floor_" + str(floor) + "/"}
            for floor in range(self.facility.number_of_floors)
        ]

        LOG.info("Saving manifest file...")
        # TODO: total over all floors
        if self.facility.traffic_policy is None:
            n_one_way_aisles = 0
        else:
            n_one_way_aisles = len(
                [
                    p
                    for p in self.facility.traffic_policy
                    if p["direction"] != 0
                ]
            )

        fp_width = (
            self.facility.floorplans[0].maxx - self.facility.floorplans[0].minx
        )
        manifest_dict = {
            "TimestepInSec": 1,
            "NumberOfFloors": self.facility.number_of_floors,
            "NumberOfOneWayAisles": n_one_way_aisles,
            "NumberOfEmployees": len(self.agents),
            "SimulationName": self.simulation_name,
            "SimulationID": self.simid,
            "Campus": self.facility.facility_name,
            "FacilityOccupancy": self.occupancy_rate,  # between 0.0 and 1.0
            "MaxRoomOccupancy": 1.0,
            "NumberOfShifts": 1,
            "NumberOfEntrances": 1,
            "NumberOfExits": 1,
            "EntranceScreening": False,
            "trajectory_file": "trajectory.txt",
            "floors": floors,
            "scaleMultiplier": max(1, round(fp_width / 1500.0)),
            "timestep": 1,
        }

        manifest_file = os.path.join(work_directory, "manifest.json")
        with open(manifest_file, "w") as json_file:
            json.dump(manifest_dict, json_file, indent=4)

    def save_maps(self, work_directory: str) -> None:
        """Save svg maps for each floor for visualization. Each floor map is
            saved in a separate subdirectory (created if not found).

        :param str work_directory: top level directory where all simulation
            outputs are saved.
        """
        for floor_number in range(self.facility.number_of_floors):

            floor_directory = os.path.join(
                work_directory, "floor_" + str(floor_number)
            )
            if not os.path.isdir(floor_directory):
                os.mkdir(floor_directory)

            # Map svg file for the entire facility
            svg_file = os.path.join(floor_directory, "map.svg")
            bv.export_world_to_svg(
                self.facility.floorplans[floor_number].walls,
                [],
                svg_file,
                marker_locations=[],
                marker_type=None,
                arrows=[],
                max_contacts=100,
                current_time=None,
                show_colobar=False,
                viewbox=[
                    self.facility.floorplans[floor_number].minx - 50,
                    self.facility.floorplans[floor_number].miny - 50,
                    self.facility.floorplans[floor_number].maxx + 50,
                    self.facility.floorplans[floor_number].maxy + 50,
                ],
            )

    def create_svg_heatmap(
        self,
        contacts_per_coord: Dict[Tuple[int, int], int],
        floor_directory: str,
    ) -> None:
        """Create and save a heatmap from coordinate contact data

        :param dict contacts_per_coord: dictionary where each key is an (x,y )
            tuple and values are the number of contacts in that location.
        :param str floor_directory: directory to save the heatmap file.
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

    def save_outputs(self, work_directory: str) -> None:
        """Write output files to the output directory

        :param str work_directory: directory where all output files are to be
            saved.
        """
        # TODO: generate time-dependent cumulative contacts per coordinate

        # Total contacts per agent
        agent_ids, n_contacts = self.extract_contact_distribution_per_agent()
        filename = os.path.join(work_directory, "contact_dist_per_agent.csv")
        with open(filename, "w") as outfile:
            outfile.write("agent_ID,Number_of_Contacts\n")
            for eid, nc in zip(agent_ids, n_contacts):
                outfile.write(str(eid) + "," + str(nc) + "\n")

        # agent ids
        filename = os.path.join(work_directory, "agent_ids.txt")
        with open(filename, "w") as outfile:
            for unique_id, agent in self.agents.items():
                outfile.write(str(unique_id + 1) + "\n")

        # Pair contacts
        filename = os.path.join(work_directory, "pair_contact.csv")
        self.contact_events.save_pairwise_contacts(filename)

        # Raw contact data
        filename = os.path.join(work_directory, "raw_contact_data.ccd")
        self.contact_events.save_raw_contact_data(filename)

        # Statistics
        statistics = self.contact_events.extract_statistics()
        statistics_dict = {
            "SimulationName": self.simulation_name,
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
                self.contact_events.get_contacts_per_coordinates(
                    self.current_step, floor_number
                )
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