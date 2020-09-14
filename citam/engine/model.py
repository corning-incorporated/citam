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

import numpy as np
import scipy.spatial.distance
from collections import OrderedDict
import json
import os
import logging
import hashlib
import networkx as nx
from matplotlib import cm

from citam.engine.agent import Agent
from citam.engine.navigation import Navigation
from citam.engine.daily_schedule import Schedule
import citam.engine.basic_visualization as bv
import citam.engine.contact_events as cev
from citam.engine.meeting_policy import MeetingPolicy
from citam.engine.constants import DEFAULT_SCHEDULING_RULES

import progressbar as pb

import xml.etree.ElementTree as ET
ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")


class FacilityTransmissionModel:

    def __init__(self,
                 floorplans,
                 daylength,
                 n_agents,
                 occupancy_rate,
                 buffer,
                 timestep,
                 entrances,
                 facility_name,
                 contact_distance,
                 shifts,
                 meetings_policy_params=None,
                 scheduling_policy=None,
                 traffic_policy=None,
                 dry_run=False
                 ):

        self.floorplans = floorplans
        self.daylength = daylength
        self.buffer = buffer
        self.entrances = entrances
        self.timestep = timestep
        self.contact_distance = contact_distance
        self.n_agents = n_agents
        self.occupancy_rate = occupancy_rate

        self.contact_events = cev.ContactEvents()
        self.current_step = 0
        self.agents = OrderedDict()
        self.facility_name = facility_name
        self.number_of_floors = len(floorplans)
        self.shifts = shifts
        self.dry_run = dry_run
        self.traffic_policy = traffic_policy

        # Handle scheduling rules
        if scheduling_policy is None:
            self.scheduling_rules = DEFAULT_SCHEDULING_RULES
        else:
            self.scheduling_rules = scheduling_policy

        self.meetings_policy_params = meetings_policy_params

        # Initialize navigation network
        self.navigation = Navigation(self.floorplans,
                                     self.facility_name,
                                     self.traffic_policy)

        # remove spaces that have no exit from the pool
        self.remove_unreachable_rooms()

        # Find all entrances to this facility
        for entrance in self.entrances:
            ename = entrance['name'].lower()
            efloor = entrance['floor']
            fp_index = None
            for i, fp in enumerate(self.floorplans):
                if fp.floor_name == efloor:
                    fp_index = i
                    entrance['floor_index'] = fp_index
                    break
            if fp_index is None:
                logging.error('Unknown entrance floor: ' + str(efloor))
                raise ValueError()
            for i, space in enumerate(self.floorplans[fp_index].spaces):
                if space.unique_name == ename:
                    entrance['space_index'] = i
                    break

        logging.info('Entrances: ' + str(self.entrances))

        # Find all office spaces in this facility
        self.total_offices = 0
        self.all_office_spaces = []
        for fn in range(self.number_of_floors):
            floor_office_spaces = self.find_floor_office_spaces(fn)
            self.all_office_spaces.append(floor_office_spaces)
            self.total_offices += len(floor_office_spaces)

        logging.info('Total office spaces is ' + str(self.total_offices))

        self.meeting_rooms, self.labs, self.cafes, self.restrooms,\
            self.offices = [], [], [], [], []  # List of list of space indices

        for fp in self.navigation.floorplans:
            floor_offices, floor_labs, floor_cafes, floor_restrooms,\
                floor_meeting_rooms = [], [], [], [], []

            for index, space in enumerate(fp.spaces):

                if space.is_space_an_office():
                    floor_offices.append(index)

                elif space.is_space_a_lab():
                    floor_labs.append(index)

                elif space.is_space_a_cafeteria():
                    floor_cafes.append(index)

                elif space.is_space_a_restroom():
                    floor_restrooms.append(index)

                elif space.is_space_a_meeting_room():
                    floor_meeting_rooms.append(index)

            self.labs.append(floor_labs)
            self.cafes.append(floor_cafes)
            self.restrooms.append(floor_restrooms)
            self.meeting_rooms.append(floor_meeting_rooms)

        n_rooms = sum([len(rooms) for rooms in self.labs])
        logging.info('Total labs is ' + str(n_rooms))

        n_rooms = sum([len(rooms) for rooms in self.cafes])
        logging.info('Total cafeterias: ' + str(n_rooms))

        n_rooms = sum([len(rooms) for rooms in self.restrooms])
        logging.info('Total restrooms: ' + str(n_rooms))

        n_rooms = sum([len(rooms) for rooms in self.meeting_rooms])
        logging.info('Total meeting rooms: ' + str(n_rooms))

        return

    def find_floor_office_spaces(self, floor_number, verify_route=False):
        """Go through office spaces and verify that they are reachable from
        at least one of the predefined entrances.
        """
        # Find all office spaces on this floor
        floorplan = self.floorplans[floor_number]
        floor_office_spaces = []
        n_unreachable_offices = 0

        pbar = pb.ProgressBar(max_value=len(floorplan.spaces))
        for index, space in enumerate(floorplan.spaces):
            pbar.update(index)
            if space.is_space_an_office():
                if verify_route:
                    best_entrance, _ = \
                        self.choose_best_entrance(floor_number, index)
                    if best_entrance is not None:
                        floor_office_spaces.append(index)
                    else:
                        n_unreachable_offices += 1
                else:
                    floor_office_spaces.append(index)

        logging.info('Unreachable offices: ' + str(n_unreachable_offices))

        return floor_office_spaces

    def create_simid(self):
        """Use simulation inputs, scheduling policy, meetings policy,
        navigation policy, floorplan and navigation data to generate a unique
        ID for each simulation.
        """
        # TODO: Add random number seed to sim ID hash data
        m = hashlib.blake2b(digest_size=10)
        data = [self.daylength,
                self.n_agents,
                self.occupancy_rate,
                self.buffer,
                self.timestep,
                self.entrances,
                self.facility_name,
                self.contact_distance,
                self.shifts,
                self.meetings_policy_params,
                self.scheduling_rules,
                self.dry_run
                ]
        m.update(repr(data).encode('utf-8'))

        for fp in self.floorplans:
            fp_data = [fp.scale,
                       fp.spaces,
                       fp.doors,
                       fp.walls,
                       fp.aisles,
                       fp.width,
                       fp.height,
                       fp.floor_name,
                       fp.special_walls,
                       fp.traffic_policy
                       ]
            m.update(repr(fp_data).encode('utf-8'))

        for nv, hg in zip(self.navigation.navnet_per_floor,
                          self.navigation.hallways_graph_per_floor
                          ):
            data = nx.to_edgelist(nv)
            m.update(repr(data).encode('utf-8'))

            data = nx.to_edgelist(hg)
            m.update(repr(data).encode('utf-8'))

        self.simid = m.hexdigest()

    def run_serial(self, sim_name, workdir):
        """Runs an citam simulation serially.

        :param str sim_name: user-defined name of this simulation
        :param str workdir: directory to save the files for this simulation
        """

        self.simulation_name = sim_name

        if self.n_agents is not None:
            self.occupancy_rate = \
                round(self.n_agents*1.0/self.total_offices, 2)
            if self.occupancy_rate > 1.0:
                logging.warn(
                    'Occupancy rate is ' + str(self.occupancy_rate) +
                    ' > 1.0 (Office spaces: ' + str(self.total_offices)
                    )
        else:
            if self.occupancy_rate < 0.0 or self.occupancy_rate > 1.0:
                raise ValueError( 'Invalid occupancy rate (must be > 0 & <=1')
            self.n_agents = round(self.occupancy_rate*self.total_offices)

        logging.info('Running simulation serially')
        logging.info('Total agents: ' + str(self.n_agents))

        self.create_simid()
        self.save_manifest(workdir)
        self.save_maps(workdir)

        # Create meetings
        agent_ids = list(range(self.n_agents))
        meeting_room_objects = []
        for fn, floor_rooms in enumerate(self.meeting_rooms):
            floor_room_objs = []
            for room_id in floor_rooms:
                room_obj = self.navigation.floorplans[fn].spaces[room_id]
                floor_room_objs.append(room_obj)
            meeting_room_objects.append(floor_room_objs)
        self.meeting_policy = MeetingPolicy(
                                    meeting_room_objects,
                                    agent_ids,
                                    policy_params=self.meetings_policy_params
                                )
        self.meeting_policy.create_meetings()

        # Create schedule and itinerary for each agent
        self.add_agents_and_build_schedules()

        # open files
        traj_file = workdir + '/trajectory.txt'
        t_outfile = open(traj_file, 'w')  # Keep the trajectory file open
        contact_outfiles = []
        for floor_number in range(self.number_of_floors):
            directory = os.path.join(workdir, 'floor_' + str(floor_number))
            if not os.path.isdir(directory):
                os.mkdir(directory)
            contact_file = os.path.join(directory, 'contacts.txt')
            contact_outfiles.append(open(contact_file, 'w'))

        # Run simulation
        pbar = pb.ProgressBar(max_value=self.daylength + self.buffer)
        for i in range(self.daylength + self.buffer):
            pbar.update(i)
            self.step(traj_outfile=t_outfile,
                      contact_outfiles=contact_outfiles
                      )
            if i % 1000 == 0:
                logging.info('Current step is: ' + str(i))

        logging.info('Current step is: ' + str(self.current_step))

        # Close files
        t_outfile.close()
        for cof in contact_outfiles:
            cof.close()
        logging.info('Done with simulation.\n')

        return True

    def remove_unreachable_rooms(self):
        """
        Iterate through every space that is not a hallway in every floor
        and exclude the ones with no door.
        """
        total_spaces = sum([len(fp.spaces) for fp in self.floorplans])
        logging.info('Number of spaces before ' + str(total_spaces) + '...')

        n_hallways = 0
        n_rooms_with_doors = 0
        n_rooms_with_no_doors = 0
        n_rooms_with_doors_but_no_exit = 0

        for fn, floorplan in enumerate(self.floorplans):
            tmp_spaces = []
            for i, space in enumerate(floorplan.spaces):
                if space.is_space_a_hallway():
                    tmp_spaces.append(space)
                    n_hallways += 1
                elif len(space.doors) > 0:
                    n_rooms_with_doors += 1
                    exit_coords = floorplan.get_room_exit_coords(i)
                    if exit_coords is not None:
                        tmp_spaces.append(space)
                    else:
                        n_rooms_with_doors_but_no_exit += 1
                else:
                    n_rooms_with_no_doors += 1

            self.floorplans[fn].spaces = tmp_spaces

        logging.info('After sanitizing...')
        logging.info('\tNumber of hallways: ' + str(n_hallways))
        logging.info('\tRooms with doors: ' + str(n_rooms_with_doors))
        logging.info('\tRooms with no doors: ' + str(n_rooms_with_no_doors))

        total_spaces = sum([len(fp.spaces) for fp in self.floorplans])
        logging.info('\tNumber of spaces: ' + str(total_spaces))

    def find_possible_entrance_doors(self, entrance_floor, entrance_space):
        """
        Iterate over all doors in the facility to identify any that belong to
        the entrance floor and entrance spaceand are outside facing.
        """
        possible_entrance_doors = []
        for door in self.navigation.floorplans[entrance_floor].doors:
            if door.space1 is not None and door.space2 is not None:
                # The door has to lead to outside of the facility
                continue
            if door.space1 is not None:
                if door.space1.unique_name == entrance_space.unique_name:
                    possible_entrance_doors.append(door)
            elif door.space2 is not None:
                if door.space2.unique_name == entrance_space.unique_name:
                    possible_entrance_doors.append(door)

        return possible_entrance_doors

    def validate_entrances(self):
        """
        Iterate over possible entrances and verify that there is indeed
        an outside facing door and that the door is present in the navnet.
        """
        for entrance in self.entrances:
            # chosen_entrance = np.random.choice(self.entrances)
            entrance_floor = entrance['floor_index']
            entrance_room_id = entrance['space_index']
            entrance_space = self.navigation.floorplans[entrance_floor]\
                                            .spaces[entrance_room_id]

            possible_entrance_doors = self.find_possible_entrance_doors(
                                        entrance_floor,
                                        entrance_space
                                    )
            if len(possible_entrance_doors) == 0:
                raise ValueError('This entrance does not have any doors')

            entrance_door = np.random.choice(possible_entrance_doors)

            door_mid_point = entrance_door.path.point(0.5)
            entrance_coords = (round(door_mid_point.real),
                               round(door_mid_point.imag)
                               )

            if self.navigation.navnet_per_floor[entrance_floor]\
                    .has_node(entrance_coords):
                edges = self.navigation.navnet_per_floor[entrance_floor]\
                        .edges(entrance_coords)
                if len(edges) == 0:
                    logging.info('Possible doors are:')
                    for d in possible_entrance_doors:
                        logging.info('\t' + str(d))
                    raise ValueError('Cannot use this entrance %s',
                                     entrance_door)
            else:
                logging.info('Entrance coords: ' + str(entrance_coords))
                logging.info('Entrance floor is: ' + str(entrance_floor))
                logging.info(str(entrance_door))
                logging.info('Possible doors aree:')
                for d in possible_entrance_doors:
                    logging.info('\t' + str(d))
                raise ValueError('Entrance coords not found in graph.')

    def choose_best_entrance(self, office_floor, office_id):
        """
        Find the facility entrance that offers the fastest route to an agent's
        assigned office space.

        :param int offcie_floor: index of the floor where this office is
            located
        :param int office_id: index of the office space
        :return: best_entrance_door, best_entrance_floor
        :rtype: (dict, int)
        """
        best_entrance_door = None
        best_entrance_floor = None
        min_length = 1e10

        for entrance in self.entrances:
            # chosen_entrance = np.random.choice(self.entrances)
            entrance_floor = entrance['floor_index']
            entrance_room_id = entrance['space_index']
            entrance_space = self.navigation.floorplans[entrance_floor]\
                                            .spaces[entrance_room_id]

            possible_entrance_doors = self.find_possible_entrance_doors(
                                        entrance_floor,
                                        entrance_space
                                    )

            entrance_door = np.random.choice(possible_entrance_doors)
            door_mid_point = entrance_door.path.point(0.5)
            entrance_coords = (round(door_mid_point.real),
                               round(door_mid_point.imag)
                               )
            route = self.navigation.get_route(entrance_coords,
                                              entrance_floor,
                                              office_id,
                                              office_floor,
                                              1.0
                                              )
            if route is not None:
                if len(route) < min_length:
                    min_length = len(route)
                    best_entrance_door = entrance_door
                    best_entrance_floor = entrance_floor

        if best_entrance_door is None:
            office = self.floorplans[office_floor].spaces[office_id]
            logging.info('\tNo entrance found for office: ' +
                         office.unique_name
                         )
        return best_entrance_door, best_entrance_floor

    def add_agents_and_build_schedules(self):
        """
        Add the specified number of agents to the facility and create a
        schedule and an itinerary for each of them.
        """
        logging.info('Initializing with ' + str(self.n_agents) + ' agents...')
        total_agents = 0
        current_agent = 0
        agent_pool = list(range(self.n_agents))
        for shift in self.shifts:
            print('Building shift ', shift['name'])
            shift_start_time = shift['start_time'] + self.buffer
            n_shift_agents = round(shift['percent_workforce']*self.n_agents)
            shift_agents = np.random.choice(agent_pool, n_shift_agents)
            agent_pool = [a for a in agent_pool if a not in shift_agents]
            total_agents += n_shift_agents

            logging.info('Working with shift: ' + shift['name'])
            logging.info('\tNumber of agents: ' + str(n_shift_agents))
            logging.info('\tAverage starting step: ' + str(shift_start_time))

            for i in pb.progressbar(shift_agents):

                entrance_door = None

                while entrance_door is None:

                    office_floor = np.random.randint(self.number_of_floors)
                    n_offices = len(self.all_office_spaces[office_floor])
                    rint = np.random.randint(n_offices)
                    office_id = self.all_office_spaces[office_floor].pop(rint)

                    # Choose the closest entrance to office
                    entrance_door, entrance_floor = \
                        self.choose_best_entrance(office_floor, office_id)

                if len(self.all_office_spaces[office_floor]) == 0:
                    # Reinitialize office spaces.
                    # People will be 2 per office now
                    # TODO: Use office capacity instead
                    floor_offices = self.find_floor_office_spaces(office_floor)
                    self.all_office_spaces[office_floor] = floor_offices

                # Sample start time and exit time from a poisson distribution
                start_time = -1
                while start_time < 0 or start_time > 2*shift_start_time:
                    start_time = round(np.random.poisson(shift_start_time))

                exit_time = 0
                while exit_time == 0 or \
                        exit_time > self.daylength + self.buffer or \
                        exit_time < self.daylength - self.buffer:

                    exit_time = round(np.random.poisson(self.daylength))

                # Exit through the same door
                exit_door = entrance_door
                exit_floor = entrance_floor

                schedule = Schedule(timestep=self.timestep,
                                    start_time=start_time,
                                    exit_time=exit_time,
                                    entrance_door=entrance_door,
                                    entrance_floor=entrance_floor,
                                    exit_door=exit_door,
                                    exit_floor=exit_floor,
                                    office_location=office_id,
                                    office_floor=office_floor,
                                    navigation=self.navigation,
                                    scheduling_rules=self.scheduling_rules
                                    )
                agent = Agent(current_agent, schedule)
                self.agents[agent.unique_id] = agent

                schedule.build()
                logging.info('Schedule for agent: ' + str(current_agent))
                logging.info('\t' + str(schedule))
                logging.info('\n')

                current_agent += 1

    def identify_xy_proximity(self, positions_vector):
        """Compute pairwise distances, given a vector of xy positions and
        return the indices of the ones that fall within the given contact
        distance.

        :param list[(x,y)] position_vector: list of current xy positions
            of all active agents
        :return: list of indices of agents that are within the contact
            distance of each other
        :rtype: list[int]
        """
        # Compute pairwise distances and find indices of agents within
        # contact distance
        dists = scipy.spatial.distance.pdist(positions_vector)
        dist_matrix = scipy.spatial.distance.squareform(dists)
        indices = np.argwhere(dist_matrix < self.contact_distance)

        return indices

    def identify_contacts(self, agents):
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

        positions_vector = np.array([a.pos for a in agents])
        proximity_indices = self.identify_xy_proximity(positions_vector)

        for i, j in proximity_indices:
            if i < j:  # only consider upper right side of symmetric matrix
                agent1 = agents[i]
                agent2 = agents[j]

                if agent1.current_floor == agent2.current_floor:
                    fn = agent1.current_floor
                    if agent1.current_location == agent2.current_location:
                        self.add_contact_event(agent1, agent2)

                    else:
                        hallways_graph = \
                            self.navigation.hallways_graph_per_floor[fn]
                        if hallways_graph is None:
                            continue
                        floorplan = self.navigation.floorplans[fn]
                        space1 = floorplan.spaces[agent1.current_location]
                        space2 = floorplan.spaces[agent2.current_location]
                        if not space1.is_space_a_hallway():
                            continue
                        if not space2.is_space_a_hallway():
                            continue
                        if hallways_graph.has_edge(space1.unique_name,
                                                   space2.unique_name
                                                   ):
                            self.add_contact_event(agent1, agent2)

    def add_contact_event(self, agent1, agent2):
        """
        Record contact event between agent1 and agent2.
        """
        dx = (agent2.pos[0] - agent1.pos[0])/2.0
        dy = (agent2.pos[1] - agent1.pos[1])/2.0
        contact_position = (agent1.pos[0] + dx, agent1.pos[1] + dy)
        agent1.n_contacts += 1
        agent2.n_contacts += 1
        self.contact_events.add_contact(agent1,
                                        agent2,
                                        self.current_step,
                                        contact_position)
        if agent1.pos not in self.step_contact_locations[agent1.current_floor]:
            self.step_contact_locations[agent1.current_floor][agent1.pos] = 1
        else:
            self.step_contact_locations[agent1.current_floor][agent1.pos] += 1

        return

    def step(self, traj_outfile=None, contact_outfiles=None):
        """Move the simulation by one step
        """
        self.step_contact_locations = []
        for floor in range(self.number_of_floors):  # One per floor
            self.step_contact_locations.append({})

        active_agents, moving_agents = self.move_agents()

        if len(moving_agents) > 1 and not self.dry_run:
            # At least 2 agents required
            moving_active_agents = []
            for a in moving_agents:
                if a.current_location is not None:
                    moving_active_agents.append(a)
            self.identify_contacts(moving_active_agents)

        if traj_outfile is not None:
            traj_outfile.write(
                str(len(active_agents)) + '\nstep: ' +
                str(self.current_step)+'\n'
            )
            for agent in active_agents:
                traj_outfile.write(
                    str(agent.unique_id) + '\t' +
                    str(agent.pos[0]) + '\t' +
                    str(agent.pos[1]) + '\t' +
                    str(agent.current_floor) + '\t' +
                    str(agent.n_contacts) + '\n'
                )

        if contact_outfiles is not None:

            for fn in range(self.number_of_floors):

                n_contact_loc = len(self.step_contact_locations[fn])
                contact_outfiles[fn].write(
                    str(n_contact_loc) +
                    '\nstep :' + str(self.current_step) + '\n'
                )

                for cl, nc in self.step_contact_locations[fn].items():
                    contact_outfiles[fn].write(
                                str(cl[0]) + '\t' +
                                str(cl[1]) + '\t' +
                                str(nc) + '\n'
                            )
        self.current_step += 1

    def move_agents(self):
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

    def extract_contact_distribution_per_agent(self):
        """
        Compute total contacts per agent.
        """
        agent_ids, n_contacts = [], []
        for unique_id, agent in self.agents.items():
            agent_ids.append('ID_' + str(unique_id+1))
            n_contacts.append(agent.n_contacts)

        return agent_ids, n_contacts

    def save_manifest(self, work_directory):
        """
        Save manifest file, used by the dashboard to show results.
        """
        floors = []
        for floor in range(self.number_of_floors):
            floors.append(
                        {"name": str(floor),
                         "directory": "floor_" + str(floor) + "/"
                         }
                )

        logging.info('Saving manifest file...')
        # TODO: total over all floors
        if self.traffic_policy is None:
            n_one_way_aisles = 0
        else:
            n_one_way_aisles = len([p for p in self.traffic_policy
                                    if p['direction'] != 0
                                    ])
        manifest_dict = {
            'TimestepInSec': 1,
            'NumberOfFloors': self.number_of_floors,
            'NumberOfOneWayAisles': n_one_way_aisles,
            'NumberOfEmployees': len(self.agents),
            "SimulationName": self.simulation_name,
            "SimulationID": self.simid,
            "Campus": self.facility_name,
            "FacilityOccupancy": self.occupancy_rate,  # between 0.0 and 1.0
            "MaxRoomOccupancy": 1.0,
            "NumberOfShifts": 1,
            "NumberOfEntrances": 1,
            "NumberOfExits": 1,
            "EntranceScreening": False,
            "trajectory_file": "trajectory.txt",
            "floors": floors,
            "scaleMultiplier": max(1, round(self.floorplans[0].width/1500.0)),
            "timestep": 1
        }

        manifest_file = os.path.join(work_directory, 'manifest.json')
        with open(manifest_file, 'w') as json_file:
            json.dump(manifest_dict, json_file, indent=4)

    def save_maps(self, work_directory):
        """Save svg maps for each floor for visualization.
        """
        for floor_number in range(self.number_of_floors):

            floor_directory = os.path.join(work_directory,
                                           'floor_' + str(floor_number)
                                           )
            if not os.path.isdir(floor_directory):
                os.mkdir(floor_directory)

            # Map svg file for the entire facility
            svg_file = os.path.join(floor_directory, 'map.svg')
            bv.export_world_to_svg(
                self.floorplans[floor_number].walls,
                [],
                svg_file,
                marker_locations=[],
                marker_type=None,
                arrows=[],
                max_contacts=100,
                current_time=None,
                show_colobar=False,
                viewbox=[-10,
                         -10,
                         self.floorplans[floor_number].width + 50,
                         self.floorplans[floor_number].height + 50
                         ]
            )

    def create_svg_heatmap(self,
                           contacts_per_coord,
                           floor_directory
                           ):
        """Create and save a heatmap from coordinate contact data
        """
        heatmap_file = os.path.join(floor_directory, 'heatmap.svg')
        map_file = os.path.join(floor_directory, 'map.svg')

        if not os.path.isfile(map_file):
            logging.error('Could not find map file: ' + str(map_file))
            return False

        max_contacts = max(contacts_per_coord.values())
        tree = ET.parse(map_file)

        root = tree.getroot()[0]

        filter_elem = ET.Element('filter')
        filter_elem.set('id', 'blurMe')
        filter_elem.set('width', str(self.contact_distance*2))
        filter_elem.set('height', str(self.contact_distance*2))
        filter_elem.set('x', '-100%')
        filter_elem.set('y', '-100%')

        blur_elem = ET.Element('feGaussianBlur')
        blur_elem.set('in', 'SourceGraphic')
        blur_elem.set('stdDeviation', str(self.contact_distance*0.4))
        blur_elem.set('edgeMode', 'duplicate')

        filter_elem.append(blur_elem)
        root.append(filter_elem)
        color_scale = cm.get_cmap('RdYlGn')

        print('Number of contact coord: ', len(contacts_per_coord))

        for key, v in contacts_per_coord.items():
            x, y = key
            color = color_scale(1.0 - v*1.0/max_contacts)
            new_elem = ET.Element('circle')
            new_elem.set('cx', str(x))
            new_elem.set('cy', str(y))
            new_elem.set('r', str(self.contact_distance))
            new_elem.set('fill', color)
            new_elem.set('fill-opacity', str(0.2))
            new_elem.set('filter', "url(#blurMe)")
            root.append(new_elem)

        try:
            tree.write(heatmap_file)
        except Exception as e:
            logging.exception(e)
            return False

        return True

    def save_outputs(self, work_directory):
        """Write output files to the output directory

        :param str work_directory: directory where all output files are to be
            saved.
        """
        # TODO: generate time-dependent cumulative contacts per coordinate

        # Total contacts per agent
        agent_ids, n_contacts = \
            self.extract_contact_distribution_per_agent()
        filename = os.path.join(work_directory, 'contact_dist_per_agent.csv')
        with open(filename, 'w') as outfile:
            outfile.write('agent_ID,Number_of_Contacts\n')
            for eid, nc in zip(agent_ids, n_contacts):
                outfile.write(str(eid) + ',' + str(nc) + '\n')

        # agent ids
        filename = os.path.join(work_directory, 'agent_ids.txt')
        with open(filename, 'w') as outfile:
            for unique_id, agent in self.agents.items():
                outfile.write(str(unique_id + 1) + '\n')

        # Pair contacts
        filename = os.path.join(work_directory, 'pair_contact.csv')
        self.contact_events.save_pairwise_contacts(filename)

        # Raw contact data
        filename = os.path.join(work_directory, 'raw_contact_data.ccd')
        self.contact_events.save_raw_contact_data(filename)

        # Statistics
        statistics = self.contact_events.exatract_statistics()
        statistics_dict = {"SimulationName": self.simulation_name,
                           "data": statistics
                           }
        filename = os.path.join(work_directory, 'statistics.json')
        with open(filename, 'w') as json_file:
            json.dump(statistics_dict, json_file)

        # Per-floor outputs
        for floor_number in range(self.number_of_floors):

            # Distribution of contact locations

            floor_directory = os.path.join(work_directory,
                                           'floor_' + str(floor_number)
                                           )

            coord_contact_dist_filename = os.path.join(
                                                floor_directory,
                                                'contact_dist_per_coord.csv'
                                            )

            contacts_per_coord = \
                self.contact_events.get_contacts_per_coordinates(
                                                self.current_step,
                                                floor_number
                                            )

            with open(coord_contact_dist_filename, 'a') as outfile:
                outfile.write('x,y,n_contacts\n')
                for pos in contacts_per_coord:
                    x, y = pos
                    dur = contacts_per_coord[pos]
                    outfile.write(str(x) + ',' + str(y) + ','+str(dur)+'\n')

            self.create_svg_heatmap(contacts_per_coord, floor_directory)
