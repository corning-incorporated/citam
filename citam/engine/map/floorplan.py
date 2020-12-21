# Copyright 2020. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================

import logging
import os
import json
from typing import Dict, Any, Tuple, List, Optional, Union
import pathlib

from svgpathtools import Line

import citam.engine.io.visualization as bv
from citam.engine.map.point import Point
from citam.engine.io.serializer import serializer
from citam.engine.map.space import Space
from citam.engine.map.door import Door
from citam.engine.core.agent import Agent

LOG = logging.getLogger(__name__)


@serializer
class Floorplan:
    """
    Class to represent and manipulate a floorplan in a given facility.
    """

    def __init__(
        self,
        scale: float,
        spaces: List[Space],
        doors: List[Door],
        walls: List[Line],
        aisles: Tuple[Line, Line],
        minx: float,
        miny: float,
        maxx: float,
        maxy: float,
        floor_name="0",
        special_walls: List[Line] = None,  # Walls not attached to any space
        traffic_policy: List[Dict[str, Any]] = None,
        assign_doors_on_load: bool = False,
    ) -> None:
        """
        Initialize a new floorplan object.

        :param scale: The scale of the floorplan in units of [drawing unit/ft]
        :type scale: float
        :param spaces: List of spaces in this floorplan
        :type spaces: List[Space]
        :param doors: List of doors in this floorplan.
        :type doors: List[Door]
        :param walls: List of walls in this floorplan.
        :type walls: List[Line]
        :param aisles: List of aisles
        :type aisles: Tuple[Line, Line]
        :param minx: Minimum x coordinate of the floorplan
        :type minx: float
        :param miny: Minimum y coordinate of the floorplan
        :type miny: float
        :param maxx: Maximum x coordinate of the floorplan
        :type maxx: float
        :param maxy: Maximum y coordinate of the floorplan
        :type maxy: float
        :param floor_name: Name of the floor, defaults to "0"
        :type floor_name: str, optional
        :param special_walls: List of special walls, defaults to None
        :type special_walls: List[Line], optional
        :param assign_doors_on_load: If doors should be assigned automatically,
             defaults to False
        :type assign_doors_on_load: bool, optional
        :raises ValueError: If no doors, spaces, walls or aisles are provided
        """
        self.floor_name = None
        self.scale = scale
        self.floor_name = floor_name
        self.buildings: List[str] = []
        self.special_walls: List[Line] = special_walls if special_walls else []

        self.spaces = spaces
        self.doors = doors
        self.walls = walls
        self.aisles = aisles
        self.maxx = maxx
        self.maxy = maxy
        self.minx = minx
        self.miny = miny

        if any(ele is None for ele in [doors, spaces, walls, aisles]):
            raise ValueError("Invalid inputs for floorplan.")

        if assign_doors_on_load:
            self.match_doors_and_spaces()

        n_rooms_with_doors = 0
        n_rooms = 0
        for space in self.spaces:
            if space.building not in self.buildings:
                self.buildings.append(space.building)
            if not space.is_space_a_hallway():
                n_rooms += 1
                if len(space.doors) > 0:
                    n_rooms_with_doors += 1

        LOG.info("Number of spaces: " + str(len(self.spaces)))
        LOG.info("Number of rooms: " + str(n_rooms))
        LOG.info("Number of rooms with doors: " + str(n_rooms_with_doors))
        LOG.info("Number of walls: " + str(len(self.walls)))
        LOG.info("Total number of doors: " + str(len(self.doors)))

        n_outside_doors = sum(
            1
            for door in self.doors
            if door.space1 is None or door.space2 is None
        )
        LOG.info("Number of outside doors: " + str(n_outside_doors))

        # This is to avoid using a grid and keeping track of all possible
        # locations on the floor. Instead, only locations that have agents
        # are tracked.
        self.agent_locations: Dict[str, List[Agent]] = {}
        self.traffic_policy = traffic_policy

    def match_doors_and_spaces(self) -> None:
        """
        Iterate over all doors and create references to corresponding spaces.
        This is useful when recreating a floorplan from serialized data.
        """
        for door in self.doors:
            if door.space1_id:
                space1 = self.find_space_by_id(door.space1_id)
                if space1:
                    space1.doors.append(door)
                    door.space1 = space1
            if door.space2_id:
                space2 = self.find_space_by_id(door.space2_id)
                if space2:
                    space2.doors.append(door)
                    door.space2 = space2

    def find_space_by_id(self, space_id: int) -> Optional[Space]:
        """
        Find and return the space object that has the given id.

        :param space_id: The ID of the space of interest.
        :type space_id: int
        :return: The space that has this ID, None if no match found.
        :rtype: Space
        """
        return next(
            (space for space in self.spaces if space.id == space_id), None
        )

    def place_agent(self, agent: Agent, pos: Tuple[int, int]) -> None:
        """
        Position an agent in a given x, y position on this floor

        :param agent: The agent to place on this floor.
        :type agent: Agent
        :param pos: The xy location to place the agent.
        :type pos: Tuple[int, int]
        """
        x, y = pos
        key = str(x) + "-" + str(y)
        if key not in self.agent_locations:
            self.agent_locations[key] = [agent]
        else:
            self.agent_locations[key].append(agent)
        agent.pos = pos

    def remove_agent(self, agent: Agent) -> None:
        """
        Remove the agent from the floor and set its position to None.

        :param agent: the agent to remove from this floor.
        :type agent: Agent
        """
        pos = agent.pos
        x, y = pos
        key = str(x) + "-" + str(y)
        if key not in self.agent_locations:
            LOG.error("Cannot find any agent in this location.")
        else:
            self.agent_locations[key].remove(agent)
        agent.pos = None

    def move_agent(self, agent: Agent, pos: Tuple[int, int]) -> None:
        """
        Move an agent from its current position to a new position.

        :param agent: Agent object to move. Assumed to have its current
                location stored in a 'pos' tuple.
        :type agent: Agent
        :param pos: Tuple of new position to move the agent to.
        :type pos: Tuple[int, int]
        """
        self.remove_agent(agent)
        self.place_agent(agent, pos)

    def identify_this_location(
        self, x: int, y: int, include_boundaries=True
    ) -> Optional[int]:
        """
        Given a point given by its xy coords, find the space inside of which it
        is located. Returns the space integer id.

        :param x: x-coordinate position
        :type x: int
        :param y: y-coordinate position
        :type y: int
        :param include_boundaries: whether to include space boundaries in the
            definition of the space, defaults to True
        :type include_boundaries: bool, optional
        :return: The index of the space where this position falls.
        :rtype: Optional[int]
        """

        location = None
        for i, room in enumerate(self.spaces):
            if room.is_point_inside_space(
                Point(x=x, y=y), include_boundaries=include_boundaries
            ):
                location = i
                break

        return location

    def get_room_exit_coords(
        self, room_id: int
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Given a room id, find the exit coords (xy point at the middle of the
        door)

        :param room_id: [description]
        :type room_id: int
        :return: The xy coordinates where an agent can exit this space.
        :rtype: Optional[Tuple[int, int]]
        """
        room = self.spaces[room_id]
        if len(room.doors) == 0:
            LOG.warning(f"{room.unique_name} has no door")
            return None

        return [room_door.intersect_coords for room_door in room.doors]

    def export_to_svg(
        self, svg_file: Union[str, pathlib.Path], include_doors=False
    ) -> None:
        """
        Export the current floorplan to an SVG file.

        Each space is written to file as a path element. Doors are written
        seperately as path element as well.

        :param svg_file: location where to save the file.
        :type svg_file: Union[str, pathlib.Path]
        :param include_doors: Whether to include doors in the SVG file or not,
                 defaults to False
        :type include_doors: bool, optional
        """
        doors = []
        if include_doors:
            doors = self.doors

        bv.export_world_to_svg(
            self.walls,
            [],
            svg_file,
            marker_locations=[],
            marker_type=None,
            arrows=[],
            doors=doors,
            max_contacts=100,
            current_time=None,
            show_colobar=False,
            viewbox=None,
        )

    def _as_dict(self) -> Dict[str, Any]:
        """
        Return the floorplan as a dictionary. The "assign_doors_on_load" flag
        is added so that doors can be reassigned to the appropirate spaces
        when the object is recreated.

        :return: A dictionary representing this floorplan
        :rtype: Dict[str, Any]
        """

        d: Dict[str, Any] = {}
        d["scale"] = self.scale
        d["spaces"] = self.spaces
        d["doors"] = self.doors
        d["walls"] = self.walls
        d["aisles"] = self.aisles
        d["minx"] = self.minx
        d["maxx"] = self.maxx
        d["miny"] = self.miny
        d["maxy"] = self.maxy
        d["special_walls"] = self.special_walls
        d["assign_doors_on_load"] = True

        return d

    def to_json_file(self, json_file: Union[str, pathlib.Path]) -> None:
        """
        Export extracted floorplan data to a json file.

        :param json_file: location of the json file to write to.
        :type json_file: Union[str, pathlib.Path]
        """

        with open(json_file, "w") as outfile:
            json.dump(self, outfile, default=serializer.encoder_default)


def floorplan_from_directory(
    directory: Union[str, pathlib.Path], floor: str, **kwargs
) -> Floorplan:
    """
    Load a floorplan from a given floorplan directory. The floorplan is
    expected to be in a file named floorplan.json or updated_floorplan.json

    .. note:: additional kwargs will be passed to the Floorplan constructor

    :param directory: Floorplan Directory
    :type directory: Union[str, pathlib.Path]
    :param floor: Name of the floor being imported
    :type floor: str
    :raises FileNotFoundError: If floorplan file cannot be found
    :raises NotADirectoryError: path does not reference a valid directory
    :raises NotADirectoryError: [description]
    :raises FileNotFoundError: [description]
    :return: Floorplan instance found in this directory.
    :rtype: Floorplan
    """

    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Floor directory not found: {directory}")

    fp_file = os.path.join(directory, "updated_floorplan.json")
    if not os.path.isfile(fp_file):
        fp_file = os.path.join(directory, "floorplan.json")

    if os.path.isfile(fp_file):
        with open(fp_file, "r") as infile:
            floorplan = json.load(infile, object_hook=serializer.decoder_hook)
        LOG.info("Floorplan successfully loaded.")

    else:
        raise FileNotFoundError(f"Could not find floorplan file: {fp_file}")

    fp_inputs: Dict[str, Any] = {}
    if kwargs.items():
        no_none_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        LOG.debug("Updating fp_inputs with kwargs %s", no_none_kwargs)
        fp_inputs.update(**no_none_kwargs)

    floorplan.floor_name = floor

    if "scale" in fp_inputs:
        floorplan.scale = fp_inputs["scale"]

    return floorplan
