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
import pickle

import networkx as nx
from svgpathtools import Line

import citam.engine.geometry_and_svg_utils as gsu
import citam.engine.storage_utils as su
from citam.engine.constants import (
    ONEWAY_TRAFFIC_NEGATIVE_DIRECTION,
    ONEWAY_TRAFFIC_POSITIVE_DIRECTION,
    TWO_WAY_TRAFFIC,
)
from citam.engine.point import Point

LOG = logging.getLogger(__name__)


class Navigation:
    def __init__(
        self,
        floorplans,
        facility_name,
        traffic_policy,
        multifloor_type="naming",
    ):

        super().__init__()

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
            navnet = self.load_floor_navnet(floorplan_directory)
            self.navnet_per_floor.append(navnet)

            # Load oneway network
            if self.traffic_policy is not None and self.traffic_policy != []:
                LOG.info("Loading oneway network...")
                oneway_net = self.load_floor_oneway_net(floorplan_directory)
                self.oneway_network_per_floor.append(oneway_net)

            # Load hallways graph
            LOG.info("Loading hallway graph for floor...")
            hg = self.load_hallway_graph(floorplan_directory)
            self.hallways_graph_per_floor.append(hg)

        if len(self.floorplans) > 1:
            self.create_multifloor_navnet()

        self.apply_traffic_policy()

    def load_hallway_graph(self, floorplan_directory):
        """Load the hallway graph"""
        hg = None
        floor_hallway_graph_file = os.path.join(
            floorplan_directory, "hallways_graph.pkl"
        )
        if os.path.isfile(floor_hallway_graph_file):
            with open(floor_hallway_graph_file, "rb") as f:
                hg = pickle.load(f)
            LOG.info("Success!")
        else:
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                floor_hallway_graph_file,
            )

        return hg

    def load_floor_oneway_net(self, floorplan_directory):
        """Load the oneway network"""
        oneway_net = None
        oneway_net_file = os.path.join(
            floorplan_directory, "oneway_network.pkl"
        )
        if os.path.isfile(oneway_net_file):
            with open(oneway_net_file, "rb") as f:
                oneway_net = pickle.load(f)
            LOG.info("Success!")
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), oneway_net_file
            )
        return oneway_net

    def load_floor_navnet(self, floorplan_directory):
        """Load the navigation network."""
        navnet = None
        floor_navnet_file = os.path.join(floorplan_directory, "routes.pkl")
        if os.path.isfile(floor_navnet_file):
            with open(floor_navnet_file, "rb") as f:
                navnet = pickle.load(f)
            LOG.info("Success!")
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), floor_navnet_file
            )
        return navnet

    def get_corresponding_vertical_space(self, ref_space, dest_floor):
        """Given a reference space and a destination floor, find the space
        on the destination floor that lies in the same xy position as the
        reference space. Mostly used for stairs and elevators.

        :param Space ref_space: the reference space
        :param int dest_floor: id of the destination floor
        :return: dest_space_id
        :return: dest_space
        :rtype: (int, Space)
        """
        # TODO: Add regex as another method.
        dest_space = None
        dest_space_id = None

        if self.multifloor_type == "naming":
            name1 = ref_space.unique_name
            name2 = name1[0] + str(dest_floor + 1) + name1[2:]

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
                "Unknown method : ' + str(method) +'Expected: naming or 'xy'"
            )

        return dest_space_id, dest_space

    def add_vertical_edges(self, floor_number1, floor_number2):
        """Create new edges in the navigation network to connect vertical
        spaces allowing multifloor navigation. If there are more than 2 floors
        in the facility, this function should be used toconnect only
        adjacent floors.

        This function finds all the vertical spaces in the starting floor and
        finds if there is a corresponding space on the destination floor in
        which case edges are added between them.

        Parameters:
        -----------
        floor_number1: int
            Integer ID of the first floor
        floor_number2: int
            Integer ID of the second floor

        Returns
        --------
        int
            Number of vertical spaces connected
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

            # add edges between room the exit coords of the vertical spaces
            # (TODO: maybe create edges between an xy coords inside rooms?)
            node1 = (coords1[0], coords1[1], floor_number1)
            coords2 = self.floorplans[floor_number2].get_room_exit_coords(j)
            if coords2 is None:
                continue
            node2 = (coords2[0], coords2[1], floor_number2)

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
        """Use vertical spaces to combine multiple floor navnets into a global
        navnet.

        Each node in the global navnet is of the form (x, y, f) where f is the
        floor number.

        Parameters
        -----------
        No parameters

        Returns
        --------

        """
        print("Combining navigation networks...")
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
        """Remove edges that should not exist based on user traffic policy
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
        policy,
        navnet,
        oneway_net,
        navnet_type="singlefloor",
        floor_number=0,
    ):
        """Find edge of interest from navnet and keep only the ones that
        match the desired traffic pattern.
        """
        LOG.info("Applying this policy {%s}: ", policy)
        print(policy)
        if policy["direction"] == TWO_WAY_TRAFFIC:
            return

        if (
            policy["direction"] != ONEWAY_TRAFFIC_NEGATIVE_DIRECTION
            and policy["direction"] != ONEWAY_TRAFFIC_POSITIVE_DIRECTION
        ):
            LOG.fatal(
                "Unknown direction in traffic policy input {%s}",
                policy["direction"],
            )
            LOG.info(
                "Supported values are {%d}, {%d} and {%d}. See docs.",
                ONEWAY_TRAFFIC_POSITIVE_DIRECTION,
                ONEWAY_TRAFFIC_NEGATIVE_DIRECTION,
                TWO_WAY_TRAFFIC,
            )
            raise ValueError()

        # Find edges of interest and remove them from navnet if they don't
        # match the desired traffic direction
        for edge in oneway_net.edges(data=True):
            if str(edge[2]["id"]) == str(policy["segment_id"]):
                all_coords = [edge[0], edge[1]] + edge[2]["inter_points"]
                n_coords = len(all_coords)
                for i in range(n_coords - 1):
                    for j in range(i, n_coords):
                        if navnet_type == "singlefloor":
                            test_edge1 = (all_coords[i], all_coords[j])
                            test_edge2 = (all_coords[j], all_coords[i])
                        else:
                            test_edge1 = (
                                all_coords[i],
                                all_coords[j],
                                floor_number,
                            )
                            test_edge2 = (
                                all_coords[j],
                                all_coords[i],
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
                break

        return

    def is_edge_matching_direction(self, edge, desired_direction):
        """Verify if edge direction matches desired direction.

        Use the start and end points to compute a direction angle alpha
        with respect to the positive x-axis. The positive direction corresponds
        to 0 <= alpha <= 90 or 270 > alpha >= 360. The negative direction is
        the other half of the possible angles.
        """
        # Compute angle
        dx = edge[1][0] - edge[0][0]
        dy = edge[1][1] - edge[0][1]
        alpha = math.degrees(math.atan2(dy, dx))

        if (alpha >= 0 and alpha <= 90) or (alpha > 180 and alpha <= 360):
            edge_direction = ONEWAY_TRAFFIC_POSITIVE_DIRECTION
        else:
            edge_direction = ONEWAY_TRAFFIC_NEGATIVE_DIRECTION

        return desired_direction == edge_direction

    def get_route(
        self,
        starting_location,
        starting_floor_number,
        destination,
        destination_floor_number,
        pace,
    ):
        """Get the shortest path between 2 spaces in the floorplans.

        Parameters
        -----------
        starting_location: int
            Integer ID of the space where the agent is currently located
        starting_floor_number: int
            Integer ID of the floor where the agent is currently located
        destination: int
            Integer ID of the the location where the agent is going
        destination_floor_number: int
            Integer ID of the floor number of the destination

        Results
        --------
        list
            List of all the connected nodes forming the shortest path
            between the given starting location and destination
        """
        if len(self.floorplans) == 1:
            route = self.get_route_same_floor(
                starting_floor_number, starting_location, destination
            )
            tmp_route = unroll_route(route, pace)
            if tmp_route is None:
                return None
            route = [[r, starting_floor_number] for r in tmp_route]
        else:
            route = self.get_multifloor_route(
                starting_location,
                starting_floor_number,
                destination,
                destination_floor_number,
            )
            tmp_route = unroll_route(route, pace)
            if tmp_route is None:
                return None
            route = [[(r[0], r[1]), r[2]] for r in tmp_route]

        return route

    def get_multifloor_route(
        self,
        starting_location,
        starting_floor_number,
        destination,
        destination_floor_number,
    ):

        # Start node
        if isinstance(starting_location, tuple):
            start_node = (
                starting_location[0],
                starting_location[1],
                starting_floor_number,
            )
        else:
            coords = self.floorplans[
                starting_floor_number
            ].get_room_exit_coords(starting_location)
            if coords is None:
                LOG.error("No exit from this room. Check the navnet")
                return None
            start_node = (coords[0], coords[1], starting_floor_number)
        if self.multifloor_navnet.has_node(start_node):
            n_edges = self.multifloor_navnet.edges(start_node)
            if n_edges == 1:
                LOG.error("No exit from this room. Check the navnet")
                return None
        else:
            LOG.error("Start coordinates not in navnet: %s", str(start_node))

        # End node
        if isinstance(destination, tuple):
            end_node = (
                destination[0],
                destination[1],
                destination_floor_number,
            )
        else:
            coords = self.floorplans[
                destination_floor_number
            ].get_room_exit_coords(destination)
            if coords is None:
                LOG.error("No exit from this room. Check the navnet")
                return None
            end_node = (coords[0], coords[1], destination_floor_number)

        if self.multifloor_navnet.has_node(end_node):
            n_edges = self.multifloor_navnet.edges(end_node)
            if n_edges == 1:
                LOG.error("No exit from this room. Check the navnet")
                return None
        else:
            LOG.error("Dest coordinates not in navnet: %s", str(end_node))
            return None

        # Get route
        try:
            route = nx.astar_path(self.multifloor_navnet, start_node, end_node)
        except Exception as e:
            LOG.exception("Here is the exception: %s", e)
            LOG.error(
                "No route between: %s, %s", starting_location, destination
            )
            return None

        return route

    def get_route_same_floor(
        self, floor_number, current_location, destination
    ):
        """Find the best route between two locations on the same floor.

        Parameters
        -----------
        floor_number : int
        current_location : int
        destination : int

        Returns
        --------
        route : list of (x, y) positions
        """
        # Pace expected in unit length of the floormap per simulation timestep
        floorplan = self.floorplans[floor_number]

        if isinstance(current_location, tuple):
            start_coords = current_location
        else:
            start_coords = floorplan.get_room_exit_coords(current_location)
            if self.navnet_per_floor[floor_number].has_node(start_coords):
                n_edges = self.navnet_per_floor[floor_number].edges(
                    start_coords
                )
                if n_edges == 1:
                    LOG.error("No exit from this room. Check the navnet")
                    return None

        if isinstance(destination, tuple):
            end_coords = destination
        else:
            end_coords = floorplan.get_room_exit_coords(destination)
            if self.navnet_per_floor[floor_number].has_node(end_coords):
                n_edges = self.navnet_per_floor[floor_number].edges(end_coords)
                if n_edges == 1:
                    LOG.error("No exit from this room. Check the navnet")
                    return None

        if start_coords is None or end_coords is None:
            return None

        if not self.navnet_per_floor[floor_number].has_node(start_coords):
            LOG.error("Start coordinates not in nav network: %s", start_coords)
            return None

        if not self.navnet_per_floor[floor_number].has_node(end_coords):
            if not (isinstance(destination, tuple)):
                dest_space = self.floorplans[floor_number].spaces[destination]
                dest_name = dest_space.unique_name
                # This should never happen but for now, here is a workaround.
            else:
                dest_name = destination
            LOG.error(
                "End coordinates not in nav network: %s. Destination %s",
                end_coords,
                dest_name,
            )
            return None

        try:
            route = nx.astar_path(
                self.navnet_per_floor[floor_number], start_coords, end_coords
            )
        except Exception as e:
            LOG.exception("Here is the exception: %s", str(e))
            LOG.info(
                "No route between: (%s, %s)", current_location, destination
            )
            return None

        return route


def remove_unnecessary_coords(route):
    """
    Inspect a route given by a set of coordinates and remove any intermediate
    coords that's collinear with its two neighbors.

    :param list route: List of tuples of x, y coordinates
    :return: Trimmed down list of coords
    :rtype: list[(int, int)]
    """
    while True:
        index_of_coords_to_delete = None
        for i in range(1, len(route)-1):
            pos = route[i]
            if len(pos) == 3 and (
                route[i - 1][2] != pos[2] or pos[2] != route[i + 1][2]
            ):
                continue
            # Check if this point and the points before and after are collinear
            test_line = Line(
                start=complex(route[i - 1][0], route[i - 1][1]),
                end=complex(route[i + 1][0], route[i + 1][1]),
            )
            test_point = Point(x=pos[0], y=pos[1])
            if gsu.is_point_on_line(test_line, test_point, tol=1e-1):
                index_of_coords_to_delete = i
                break
        if index_of_coords_to_delete is not None:
            del route[index_of_coords_to_delete]
        else:
            break

    return route


def unroll_route(route, pace):
    """Use the given pace to find intermediate coordinates between each
    pair of nodes in this route.
    """
    if route is None:
        return None

    route = remove_unnecessary_coords(route)
    full_route = [route[0]]

    for i, pos in enumerate(route[1:]):  # Look back and unroll

        current_x, current_y = pos[0], pos[1]
        last_x, last_y = route[i][0], route[i][1]

        # Check if this is between 2 floors
        if len(pos) == 3 and pos[2] != route[i][2]:
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
                    new_pos = (last_x + step * dx, last_y + step * dy, pos[2])
                full_route.append(new_pos)

        full_route.append(pos)

    return full_route
