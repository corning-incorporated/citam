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
import os
import json

import citam.engine.io.visualization as bv
from citam.engine.map.point import Point
from citam.engine.io.serializer import serializer

LOG = logging.getLogger(__name__)


@serializer
class Floorplan:
    """
    Class to represent and manipulate a floorplan in a given facility.

    ...

    Attributes
    ----------
    scale : float
        The scale of the floorplan in ft per drawing unit
    spaces : list of Space objects
        list of space objects representing each space (room, hallway,
        etc.). Used for geolocation and navigation
    aisles : list
        list of all aisles. Each aisle is a list with 2 (parallel) walls
    walls : list of Line objects
        list of all the walls in the floorplan. Used to generate the final
        map of the facility and to have realistic navigation.
    minx : int
        the minimum x-value of the facility  in units of the SVG drawing
    miny : int
        the minimum y-value of the facility in units of the SVG drawing
    maxx : int
        the maximum x-value of the facility  in units of the SVG drawing
    maxy : int
        the maximum y-value of the facility in units of the SVG drawing
    """

    def __init__(
        self,
        scale,
        spaces,
        doors,
        walls,
        aisles,
        minx,
        miny,
        maxx,
        maxy,
        floor_name="0",
        special_walls=None,  # Walls not attached to any space
        traffic_policy=None,
        assign_doors_on_load=False,
    ):
        super().__init__()

        self.floor_name = None
        self.scale = scale
        self.floor_name = floor_name
        self.buildings = []
        self.special_walls = special_walls
        if self.special_walls is None:
            self.special_walls = []

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

        self.agent_locations = {}
        self.traffic_policy = traffic_policy

        return

    def match_doors_and_spaces(self):
        """
        Iterate over all doors and create references to corresponding spaces.
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
        return

    def find_space_by_id(self, space_id):
        """
        Find and return the space object that has the given id
        """

        return next(
            (space for space in self.spaces if space.id == space_id), None
        )

    def place_agent(self, agent, pos):
        """Position an agent in a given x, y position on this floor"""
        x, y = pos
        key = str(x) + "-" + str(y)
        # self.grid[x][y].add(agent)
        if key not in self.agent_locations:
            self.agent_locations[key] = [agent]
        else:
            self.agent_locations[key].append(agent)
        agent.pos = pos

    def remove_agent(self, agent):
        """Remove the agent from the facility and set its pos variable to
        None."""
        pos = agent.pos
        x, y = pos
        key = str(x) + "-" + str(y)
        if key not in self.agent_locations:
            LOG.error("Cannot find any agent in this location.")
        else:
            self.agent_locations[key].remove(agent)
        agent.pos = None

    def move_agent(self, agent, pos):
        """
        Move an agent from its current position to a new position.

        Parameters
        ------------
        agent: Agent object to move. Assumed to have its current location
                   stored in a 'pos' tuple.
        pos: Tuple of new position to move the agent to.
        """
        self.remove_agent(agent)
        self.place_agent(agent, pos)

    def identify_this_location(self, x, y, include_boundaries=True):
        """Given a point given by its xy coords, find the space inside of
        which it is located. Returns the space integer id.
        """
        location = None
        for i, room in enumerate(self.spaces):
            if room.is_point_inside_space(
                Point(x=x, y=y), include_boundaries=include_boundaries
            ):
                location = i
                break

        return location

    def get_room_exit_coords(self, room_id):
        """Given a room id, find the exit coords (xy point at the middle of
        the door)
        """

        room = self.spaces[room_id]
        if len(room.doors) == 0:
            LOG.warning(f"{room.unique_name} has no door")
            return None

        return [room_door.intersect_coords for room_door in room.doors]

    def export_to_svg(self, svg_file, include_doors=False):
        """Export the current floorplan to an SVG file.

        Each space is written to file as a path element. Doors
        are written seperately as path element as well.

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

        return

    def _as_dict(self):
        """
        Return the floorplan as a dictionary. The "assign_doors_on_load" flag
        is added so that doors can be reassigned to the appropirate spaces
        when the object is recreated.
        """
        d = {}
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

    def to_json_file(self, json_file: str):
        """Export extracted floorplan data to a json file.

        :param str json_file: file location where to save the data
        """
        with open(json_file, "w") as outfile:
            json.dump(self, outfile, default=serializer.encoder_default)


def floorplan_from_directory(path: str, floor: str, **kwargs) -> Floorplan:
    """Load a floorplan from a given floorplan directory

    .. note:: additional kwargs will be passed to the Floorplan constructor

    :param path: Floorplan Directory
    :param floor: Name of the floor being imported
    :raise FileNotFoundError: If floorplan file cannot be found
    :raise NotADirectoryError: path does not reference a valid directory
    :return: Floorplan Directory
    """

    if not os.path.isdir(path):
        raise NotADirectoryError(f"Floor directory not found: {path}")

    fp_file = os.path.join(path, "updated_floorplan.json")
    if not os.path.isfile(fp_file):
        fp_file = os.path.join(path, "floorplan.json")

    if os.path.isfile(fp_file):
        with open(fp_file, "r") as infile:
            floorplan = json.load(infile, object_hook=serializer.decoder_hook)
        LOG.info("Floorplan successfully loaded.")

    else:
        raise FileNotFoundError("Could not find floorplan file")

    fp_inputs = {}
    if kwargs.items():
        no_none_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        LOG.debug("Updating fp_inputs with kwargs %s", no_none_kwargs)
        fp_inputs.update(**no_none_kwargs)

    floorplan.floor_name = floor

    if "scale" in fp_inputs:
        floorplan.scale = fp_inputs["scale"]

    return floorplan
