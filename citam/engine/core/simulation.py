#  Copyright 2021. Corning Incorporated. All rights reserved.
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

from typing import Dict, Tuple, List, TextIO, Optional, Union
from collections import OrderedDict
import json
import os
import logging
import hashlib
import uuid
import xml.etree.ElementTree as ET

import networkx as nx
import progressbar as pb

from citam.engine.calculators.calculator import Calculator
from citam.engine.calculators.close_contacts_calculator import (
    CloseContactsCalculator,
)
from citam.engine.core.agent import Agent
from citam.engine.schedulers.office_scheduler import OfficeScheduler
from citam.engine.schedulers.schedule import Schedule
import citam.engine.io.visualization as bv

from citam.engine.constants import (
    DEFAULT_MEETINGS_POLICY,
    DEFAULT_SCHEDULING_RULES,
    CAFETERIA_VISIT,
)
from citam.engine.facility.indoor_facility import Facility
from citam.engine.schedulers.scheduler import Scheduler

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

LOG = logging.getLogger(__name__)


class Simulation:
    """
    Implements a CITAM indoor Agent-Based Modeling simulation.

    Given a facility and simulation inputs, this implements routines to
    initialize the agents and their scheduels, run a simulation and output
    results to file.
    """

    def __init__(
        self,
        facility: Facility,
        total_timesteps: int,
        n_agents: int,
        calculators: Optional[List[Calculator]] = None,
        scheduler: Optional[Scheduler] = None,
        dry_run=False,
    ) -> None:
        """
        Initialize a new simulation object.

        :param facility: Facility object for which to run this simulation.
        :type facility: Facility
        :param total_timesteps: Total timesteps to run this simulation for.
        :type total_timesteps: int
        :param n_agents: Total number of people in this facility.
        :type n_agents: int
        :param shifts: A shift is a group of agents who
                enter the facility at relatively the same time (Note: exit time
                is not included). A shift is defined by a name, an entrance
                 time, a percentage of agents.
        :type shifts: List[Dict]
        :param buffer: Number of timesteps at the beginning and ending of the
                day when agents enter and exit the facility.
        :type buffer: int
        :param occupancy_rate: how many office spaces are occupied. Note:
                'n_agents' supersedes 'occupancy_rate' when specified, in which
                case occupancy_rate can be None. defaults to None
        :type occupancy_rate: float, optional
        :param timestep: How long does one timestep corresponds to in seconds,
                 defaults to 1.0
        :type timestep: float, optional
        :param contact_distance: Maximum between two agents for a contact to be
                registered, defaults to 6.0
        :type contact_distance: float, optional
        :param meetings_policy_params: Parameters defining a meeting policy,
                 defaults to None
        :type meetings_policy_params: dict, optional
        :param create_meetings: Whether meetings are allowed or not,
                 defaults to True
        :type create_meetings: bool, optional
        :param close_dining: Wheter cafeterias are open or not,
                defaults to False
        :type close_dining: bool, optional
        :param scheduling_policy: Policy defining how daily schedules are
                created, defaults to None
        :type scheduling_policy: dict, optional
        :param dry_run: If true, generate itineraries but do not compute
                contact statistics, defaults to False
        :type dry_run: bool, optional
        """

        self.facility = facility
        self.total_timesteps = total_timesteps
        # self.buffer = buffer
        # self.timestep = timestep
        self.n_agents = n_agents
        # self.occupancy_rate = occupancy_rate
        # self.preassigned_offices = preassigned_offices

        if calculators is None:
            LOG.info(
                "No calculator provided. Defaulting to close contacts calculator."
            )
            self.calculators = [CloseContactsCalculator(facility)]
        elif isinstance(calculators, Calculator):
            self.calculators = [calculators]
        elif isinstance(calculators, list):
            for calc in calculators:
                if not isinstance(calc, Calculator):
                    raise ValueError(
                        "Invalid calculator. Must be an instance of Calculator."
                    )
            self.calculators = calculators
        else:
            raise ValueError(
                "Invalid calculator. Must be an instance of Calculator"
            )
        if scheduler is None:
            LOG.info("No scheduler provided. Defaulting to office scheduler.")
            self.scheduler = OfficeScheduler(facility, total_timesteps)
        elif not isinstance(scheduler, Scheduler):
            raise ValueError(
                "Invalid scheduler. Must be an instance of Scheduler"
            )
        else:
            self.scheduler = scheduler

        self.current_step = 0
        self.agents = OrderedDict()
        # self.shifts = shifts
        self.dry_run = dry_run
        self.simulation_hash = None
        self.run_id = str(uuid.uuid4())

        # self.create_meetings = create_meetings

        # Handle scheduling rules
        # if scheduling_policy is None:
        #     self.scheduling_rules = DEFAULT_SCHEDULING_RULES
        # else:
        #     self.scheduling_rules = scheduling_policy

        # if close_dining and CAFETERIA_VISIT in self.scheduling_rules:
        #     del self.scheduling_rules[CAFETERIA_VISIT]

        # self.meetings_policy_params = meetings_policy_params

    def create_sim_hash(self):
        """
        Hash simulation inputs, scheduling policy, meetings policy,
        navigation policy, floorplan and navigation data to generate a unique
        ID for each simulation.
        """

        m = hashlib.blake2b(digest_size=10)
        data = [
            self.total_timesteps,
            self.n_agents,
            # self.occupancy_rate,
            # self.buffer,
            # self.timestep,
            self.facility.entrances,
            self.facility,
            # self.shifts,
            # self.meetings_policy_params,
            # self.scheduling_rules,
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

        self.simulation_hash = m.hexdigest()

    def run_serial(
        self,
        workdir: Union[str, os.PathLike, bytes],
        sim_name: str,
        run_name: str,
    ) -> None:
        """
        Run a CITAM simulation serially (i.e. only one core will be used).

        The serial runner is understandably slow because at each timestep,
        contacts have to be computed while taking into account the specific
        layout of the facility. A parallel version that computes contacts
        for timestep blocks is desirable.

        :param workdir: The directory where all results are to saved.
        :type workdir: str
        :raises ValueError: If occupancy rate is not between 0.0 and 1.0
        """

        # Load pre-assigned offices as needed
        self.create_sim_hash()
        self.save_manifest(workdir, sim_name, run_name)
        self.save_maps(workdir)
        self.create_agents()
        self.save_schedules(workdir)

        # Initialize calculators
        for calculator in self.calculators:
            calculator.initialize(self.agents, workdir)

        LOG.info(f"Running simulation serially with {self.n_agents} agents")
        self.run_simulation_and_save_results(workdir)

    def run_simulation_and_save_results(
        self, workdir: Union[str, bytes, os.PathLike]
    ) -> None:
        """
        Perform simulation and save results to files.

        :param workdir: path where results are saved.
        :type workdir: str
        """
        # open files
        traj_file = workdir + "/trajectory.txt"
        t_outfile = open(traj_file, "w")  # Keep the trajectory file open

        # Run simulation
        pbar = pb.ProgressBar(max_value=self.total_timesteps)
        for i in range(self.total_timesteps):
            pbar.update(i)
            self.step(traj_outfile=t_outfile)
            if i % 1000 == 0:
                LOG.info("Current step is: " + str(i))

        LOG.info(f"Done with all {self.current_step} steps.")

        # Close files
        t_outfile.close()
        for calc in self.calculators:
            calc.finalize(self.agents, work_directory=workdir)
        LOG.info("Done with simulation.\n")

    def create_agents(self) -> List[Schedule]:
        """
        Generate a list of schedules, one per agent.

        :raises ValueError: If an entrance could not be found

        """
        LOG.info(f"Generating schedules for {self.n_agents} agents...")
        current_agent = 0
        schedules = self.scheduler.run(self.n_agents)
        for current_agent, schedule in enumerate(schedules):
            agent = Agent(current_agent, schedule)
            self.agents[agent.unique_id] = agent

    def step(
        self,
        traj_outfile: TextIO = None,
    ) -> None:
        """
        Move the simulation one step ahead.

        At each step, agents are advanced one step ahead in their itineraries
        and contact statistics are computed.

        :param traj_outfile: File to write trajectory data, defaults to None
        :type traj_outfile: TextIO, optional

        """

        active_agents, _ = self.move_agents()
        if not self.dry_run:
            # if dry_run is True, don't run the calculator.
            for calculator in self.calculators:
                calculator.run(self.current_step, active_agents)

        if traj_outfile is not None:
            traj_outfile.write(
                str(len(active_agents))
                + "\nstep: "
                + str(self.current_step)
                + "\n"
            )
            for agent in active_agents:
                agent_data = (
                    str(agent.unique_id)
                    + "\t"
                    + str(agent.pos[0])
                    + "\t"
                    + str(agent.pos[1])
                    + "\t"
                    + str(agent.current_floor)
                )
                for ip in agent.instantaneous_properties.values():
                    agent_data += "\t" + str(ip[-1])
                for cp in agent.cumulative_properties.values():
                    agent_data += "\t" + str(cp)
                agent_data += "\n"
                traj_outfile.write(agent_data)

        self.current_step += 1

    def move_agents(self) -> Tuple[List[Agent], List[Agent]]:
        """
        Iterate over agents and move them to the next position in their
        itinerary. Active agents are agents currently in the facility and
        moving agents are agents currently moving from one location to the
        next.

        :return: list of active and moving agents
        :rtype: Tuple[List[Agent], List[Agent]]
        """

        active_agents = []  # All agents currently within the facility

        # TODO: consider contacts for agents that are stationary as well
        moving_agents = []  # All employees that are currently moving

        for _, agent in self.agents.items():
            has_moved = agent.step()
            if agent.pos is not None:
                active_agents.append(agent)
                if has_moved:
                    moving_agents.append(agent)

        return active_agents, moving_agents

    def save_manifest(
        self, work_directory: str, sim_name: str, run_name: str
    ) -> None:
        """
        Save manifest file, used by the dashboard to show results.

        :param work_directory:  top level directory where all simulation
            outputs are saved.
        :type work_directory: str
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
            "NumberOfAgents": self.n_agents,
            "SimulationName": sim_name,
            "RunName": run_name,
            "SimulationHash": self.simulation_hash,
            "RunID": self.run_id,
            "FacilityName": self.facility.facility_name,
            # "FacilityOccupancy": self.occupancy_rate,  # between 0.0 and 1.0
            "MaxRoomOccupancy": 1.0,
            "NumberOfShifts": 1,
            "NumberOfEntrances": 1,
            "NumberOfExits": 1,
            "EntranceScreening": False,
            "TrajectoryFile": "trajectory.txt",
            "Floors": floors,
            "ScaleMultiplier": max(1, round(fp_width / 1500.0)),
            "Timestep": 1,
            "TotalTimesteps": self.total_timesteps,
        }

        manifest_file = os.path.join(work_directory, "manifest.json")
        with open(manifest_file, "w") as json_file:
            json.dump(manifest_dict, json_file, indent=4)

    def save_maps(self, work_directory: str) -> None:
        """
        Save svg maps for each floor for visualization. Each floor map is
        saved in a separate subdirectory (created if not found).

        :param work_directory: top level directory where all simulation
                outputs are saved.
        :type work_directory: str
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

    def save_schedules(
        self,
        work_directory: str,
    ) -> None:
        """
        Write agent schedules to file.

        :param work_directory: directory where output files are to be saved.
        :type work_directory: str
        :param scheduler: Scheduler agent used in this simulation.
        :type scheduler: Scheduler
        """

        # agent ids and
        self.scheduler.save_to_files(work_directory)

        # Full schedules of all agents
        with open(
            os.path.join(work_directory, "schedules.txt"), "w"
        ) as outfile:
            for unique_id, agent in self.agents.items():
                outfile.write(
                    "Agent ID: "
                    + str(unique_id)
                    + str(agent.schedule)
                    + "\n\n"
                )
