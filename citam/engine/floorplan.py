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
import pickle

import citam.engine.basic_visualization as bv
from citam.engine.point import Point

LOG = logging.getLogger(__name__)


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
    width : int
        the overall width of the facility  in units of the SVG drawing
    height : int
        the overall height of the facility in units of the SVG drawing
    """

    def __init__(self,
                 scale,
                 spaces,
                 doors,
                 walls,
                 aisles,
                 width,
                 height,
                 floor_name="0",
                 special_walls=None,  # Walls not attached to any space
                 traffic_policy=None,
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
        self.width = width
        self.height = height
        self.minx = 0
        self.miny = 0

        if any(ele is None for ele in [doors, spaces, walls, aisles]):
            raise ValueError("Invalid inputs for floorplan.")

        n_rooms_with_doors = 0
        n_rooms = 0
        for space in self.spaces:

            if space.building not in self.buildings:
                self.buildings.append(space.building)

            if not space.is_space_a_hallway():
                n_rooms += 1
                if len(space.doors) > 0:
                    n_rooms_with_doors += 1

        LOG.info('Number of spaces: ' + str(len(self.spaces)))
        LOG.info('Number of rooms: ' + str(n_rooms))
        LOG.info('Number of rooms with doors: ' + str(n_rooms_with_doors))
        LOG.info('Number of walls: ' + str(len(self.walls)))
        LOG.info('Total number of doors: ' + str(len(self.doors)))

        n_outside_doors = 0
        for door in self.doors:
            if door.space1 is None or door.space2 is None:
                n_outside_doors += 1
        LOG.info('Number of outside doors: ' + str(n_outside_doors))

        self.agent_locations = {}
        self.traffic_policy = traffic_policy

        return

    def place_agent(self, agent, pos):
        """ Position an agent in a given x, y position on this floor
        """
        x, y = pos
        key = str(x) + '-' + str(y)
        # self.grid[x][y].add(agent)
        if key not in self.agent_locations:
            self.agent_locations[key] = [agent]
        else:
            self.agent_locations[key].append(agent)
        agent.pos = pos

    def remove_agent(self, agent):
        """Remove the agent from the facility and set its pos variable to None.
        """
        pos = agent.pos
        x, y = pos
        key = str(x) + '-' + str(y)
        if key not in self.agent_locations:
            LOG.error('Cannot find any agent in this location.')
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
            if room.is_point_inside_space(Point(x=x, y=y),
                                          include_boundaries=include_boundaries
                                          ):
                location = i
                break

        return location

    def get_room_exit_coords(self, room_id):
        """Given a room id, find the exit coords (xy point at the middle of
        the door)
        """
        room = self.spaces[room_id]
        room_door = None

        if len(room.doors) == 0:
            for door in self.doors:
                if self.spaces[room_id] in [door.space1, door.space2]:
                    room_door = door
                    break
            if room_door is None:
                space_name = str(self.spaces[room_id].unique_name)
                LOG.warning(space_name + ' has no door')
                return None

        else:
            room_door = room.doors[0]

        x = round(room_door.point(0.5).real)
        y = round(room_door.point(0.5).imag)

        return (x, y)

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
            viewbox=None
        )

        return

    def export_to_file(self, filename):
        """Serialize floorplan data and save to file.
        """
        space_dict_list = [vars(space) for space in self.spaces]
        door_dict_list = []

        for door in self.doors:
            if door.space1 is not None:
                name1 = door.space1.unique_name
            else:
                name1 = None

            if door.space2 is not None:
                name2 = door.space2.unique_name
            else:
                name2 = None

            door_dict = {'path': door.path,
                         'space1': name1,
                         'space2': name2
                         }
            door_dict_list.append(door_dict)

        # TODO: also add building walls so that people can run simulations for
        # specific buildings in a facility
        data_dict = {'spaces': space_dict_list,
                     'doors': door_dict_list,
                     'walls': self.walls,
                     'special_walls': self.special_walls,
                     'aisles': self.aisles,
                     'scale': self.scale
                     }

        with open(filename, 'wb') as outfile:
            pickle.dump(data_dict, outfile)

        return

    def export_data_to_pickle_file(self, fp_pickle_file):

        data_to_save = [self.spaces,
                        self.doors,
                        self.walls,
                        self.special_walls,
                        self.aisles,
                        1000,
                        1000,
                        self.scale
                        ]
        with open(fp_pickle_file, 'wb') as f:
            pickle.dump(data_to_save, f)

        return


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
        raise NotADirectoryError(f'Floor directory not found: {path}')

    fp_pickle_file = os.path.join(path, 'updated_floorplan.pkl')
    if not os.path.isfile(fp_pickle_file):
        fp_pickle_file = os.path.join(path, 'floorplan.pkl')

    if os.path.isfile(fp_pickle_file):
        with open(fp_pickle_file, 'rb') as f:
            fields = ('spaces', 'doors', 'walls', 'special_walls', 'aisles',
                      'width', 'height', 'scale')
            fp_inputs = {k: v for k, v in zip(fields, pickle.load(f))}
        LOG.info('Floorplan successfully loaded.')
    else:
        raise FileNotFoundError("Could not find floorplan file")

    if kwargs.items():
        no_none_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        LOG.debug("Updating fp_inputs with kwargs %s", no_none_kwargs)
        fp_inputs.update(**no_none_kwargs)

    fp_inputs['floor_name'] = floor
    LOG.info('Initializing floorplan: '
             'doors: %s, '
             'walls: %d, '
             'scale: %d [ft/drawing unit]',
             len(fp_inputs.get('doors', [])),
             len(fp_inputs.get('walls', [])),
             fp_inputs.get('scale', float("NaN")))

    LOG.debug("Initializing floorplan: %s", fp_inputs)
    return Floorplan(**fp_inputs)
