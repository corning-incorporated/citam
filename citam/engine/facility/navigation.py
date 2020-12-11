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

import errno
import logging
import math
import os
from itertools import product
from enum import Enum
import json
from typing import List, Dict, Tuple, Union, Optional, Any
import pathlib

import networkx as nx
from svgpathtools import Line

import citam.engine.map.geometry as gsu
import citam.engine.io.storage_utils as su
from citam.engine.map.point import Point
from citam.engine.map.floorplan import Floorplan
from citam.engine.map.space import Space

LOG = logging.getLogger(__name__)


class TrafficPattern(Enum):
    ONEWAY_POSITIVE_DIRECTION = 1
    ONEWAY_NEGATIVE_DIRECTION = -1
    TWO_WAY = 0


class MultifloorType(Enum):
    """
    Enum to hold the different ways the different floors are connected in
    multifloor facilities.

    Two types are defined:
    - naming-X: corresponding spaces on different floors don't necessarily have
            the same xy but their names carry information about the floor.
            The 'X' at the end is for the position of the floor identifier in
            space names. For example: 'naming-2' => F2R13 or 'naming-1' => 213
            both are valid identifier of room 13 in the second floor.
    - xy: corresponding spaces on different floors have the same xy. This means
          the space directly on top of a stairway in terms of xy position is
          also a stairway.
    """

    NAMING = "naming-2"
    XY = "xy"


class Navigation:
    """
    Implements the navigation class to manage agents circulation between
    different spaces in a facility.
    """

    def __init__(
        self,
        floorplans: List[Floorplan],
        facility_name: str,
        traffic_policy: List[Dict[str, Union[str, int]]],
        multifloor_type: str = MultifloorType.NAMING.value,
    ):
        """
        Initialize a new navigation object.

        :param floorplans: list of floorplans in this facility.
        :type floorplans: List[Floorplan]
        :param facility_name: Name of the facility, used to retrive data for
                this facility from the user cache.
        :type facility_name: str
        :param traffic_policy: The traffic policy in place in this facility.
        :type traffic_policy: List[Dict[str, Union[str, int]]]
        :param multifloor_type: type of correspondence between spaces in
                different floors, defaults to "naming"
        :type multifloor_type: str, optional
        """

        self.multifloor_type = multifloor_type
        self.navnet_per_floor = []
        self.oneway_network_per_floor = []
        self.hallways_graph_per_floor = []
        self.floorplans = floorplans
        self.facility_name = facility_name
        self.traffic_policy = traffic_policy

        for fnum, floorplan in enumerate(self.floorplans):

            LOG.info(
                "Loading navigation data for floor {%s}", floorplan.floor_name
            )

            floorplan_directory = su.get_datadir(
                facility_name, floorplan.floor_name
            )

            # Load navigation network
            LOG.info("Loading navnet...")
            floor_navnet_file = os.path.join(
                floorplan_directory, "routes.json"
            )
            navnet = self.load_floor_navnet(floor_navnet_file)
            self.navnet_per_floor.append(navnet)

            # Load oneway network
            if self.traffic_policy is not None and self.traffic_policy != []:
                LOG.info("Loading oneway network...")
                oneway_net_file = os.path.join(
                    floorplan_directory, "oneway_network.json"
                )
                oneway_net = self.load_floor_oneway_net(oneway_net_file)
                self.oneway_network_per_floor.append(oneway_net)

            # Load hallways graph
            LOG.info("Loading hallway graph for floor...")
            floor_hallway_graph_file = os.path.join(
                floorplan_directory, "hallways_graph.json"
            )
            hg = self.load_hallway_graph(floor_hallway_graph_file)
            self.hallways_graph_per_floor.append(hg)

        if len(self.floorplans) > 1:
            self.create_multifloor_navnet()

        self.apply_traffic_policy()

    def load_hallway_graph(
        self, floor_hallway_graph_file: Union[str, pathlib.Path]
    ) -> nx.Graph:
        """
        Load the hallway graph from file. The hallway graph is a graph of
        hallways that share at least one boundary.

        :param floor_hallway_graph_file: location of the file containing the
                 hallway graph in json format.
        :type floor_hallway_graph_file: Union[str, pathlib.Path]
        :raises FileNotFoundError: If the provided file is not found.
        :return: [description]
        :rtype: nx.Graph
        """

        try:
            with open(floor_hallway_graph_file, "r") as f:
                hg_data = json.load(f)
        except Exception as exc:
            raise FileNotFoundError(
                f"Failed to load hallway graph {floor_hallway_graph_file}. "
                + f"This is the error: {exc}."
            )
        hg = nx.readwrite.json_graph.node_link_graph(hg_data)
        LOG.info("Success loading the hallway graph!")
        return hg

    def load_floor_oneway_net(
        self, oneway_net_file: Union[str, pathlib.Path]
    ) -> nx.Graph:
        """
        Load the oneway network from file. The oneway network is a graph of
        connected aisles that support one-way navigation.

        :param oneway_net_file: location of one-way network file in json
                format.
        :type oneway_net_file: Union[str, pathlib.Path]
        :raises FileNotFoundError: If file not found.
        :return: the network as read from file.
        :rtype: nx.Graph
        """

        if not os.path.isfile(oneway_net_file):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), oneway_net_file
            )
        with open(oneway_net_file, "r") as f:
            oneway_data = json.load(f)
        oneway_net = nx.readwrite.json_graph.node_link_graph(oneway_data)
        LOG.info("Success loading the oneway network file!")
        return oneway_net

    def load_floor_navnet(
        self, floor_navnet_file: Union[str, pathlib.Path]
    ) -> nx.Graph:
        """
        Load the navigation network (navnet) from file. The navnet is a graph
        of connected notable points in the facility describing where agents
        can move around.

        :param floor_navnet_file: location of navnet file in json format.
        :type floor_navnet_file: Union[str, pathlib.Path]
        :raises FileNotFoundError: if specified file is not found.
        :return: The navnet object.
        :rtype: nx.Graph
        """
        if not os.path.isfile(floor_navnet_file):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), floor_navnet_file
            )
        with open(floor_navnet_file, "r") as f:
            navnet_data = json.load(f)
        navnet = nx.readwrite.json_graph.node_link_graph(navnet_data)
        LOG.info("Success loading navnet from file!")
        return navnet

    def get_corresponding_vertical_space(
        self, ref_space: Space, dest_floor: int
    ) -> Tuple[Optional[int], Optional[Space]]:
        """
        Given a reference space and a destination floor, find the space
        on the destination floor that lies in the same xy position as the
        reference space. Mostly used for stairs and elevators.

        :param ref_space: the reference space
        :type ref_space: Space
        :param dest_floor: index of the destination floor
        :type dest_floor: int
        :raises ValueError: if the value used for the multifloor_type is
                 unknown.
        :return: index of the corresponding space and the corresponding space
                 itself.
        :rtype: Tuple[Optional[int], Optional[Space]]
        """
        # TODO: Add regex as another method.
        dest_space = None
        dest_space_id = None

        if "naming" in self.multifloor_type:
            name1 = ref_space.unique_name

            floor_identifier = self.multifloor_type.split("-")[-1]
            if not floor_identifier.isnumeric():
                raise ValueError(
                    "Number expected at the end of the multifloor type"
                )
            fid = int(floor_identifier)
            if fid > 0:
                if len(name1) < fid:
                    raise ValueError(
                        f"This multifloor type {self.multifloor_type} cannot \
                        be used for the current naming (e.g. {name1}). please \
                        update (must be less than name lenght)"
                    )
                name2 = (
                    name1[fid - 1]
                    + str(dest_floor + 1)
                    + name1[fid + 1 :]  # noqa
                )
            else:
                name2 = str(dest_floor + 1) + name1[1:]

            for j, space in enumerate(self.floorplans[dest_floor].spaces):
                if space.unique_name == name2 and space.is_space_vertical():
                    dest_space = space
                    dest_space_id = j
                    break
        elif self.multifloor_type == "xy":
            p = ref_space.get_random_internal_point()
            dest_space_id = self.floorplans[dest_floor].identify_this_location(
                p.x, p.y
            )
            if dest_space_id is not None:
                dest_space = self.floorplans[dest_floor].spaces[dest_space_id]
        else:
            raise ValueError(
                f"Unknown multifloor type: {self.multifloor_type}. "
                + "Expected: naming-D or 'xy'"
            )

        return dest_space_id, dest_space

    def add_vertical_edges(
        self, floor_number1: int, floor_number2: int
    ) -> int:
        """
        Create new edges in the navigation network to connect vertical
        spaces allowing multifloor navigation. If there are more than 2 floors
        in the facility, this function should be used toconnect only
        adjacent floors.

        This function finds all the vertical spaces in the starting floor and
        finds if there is a corresponding space on the destination floor in
        which case edges are added between them.

        :param floor_number1: index of the first floor.
        :type floor_number1: int
        :param floor_number2: index of the second floor.
        :type floor_number2: int
        :return: Number of vertical spaces connected.
        :rtype: int
        """

        # Get all vertical spaces in first floor
        n_vert_edges = 0
        starting_floor_verticals = [
            (i, space)
            for i, space in enumerate(self.floorplans[floor_number1].spaces)
            if space.is_space_vertical()
        ]
        for i, sf_vert_space in starting_floor_verticals:
            coords1 = self.floorplans[floor_number1].get_room_exit_coords(i)
            if coords1 is None:
                continue

            j, space2 = self.get_corresponding_vertical_space(
                sf_vert_space, floor_number2
            )
            if space2 is None:
                continue

            if not space2.is_space_vertical():
                continue

            coords2 = self.floorplans[floor_number2].get_room_exit_coords(j)
            if coords2 is None:
                continue

            # add edges between room the exit coords of the vertical spaces
            # TODO: create edge between a random xy coords inside rooms

            for c1, c2 in product(coords1, coords2):
                node1 = (c1[0], c1[1], floor_number1)
                node2 = (c2[0], c2[1], floor_number2)

                if self.multifloor_navnet.has_node(
                    node1
                ) and self.multifloor_navnet.has_node(node2):
                    self.multifloor_navnet.add_edge(node1, node2)
                    self.multifloor_navnet.add_edge(node2, node1)
                    n_vert_edges += 1
                else:
                    LOG.warning("%s or %s not found in graph", node1, node2)
        return n_vert_edges

    def create_multifloor_navnet(self):
        """
        Use vertical spaces to combine multiple floor navnets into a global
        navnet.
        """
        self.multifloor_navnet = nx.DiGraph()
        # Relabel nodes in each floor navnet
        for fn in range(len(self.floorplans)):
            mapping = {
                node: (node[0], node[1], fn)
                for node in list(self.navnet_per_floor[fn].nodes())
            }

            navnet = nx.relabel_nodes(self.navnet_per_floor[fn], mapping)
            # Compose new graph with all floor graphs
            self.multifloor_navnet = nx.compose(self.multifloor_navnet, navnet)

        floor_number1 = 0
        nverts = 0
        for floor_number2 in range(1, len(self.floorplans)):
            nverts += self.add_vertical_edges(floor_number1, floor_number2)
            floor_number1 = floor_number2

    def apply_traffic_policy(self):
        """
        Remove edges that should not exist based on user traffic policy
        for all floors.
        """
        if self.traffic_policy is None or self.traffic_policy == []:
            return
        LOG.info("Appling traffic policy...")
        if len(self.floorplans) == 1:
            for pol in self.traffic_policy:
                self.set_policy_for_aisle(
                    pol,
                    self.navnet_per_floor[0],
                    self.oneway_network_per_floor[0],
                )
        else:
            for i, fp in enumerate(self.floorplans):
                LOG.info("Working with floor {%s}", fp.floor_name)
                for pol in self.traffic_policy:
                    if pol["floor"] == fp.floor_name:
                        self.set_policy_for_aisle(
                            pol,
                            self.navnet_per_floor[i],
                            self.oneway_network_per_floor[i],
                            navnet_type="multifloor",
                            floor_number=i,
                        )

    def set_policy_for_aisle(
        self,
        policy: Dict[str, Union[str, int]],
        navnet: nx.Graph,
        oneway_net: nx.Graph,
        navnet_type="singlefloor",
        floor_number=0,
    ) -> None:
        """
        Find edge of interest from navnet and keep only the ones that
        match the desired traffic pattern.

        :param policy: The traffic policy to apply
        :type policy: Dict[str, Union[str, int]]
        :param navnet: the navnet to apply the policy to.
        :type navnet: nx.Graph
        :param oneway_net: The oneway navnet for this facility.
        :type oneway_net: nx.Graph
        :param navnet_type: the type of navnet, defaults to "singlefloor"
        :type navnet_type: str, optional
        :param floor_number: integer id of the floor of interst, defaults to 0
        :type floor_number: int, optional
        :raises ValueError: If the direction is not a valid value.
        """
        LOG.info("Applying this policy {%s}: ", policy)
        if policy["direction"] == TrafficPattern.TWO_WAY:
            return

        if (
            policy["direction"]
            != TrafficPattern.ONEWAY_NEGATIVE_DIRECTION.value
            and policy["direction"]
            != TrafficPattern.ONEWAY_POSITIVE_DIRECTION.value
        ):
            LOG.info(
                "Supported values are {%d}, {%d} and {%d}. See docs.",
                TrafficPattern.ONEWAY_POSITIVE_DIRECTION.value,
                TrafficPattern.ONEWAY_NEGATIVE_DIRECTION.value,
                TrafficPattern.TWO_WAY.value,
            )
            raise ValueError(
                f"Unknown direction in traffic policy: {policy['direction']}"
            )

        # Find edges of interest and remove them from navnet if they don't
        # match the desired traffic direction
        n_coords = 0
        for edge in oneway_net.edges(data=True):
            if str(edge[2]["id"]) == str(policy["segment_id"]):
                all_coords = [edge[0], edge[1]] + edge[2]["inter_points"]
                n_coords = len(all_coords)
                break
        if n_coords <= 1:
            raise ValueError(
                f"Could not find nav segment to apply traffic policy {policy}"
            )

        for i in range(n_coords - 1):
            for j in range(i, n_coords):
                if navnet_type == "singlefloor":
                    test_edge1 = (
                        tuple(all_coords[i]),
                        tuple(all_coords[j]),
                    )
                    test_edge2 = (
                        tuple(all_coords[j]),
                        tuple(all_coords[i]),
                    )
                else:
                    test_edge1 = (
                        tuple(all_coords[i]),  # type: ignore
                        tuple(all_coords[j]),
                        floor_number,
                    )

                    test_edge2 = (
                        tuple(all_coords[j]),  # type: ignore
                        tuple(all_coords[i]),
                        floor_number,
                    )
                for test_edge in [test_edge1, test_edge2]:
                    if navnet.has_edge(
                        test_edge[0], test_edge[1]
                    ) and not self.is_edge_matching_direction(
                        test_edge, policy["direction"]
                    ):
                        navnet.remove_edge(test_edge[0], test_edge[1])
                        LOG.debug("Edge removed {%s}", test_edge)

    def is_edge_matching_direction(
        self,
        edge: Tuple[Tuple[Any, ...], Tuple[Any, ...]],
        desired_direction: Union[str, int],
    ) -> bool:
        """
        Verify if edge direction matches desired direction.

        This is how the edge direction is defined and computed:
        Use the start and end points to compute a direction angle alpha
        with respect to the positive x-axis. The positive direction corresponds
        to 0 <= alpha <= 90 or 270 > alpha >= 360. The negative direction is
        the other half of the possible angles.

        :param edge: The edge of interest.
        :type edge: Tuple[Tuple[Any, ...], Tuple[Any, ...]]
        :param desired_direction: The direction of interest.
        :type desired_direction: int
        :return: Whether a match is found or not.
        :rtype: bool
        """
        # Compute angle
        dx = edge[1][0] - edge[0][0]
        dy = edge[1][1] - edge[0][1]
        alpha = math.degrees(math.atan2(dy, dx))

        if (alpha >= 0 and alpha <= 90) or (alpha > 180 and alpha <= 360):
            edge_direction = TrafficPattern.ONEWAY_POSITIVE_DIRECTION.value
        else:
            edge_direction = TrafficPattern.ONEWAY_NEGATIVE_DIRECTION.value

        return int(desired_direction) == edge_direction

    def get_route(
        self,
        starting_location: int,
        starting_floor_number: int,
        destination: int,
        destination_floor_number: int,
        pace: float,
    ) -> Optional[List[Tuple[Any, int]]]:
        """
        Get the shortest path between 2 spaces in the floorplans.

        :param starting_location: index of the space where the agent is
                currently located
        :type starting_location: int
        :param starting_floor_number: index of the the floor where the
                agent is going
        :type starting_floor_number: int
        :param destination: index of the space where the agent is going.
        :type destination: int
        :param destination_floor_number: index of the floor where the
                agent is going.
        :type destination_floor_number: int
        :param pace: The pace of walking [distance unit/timestep].
        :type pace: float
        :return: The sequence of xy points and floor numbers to get from
                current location to destination. None if no route is found.
        :rtype: Optional[List[Tuple[Any, int]]]
        """

        if len(self.floorplans) == 1:
            routes = self.get_best_possible_routes_same_floor(
                starting_floor_number, starting_location, destination
            )
        else:
            routes = self.get_best_possible_routes_multifloor(
                starting_location,
                starting_floor_number,
                destination,
                destination_floor_number,
            )

        if not routes:
            return None

        routes.sort(key=lambda route: len(route))

        tmp_route = unroll_route(routes[0], pace)

        if len(self.floorplans) == 1:
            route = [(r, starting_floor_number) for r in tmp_route]
        else:
            route = [((r[0], r[1]), r[2]) for r in tmp_route]  # type: ignore

        return route

    def get_valid_multifloor_exit_nodes(
        self, location: int, floor_number: int
    ) -> List[Tuple[int, int, int]]:
        """
        Find list of exit coords that corresponds to a valid node in the
        navigation network.

        :param location: index of the space where the agent is currently
                located.
        :type location: int
        :param floor_number: Index of the floor number.
        :type floor_number: int
        :return: List of exit coords as xy and floor number.
        :rtype: List[Tuple[int, int, int]]
        """

        if isinstance(location, tuple):
            exit_nodes = [(location[0], location[1], floor_number)]
        else:
            exit_coords = self.floorplans[floor_number].get_room_exit_coords(
                location
            )
            if exit_coords is None:
                LOG.error("No exit from this room. Check the navnet")
                return []
            exit_nodes = [
                (coor[0], coor[1], floor_number) for coor in exit_coords
            ]

        valid_exit_nodes = [
            node
            for node in exit_nodes
            if self.multifloor_navnet.has_node(node)
            and len(self.multifloor_navnet.edges(node)) >= 1
        ]
        if not valid_exit_nodes:
            if isinstance(location, int):
                loc_name = self.floorplans[floor_number].spaces[location].id
            else:
                loc_name = location
            LOG.error(
                "Exit coordinates not in navnet or disconnected: %s",
                str(loc_name),
            )

        return valid_exit_nodes

    def get_valid_single_floor_exit_nodes(
        self, location: Union[int, tuple], floor_number: int
    ) -> List[Union[Tuple[int, int], Tuple[int, int, int]]]:
        """
        Find list of exit coords that corresponds to a valid node in the
        navigation network.

        :param location: index of the space where agent is located.
        :type location: int
        :param floor_number: index of floor number.
        :type floor_number: int
        :return: List of exit coordinates.
        :rtype: List[Tuple[int,int]]
        """

        if isinstance(location, tuple):
            exit_nodes = [(location[0], location[1])]
        else:
            exit_coords = self.floorplans[floor_number].get_room_exit_coords(
                location
            )
            if exit_coords is None:
                LOG.error("No exit from this room. Check the navnet")
                return []
            exit_nodes = [(coor[0], coor[1]) for coor in exit_coords]

        valid_exit_nodes: List[
            Union[Tuple[int, int], Tuple[int, int, int]]
        ] = [
            node
            for node in exit_nodes
            if self.navnet_per_floor[floor_number].has_node(node)
            and len(self.navnet_per_floor[floor_number].edges(node)) >= 1
        ]

        if not valid_exit_nodes:
            if isinstance(location, int):
                loc_name = self.floorplans[floor_number].spaces[location].id
            else:
                loc_name = location
            LOG.error(
                "Exit coordinates not in navnet or disconnected: %s",
                str(loc_name),
            )

        return valid_exit_nodes

    def get_best_possible_routes_multifloor(
        self,
        starting_location: int,
        starting_floor_number: int,
        destination: int,
        destination_floor_number: int,
    ) -> List[List[Union[Tuple[int, int], Tuple[int, int, int]]]]:
        """
        Get list of valid routes between a starting space and a destination
        space in the current multifloor facility.

        :param starting_location: index of the starting space.
        :type starting_location: int
        :param starting_floor_number: index of the starting floor.
        :type starting_floor_number: int
        :param destination: index of the destination space.
        :type destination: int
        :param destination_floor_number: index of the destination floor.
        :type destination_floor_number: int
        :return: list of valid routes.
        :rtype: List[List[Tuple[int, int, int]]]
        """
        # Start node
        starting_nodes = self.get_valid_multifloor_exit_nodes(
            starting_location, starting_floor_number
        )

        # End node
        dest_nodes = self.get_valid_multifloor_exit_nodes(
            destination, destination_floor_number
        )

        # Get possible routes
        valid_routes = []
        for s_node, e_node in product(starting_nodes, dest_nodes):

            try:
                route = nx.astar_path(self.multifloor_navnet, s_node, e_node)
                valid_routes.append(route)
            except Exception as e:
                LOG.exception("Here is the exception: %s", e)
                LOG.warning(
                    "No route between: %s, %s", starting_location, destination
                )

        return valid_routes

    def get_best_possible_routes_same_floor(
        self, floor_number: int, current_location: int, destination: int
    ) -> List[List[Union[Tuple[int, int], Tuple[int, int, int]]]]:
        """
        Find list of possible routes between two locations on the same floor in
        this facility.

        :param floor_number: index of the floor.
        :type floor_number: int
        :param current_location: index of the starting space.
        :type current_location: int
        :param destination: index of the destination space.
        :type destination: int
        :return: list of valid routes between the two spaces.
        :rtype: List[List[Tuple[int, int, int]]]
        """

        # Start node
        starting_nodes = self.get_valid_single_floor_exit_nodes(
            current_location, floor_number
        )

        # End node
        dest_nodes = self.get_valid_single_floor_exit_nodes(
            destination, floor_number
        )

        # Get possible routes
        valid_routes = []
        for s_node, e_node in product(starting_nodes, dest_nodes):

            try:
                route = nx.astar_path(
                    self.navnet_per_floor[floor_number], s_node, e_node
                )
                valid_routes.append(route)
            except Exception as e:
                LOG.exception("Here is the exception: %s", e)
                LOG.warning(
                    "No route between: %s, %s", current_location, destination
                )

        return valid_routes


def remove_unnecessary_coords(
    route: List[Union[Tuple[int, int], Tuple[int, int, int]]]
) -> List[Union[Tuple[int, int], Tuple[int, int, int]]]:
    """
    Inspect a route given by a set of coordinates and remove any intermediate
    coords that's collinear with its two neighbors.

    [extended_summary]

    :param route: List of tuples of x, y coordinates
    :type route: List[Tuple[int, int]]
    :return: Trimmed down list of coordinates.
    :rtype: List[Tuple[int, int]]
    """

    while True:
        index_of_coords_to_delete = None
        for i in range(1, len(route) - 1):
            pos = route[i]
            if len(pos) == 3 and (
                route[i - 1][2] != pos[2]  # type: ignore
                or pos[2] != route[i + 1][2]  # type: ignore
            ):  # pos can have a length of 3
                continue
            # Check if this point and the points before and after are collinear
            test_line = Line(
                start=complex(route[i - 1][0], route[i - 1][1]),
                end=complex(route[i + 1][0], route[i + 1][1]),
            )
            test_point = Point(x=pos[0], y=pos[1])
            if gsu.is_point_on_line(test_line, test_point, tol=1e-3):
                index_of_coords_to_delete = i
                break
        if index_of_coords_to_delete is not None:
            del route[index_of_coords_to_delete]
        else:
            break

    return route


def unroll_route(
    route: List[Union[Tuple[int, int], Tuple[int, int, int]]], pace: float
) -> List[Union[Tuple[int, int], Tuple[int, int, int]]]:
    """
    Use the given pace to find intermediate coordinates between each
    pair of nodes in this route.

    Note that currently the agent is required to pass through all notable
    points (e.g. turns at intersections)

    :param route: initial route with only notable coordinates.
    :type route: List[Union[Tuple[int, int], Tuple[int, int, int]]]
    :param pace: The desired pace in units of [dist/time]
    :type pace: float
    :return: list of all coordinates required to navigate this route at the
            desired pace.
    :rtype: List[Union[Tuple[int, int], Tuple[int, int, int]]]
    """

    if route is None:
        raise ValueError("Cannot unroll. Route is None.")

    route = remove_unnecessary_coords(route)
    full_route = [route[0]]

    for i, pos in enumerate(route[1:]):  # Look back and unroll

        current_x, current_y = pos[0], pos[1]
        last_x, last_y = route[i][0], route[i][1]

        # Check if this is between 2 floors
        if len(pos) == 3 and pos[2] != route[i][2]:  # type: ignore
            full_route.append(pos)
            continue

        Dx = current_x - last_x
        Dy = current_y - last_y

        n_intermediate_steps = (
            max(int(abs(Dx) * 1.0 / pace), int(abs(Dy) * 1.0 / pace)) + 1
        )
        if n_intermediate_steps > 1:

            dx = int(round(Dx * 1.0 / n_intermediate_steps))
            dy = int(round(Dy * 1.0 / n_intermediate_steps))

            for step in range(1, n_intermediate_steps - 1):
                if len(pos) == 2:
                    new_pos = (last_x + step * dx, last_y + step * dy)
                else:
                    new_pos = (
                        last_x + step * dx,  # type: ignore
                        last_y + step * dy,
                        pos[2],  # type: ignore
                    )
                full_route.append(new_pos)

        full_route.append(pos)

    return full_route
