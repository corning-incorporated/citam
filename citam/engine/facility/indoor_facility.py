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
import os
from typing import Tuple, List

import networkx as nx
import progressbar as pb
from svgpathtools import Line, svg2paths

import citam.engine.io.visualization as bv
import citam.engine.map.utils as fu
import citam.engine.map.geometry as gsu
from citam.engine.map.door import Door
from citam.engine.map.point import Point
from citam.engine.map.floorplan import Floorplan
import json
from citam.engine.facility.navigation import Navigation

LOG = logging.getLogger(__name__)


class Facility:
    def __init__(
        self,
        floorplans: List[Floorplan],
        entrances: List[Dict],
        facility_name: str,
        traffic_policy=None,
    ):

        self.floorplans = floorplans
        self.number_of_floors = len(floorplans)
        self.entrances = entrances
        self.facility_name = facility_name
        self.traffic_policy = traffic_policy

        # Initialize navigation network
        self.navigation = Navigation(
            self.floorplans, self.facility_name, self.traffic_policy
        )

        # Validate entrances
        self.validate_entrances()

        # Find offices and verify that they are accessible from at least one
        # entrance
        self.find_and_remove_unreachable_rooms()

        # Find and group all remaining spaces in this facility
        self.group_remaining_spaces()

    def choose_best_entrance(
        self, office_floor: int, office_id: int
    ) -> Tuple[Door, int]:
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

            (
                entrance_floor,
                entrance_space_id,
            ) = self.get_entrance_floor_and_space_id(entrance)

            entrance_space = self.navigation.floorplans[entrance_floor].spaces[
                entrance_space_id
            ]

            possible_entrance_doors = self.find_possible_entrance_doors(
                entrance_floor, entrance_space
            )
            entrance_door = np.random.choice(possible_entrance_doors)
            door_mid_point = entrance_door.path.point(0.5)
            entrance_coords = (
                round(door_mid_point.real),
                round(door_mid_point.imag),
            )
            route = self.navigation.get_route(
                entrance_coords, entrance_floor, office_id, office_floor, 1.0
            )
            if route is not None and len(route) < min_length:
                min_length = len(route)
                best_entrance_door = entrance_door
                best_entrance_floor = entrance_floor

        if best_entrance_door is None:
            office = self.floorplans[office_floor].spaces[office_id]
            LOG.info("No entrance found for office: %s", office.unique_name)
        return best_entrance_door, best_entrance_floor

    def validate_entrances(self):
        """
        Iterate over possible entrances and verify that there is indeed
        an outside facing door and that the door is present in the navnet.
        """
        for entrance in self.entrances:

            (
                entrance_floor,
                entrance_space_id,
            ) = self.get_entrance_floor_and_space_id(entrance)

            entrance_space = self.navigation.floorplans[entrance_floor].spaces[
                entrance_space_id
            ]
            possible_entrance_doors = self.find_possible_entrance_doors(
                entrance_floor, entrance_space
            )
            if len(possible_entrance_doors) == 0:
                raise ValueError("This entrance does not have any doors")

            entrance_door = np.random.choice(possible_entrance_doors)

            if not self.is_door_in_navnet(entrance_floor, entrance_door):
                raise ValueError(
                    f"Cannot use this entrance: {entrance['name']}"
                )

    def is_door_in_navnet(
        self, entrance_floor: int, entrance_door: Door
    ) -> bool:
        """
        Verify if a given door is part of the navnet.

        :param int entrance_floor: index of the entrance floor.
        :param Door entrance_door: door object to check.
        :return: True if door is part of navnet, False otherwise.
        """
        entrance_coords = entrance_door.intersect_coords
        if self.navigation.navnet_per_floor[entrance_floor].has_node(
            entrance_coords
        ):
            edges = self.navigation.navnet_per_floor[entrance_floor].edges(
                entrance_coords
            )
            if len(edges) == 0:
                LOG.info("No edges from this door : %s", entrance_door)
                return False
            else:
                return True
        else:
            LOG.info("Door coords not in navnet: %s", entrance_coords)
            return False

    def find_floor_by_name(self, floor_name: str) -> int:
        """
        Find the floor that corresponds to this name.

        :param str floor_name: Name of the floor.
        :return: index of the floorplan. None if not found.
        """
        fp_index = None
        for i, fp in enumerate(self.floorplans):
            if fp.floor_name == floor_name:
                fp_index = i
                break

        return fp_index

    def find_space_by_name(self, fp_index: int, ename: str) -> int:
        """
        Find the space that corresponds to a given name. Mostly used to find
        the space that corresponds to a user-given entrance.

        :param int fp_index: index of the floorplan that contains the space
        :param str ename: name of the space.
        :return: index of the space. None if not found.
        """
        space_index = None
        for i, space in enumerate(self.floorplans[fp_index].spaces):
            if space.unique_name == ename:
                space_index = i
                break

        return space_index

    def find_possible_entrance_doors(self, entrance_floor, entrance_space):
        """
        Iterate over all doors in the facility to identify any that belong to
        the entrance floor and entrance space and are outside facing.
        """
        possible_entrance_doors = []
        for door in self.navigation.floorplans[entrance_floor].doors:
            if door.space1 is not None and door.space2 is not None:
                # The door has to lead to outside of the facility
                continue
            if (
                door.space1 is not None
                and door.space1.unique_name == entrance_space.unique_name
                or door.space2 is not None
                and door.space2.unique_name == entrance_space.unique_name
            ):
                possible_entrance_doors.append(door)
        return possible_entrance_doors

    def group_remaining_spaces(self) -> None:
        """
        Iterate over all other spaces and group them according to their
        function
        """
        (
            self.meeting_rooms,
            self.labs,
            self.cafes,
            self.restrooms,
            self.all_office_spaces,
        ) = (
            [],
            [],
            [],
            [],
            [],
        )  # List of list of space indices

        for fp in self.navigation.floorplans:
            (
                floor_offices,
                floor_labs,
                floor_cafes,
                floor_restrooms,
                floor_meeting_rooms,
            ) = ([], [], [], [], [])

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

            self.all_office_spaces.append(floor_offices)
            self.labs.append(floor_labs)
            self.cafes.append(floor_cafes)
            self.restrooms.append(floor_restrooms)
            self.meeting_rooms.append(floor_meeting_rooms)

        self.total_offices = sum(
            len(rooms) for rooms in self.all_office_spaces
        )
        LOG.info("Total offices is " + str(self.total_offices))

        n_rooms = sum(len(rooms) for rooms in self.labs)
        LOG.info("Total labs is " + str(n_rooms))

        n_rooms = sum(len(rooms) for rooms in self.cafes)
        LOG.info("Total cafeterias: " + str(n_rooms))

        n_rooms = sum(len(rooms) for rooms in self.restrooms)
        LOG.info("Total restrooms: " + str(n_rooms))

        n_rooms = sum(len(rooms) for rooms in self.meeting_rooms)
        LOG.info("Total meeting rooms: " + str(n_rooms))

    def find_and_remove_unreachable_rooms(self):
        """
        Iterate over all spaces and remove the unreachable ones.
        """

        for fn, floorplan in enumerate(self.floorplans):
            tmp_spaces = []
            for space_index, space in enumerate(floorplan.spaces):
                if space.is_space_a_hallway():
                    tmp_spaces.append(space)
                elif len(space.doors) > 0:
                    exit_coords = floorplan.get_room_exit_coords(space_index)
                    if exit_coords:
                        best_entrance, _ = self.choose_best_entrance(
                            fn, space_index
                        )
                        if best_entrance is not None:
                            tmp_spaces.append(space)
            n_unreachable = len(floorplan.spaces) - len(tmp_spaces)
            LOG.info("Unreachable rooms on floor %d: %d", fn, n_unreachable)
            self.floorplans[fn].spaces = tmp_spaces

    def get_entrance_floor_and_space_id(self, entrance):

        ename = entrance["name"].lower()
        efloor = entrance["floor"]

        entrance_floor = self.find_floor_by_name(efloor)
        if entrance_floor is None:
            raise ValueError("Unknown entrance floor: %s", efloor)

        entrance_space_id = self.find_space_by_name(entrance_floor, ename)
        if entrance_space_id is None:
            raise ValueError("Unknown space: ", ename)

        return entrance_floor, entrance_space_id
