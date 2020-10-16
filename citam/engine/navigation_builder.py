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
from typing import Tuple

import networkx as nx
import progressbar as pb
from svgpathtools import Line, svg2paths

import citam.engine.basic_visualization as bv
import citam.engine.floorplan_utils as fu
import citam.engine.geometry_and_svg_utils as gsu
from citam.engine.door import Door
from citam.engine.point import Point

LOG = logging.getLogger(__name__)


class NavigationBuilder:
    """Create the navigation network (navnet) for a given floorplan.

    Each node in the navigation network is a notable xy coordinate in the
    floorplan corresponding to entrances to various spaces and intersections
    between navigation segments. The correspondence between nodes and
    actual locations is handled at the floorplan and navigation (see the
    navigation class) level.

    Parameters
    -----------
    floorplan: Floorplan
        The floorplan to build the navigation network for
    add_all_nav_points: bool
        Whether to add all points from navigation segments to the network or
        just the endpoints.  In both cases the final simplification process
        will remove any unnecessary nodes. The tradeoff is how easy it is to
        find intersections between segments. If all points are added,
        intersections are found almost for free (nodes with more than 2 edges)
        but the simplification process takes longer. If only the endpoints are
        added, an iteration over pairs of nav segments that fall within the
        same space is required.
    """

    def __init__(self, current_floorplan, add_all_nav_points=False):
        """This is the init doc"""
        super().__init__()

        self.current_floorplan = current_floorplan
        self.add_all_nav_points = add_all_nav_points

        self.floor_navnet = nx.Graph()
        self.hallways_graph = nx.Graph()

        # Keys will be space unique names and each entry will be a list of nav
        # segments where each segment is a tuple of the 2 endpoints
        self.space_nav_segments = {}

        # self.current_space = None  # for testing and debugging purposes

        # To avoid parallel nav segments!
        self.excluded_doors = []

        return

    def build(self):
        """Build the navigation network (navnet) for a given floorplan.

        The navigation network is created by adding a navigation segment
        at the center of each aisle and then adding navigation segments
        from each side of a door in a perpendicular direction.

        Parameters
        -----------

        Returns
        --------
        None

        """

        LOG.info("Creating nav segments for each aisle...")
        pbar = pb.ProgressBar(max_value=len(self.current_floorplan.spaces))
        for i, space in enumerate(self.current_floorplan.spaces):
            pbar.update(i)
            if space.is_space_a_hallway():
                valid_boundaries = space.boundaries
                # self._find_valid_boundaries(space)
                aisles = fu.find_aisles(
                    space, valid_boundaries, no_repeat=False
                )
                for aisle in aisles:
                    if not self._aisle_has_nav_segment(aisle, space):
                        # self.current_space = space
                        self.create_nav_segment_for_aisle(aisle)

        pbar = pb.ProgressBar(max_value=len(self.current_floorplan.doors))
        LOG.info("Processing doors for each space...")
        for i, door in enumerate(self.current_floorplan.doors):
            pbar.update(i)
            self.floor_navnet.add_node(door.midpoint_coords, node_type="door")
            if door in self.excluded_doors:
                # Add short segment between current coords for door and the
                # midpoint coord
                if not door.is_intersect_and_midpoint_same():
                    self.floor_navnet.add_node(
                        door.intersect_coords, node_type="door"
                    )
                    self.floor_navnet.add_edge(
                        door.intersect_coords,
                        door.midpoint_coords,
                        half_width=1.0,
                    )
                continue
            # Add mid-point of door path to navnet as a door node
            door_width = door.path.length()
            door_normal = door.path.normal(0.5)
            segments, seg_spaces = self.compute_nav_segments(
                door.midpoint,
                door_normal,
                door_width,
                stop_at_existing_segments=True,
            )
            if len(segments) == 0:
                LOG.warning("No nav segments found. This is not typical.")
                LOG.info("Door is: %s", door)
            self._add_spaces_to_hallway_graph(seg_spaces)
            self._update_navnet(segments, seg_spaces, door_width)

        # Simplify nav network by removing unncesssary edges and nodes
        LOG.info("Removing unnecessary nodes from nav network...")
        self.simplify_navigation_network()

        # Make sure no intersection was missed, in case they happen between
        # grid points
        if self.add_all_nav_points:
            for space in list(set(self.current_floorplan.spaces)):
                self.find_intersections_in_space(space)

        # Ensure no nav path crosses a special wall
        LOG.info("Make sure nav paths do not cross any walls...")
        self.sanitize_graph()

        # Label all intersection nodes accordingly
        nodes = list(self.floor_navnet.nodes())
        for node in nodes:
            nneigh = list(self.floor_navnet.neighbors(node))
            if len(nneigh) > 2:
                self.floor_navnet.nodes[node]["node_type"] = "intersection"

        # Convert to directed graph
        self.floor_navnet = self.floor_navnet.to_directed()

        return

    def _update_navnet(self, segments, seg_spaces, width):
        # Add segments to navnet
        self._add_segments_to_navnet(segments, seg_spaces, width)

        # Add segments to space
        for seg, seg_space in zip(segments, seg_spaces):
            full_line = [seg[0], seg[-1]]
            if seg_space.unique_name in self.space_nav_segments:
                self.space_nav_segments[seg_space.unique_name].append(
                    full_line
                )
            else:
                self.space_nav_segments[seg_space.unique_name] = [full_line]

        # Find nav intersections within spaces
        if not self.add_all_nav_points:
            for seg_space in list(set(seg_spaces)):
                self.find_intersections_in_space(seg_space)
                self.find_and_remove_overlaps(seg_space)
                # TODO: Also look for overlapping segments and merge them while
                # keeping all existing intersections. Would also be great to
                # merge parallel segments as well
        return

    def _aisle_has_nav_segment(self, aisle, space):
        """Check if aisle already has a navigation segment.

        Parameters
        -----------
        aisle: tuple
            Tuple of wall 1 and wall 2

        Returns
        --------
        bool
            Whether a nav segment was found or not
        """
        if space.unique_name not in self.space_nav_segments:
            return False

        # Perpendicular vector between the two walls
        V_perp = gsu.calculate_perpendicular_vector(aisle[0], aisle[1])

        # If all of these lead to intersection with a nav seg, we are good
        test_points = [0.2, 0.8]
        tot_intersects = 0

        for seg in self.space_nav_segments[space.unique_name]:
            line2 = Line(
                start=seg[0].complex_coords, end=seg[1].complex_coords
            )
            if line2.length() <= 1.0:
                continue
            for pos in test_points:
                complex_point1 = aisle[0].point(pos)
                point1 = Point(
                    x=round(complex_point1.real), y=round(complex_point1.imag)
                )
                point2 = Point(
                    x=round(point1.x + V_perp[0]),
                    y=round(point1.y + V_perp[1]),
                )
                line1 = Line(
                    start=point1.complex_coords, end=point2.complex_coords
                )
                if line1.length() <= 1.0:
                    continue
                if len(line1.intersect(line2)) > 0:
                    tot_intersects += 1

            if tot_intersects >= len(test_points):
                return True

        return False

    def _find_valid_boundaries(self, space):
        """Iterate over boundary walls of a space and returns only the
         ones that are not between two hallways.

        Parameters
        -----------
        space: Space
            Space of interest

        Returns
        --------
        list
            List of lines representing valid boundaries
        """
        valid_boundaries = []
        for wall in space.boundaries:
            if wall.length() <= 1.0:
                continue
            mid_normal = wall.normal(0.5)
            dx = mid_normal.real
            dy = mid_normal.imag
            mid_point = wall.point(0.5)
            test_point1 = Point(
                x=round(mid_point.real + dx), y=round(mid_point.imag + dy)
            )
            space1, _ = self._find_location_of_point(test_point1)
            if space1 is None:
                valid_boundaries.append(wall)
                continue

            test_point2 = Point(
                x=round(mid_point.real - 1.0 * dx),
                y=round(mid_point.imag - 1.0 * dy),
            )
            space2, _ = self._find_location_of_point(test_point2)
            if space2 is None:
                valid_boundaries.append(wall)
                continue

            if (
                not space1.is_space_a_hallway()
                or not space2.is_space_a_hallway()
            ):
                valid_boundaries.append(wall)

        return valid_boundaries

    def create_nav_segment_for_aisle(self, aisle: tuple):
        """Create navigation segements (edges in the navnet) to handle
        circulation in this aisle.

        Parameters
        -----------
        aisle: tuple
            Tuple with the first and second wall

        Returns
        --------
        None

        """
        # use one of the walls to find the direction vector
        wall1 = aisle[0]
        p1 = Point(x=round(wall1.start.real), y=round(wall1.start.imag))
        q1 = Point(x=round(wall1.end.real), y=round(wall1.end.imag))
        L = wall1.length()
        direction_vector = complex((q1.x - p1.x) / L, (q1.y - p1.y) / L)

        center_point, width = fu.get_aisle_center_point_and_width(aisle)
        segments, seg_spaces = self.compute_nav_segments(
            center_point, direction_vector, width
        )
        self._add_spaces_to_hallway_graph(seg_spaces)
        self._update_navnet(segments, seg_spaces, width)

        return

    def _find_location_of_point(self, point):
        """Find the space inside which this point is located.

        Parameters
        -----------
        point: Point
            The point of interest

        Returns
        --------
        Space:
            Space object where the point is located (None if not found)

        int:
            index of the space where the point is located (None if not found)

        """

        for i, space in enumerate(self.current_floorplan.spaces):
            if space.is_point_inside_space(point):
                return space, i

        return None, None

    def _is_point_on_boundaries(self, point):
        """Check if point falls on any boundary and return list of
        corresponding spaces. If only one space, then this is an exterior
        boundary.

        Parameters
        -----------
        point: Point

        Returns
        --------
        list:
            List of spaces
        """
        boundary_spaces = []
        for i, space in enumerate(self.current_floorplan.spaces):
            if space.is_point_on_space_boundaries(point):
                boundary_spaces.append(space)

        return boundary_spaces

    def _add_segments_to_navnet(self, segments, seg_spaces, width):
        """Add a collection of nodes and edges to the navigation network

        Each point in each segment is added as a node to the nav network
        and a connection (edge) is created between each successive pair of
        points.

        Parameters
        -----------
        segments: list of list<Point>
            The list of segments to add to the navigation graph (navnet)

        Returns
        --------
        None

        """
        for i, seg in enumerate(segments):
            if len(seg) in [0, 1]:
                continue

            coords1 = (seg[0].x, seg[0].y)
            self.floor_navnet.add_node(coords1, node_type="step")
            if self.add_all_nav_points:
                for point in seg[1:]:
                    coords2 = (point.x, point.y)
                    self.floor_navnet.add_node(coords2, node_type="step")
                    self.floor_navnet.add_edge(
                        coords1, coords2, half_width=round(width / 2)
                    )
                    coords1 = coords2

            else:
                coords2 = (seg[-1].x, seg[-1].y)
                self.floor_navnet.add_node(coords2, node_type="step")
                if coords1 != coords2:
                    self.floor_navnet.add_edge(
                        coords1, coords2, half_width=round(width / 2)
                    )

        return

    def _add_spaces_to_hallway_graph(self, spaces):
        """Add hallways to the hallway graph

        The hallway graph keeps track of which hallway is accessible from
        which hallway. A connection is created between each space given
        as input.

        Parameters
        -----------
        spaces: list of Space
            The list of space objects to add to the graph.

        Returns
        --------
        None

        """

        if len(spaces) == 0:
            return
        if self.hallways_graph is None:
            return

        old_space = spaces[0]
        if old_space is not None and old_space.is_space_a_hallway():
            self.hallways_graph.add_node(old_space.unique_name)

        for current_space in spaces[1:]:
            if (
                old_space != current_space
                and current_space is not None
                and old_space is not None
                and (
                    old_space.is_space_a_hallway()
                    and current_space.is_space_a_hallway()
                )
            ):

                self.hallways_graph.add_edge(
                    old_space.unique_name, current_space.unique_name
                )
            old_space = current_space

        return

    def find_door_intersect(self, test_line) -> Tuple[tuple, Door]:
        """Check if the given line intersects with a door."""
        coords = None
        door_found = None
        for door in self.current_floorplan.doors:
            intersects = test_line.intersect(door.path)
            if len(intersects) > 0:
                t1 = intersects[0][0]
                if t1 == 0.0:
                    continue
                door_intersect = test_line.point(t1)
                coords = (
                    round(door_intersect.real),
                    round(door_intersect.imag),
                )
                door_found = door
                break

        return coords, door_found

    def compute_nav_segments(
        self,
        first_point,
        direction_vector,
        width,
        stop_at_existing_segments=False,
    ):
        """Compute navigation segments from a given point and direction.
        2 segments are created from the starting point going in opposite
        directions.

        A navigation segment corresponds to an edge in the navigation graph
        connecting 2 nodes (usually doors or walls marking the end of the
        navigation segment).

        Parameters
        -----------
        first_point: Point
            The initial point from which to start the segments

        direction_vector: complex
            Vector indicating the directions (positive and negative)
            of the segments.

        width: float
            The width to assign to the edges corresponding to the segments
            created in the navigation graph

        stop_at_existing_segments: true
            Whether to stop if the segment crosses an existing navigation
            segment in the navnet or not

        Returns
        --------
        (segments, segment_spaces): tuple of 2 lists

        """
        segments = []
        segment_spaces = []

        dx = direction_vector.real
        dy = direction_vector.imag

        for direction in [-1, 1]:
            new_point = first_point
            segments.append([new_point])
            current_space, _ = self._find_location_of_point(new_point)

            if current_space is None:
                boundary_spaces = self._is_point_on_boundaries(new_point)
                if len(boundary_spaces) == 0:
                    raise ValueError(
                        "Unable to compute a nav segment from %s",
                        str(new_point),
                    )
                elif len(boundary_spaces) == 1:
                    LOG.info(
                        "{%s} on space boundary. Is it an entrance?", new_point
                    )
                    current_space = boundary_spaces[0]
                else:
                    test_point = Point(
                        x=round(new_point.x + direction * dx),
                        y=round(new_point.y + direction * dy),
                    )
                    current_space, _ = self._find_location_of_point(test_point)
                    if current_space is None:
                        raise ValueError(
                            "Unable to compute a nav segment from %s",
                            str(new_point),
                        )

            segment_spaces.append(current_space)

            wall_found = False
            while not wall_found:
                # move one point in the given direction
                new_point = Point(
                    x=round(new_point.x + direction * dx),
                    y=round(new_point.y + direction * dy),
                )

                if current_space.is_point_inside_space(new_point):
                    if direction == -1:
                        segments[-1] = [new_point] + segments[-1]
                    else:
                        segments[-1].append(new_point)
                else:
                    new_space, _ = self._find_location_of_point(new_point)
                    # Check if this is a wall, in which case we end the
                    # nav segment
                    test_line = Line(
                        start=first_point.complex_coords,
                        end=new_point.complex_coords,
                    )
                    # TODO: Change test_line to be the last segment!
                    for wall in self.current_floorplan.walls:
                        if (
                            wall.length() > 1
                            and len(test_line.intersect(wall)) > 0
                        ):
                            wall_found = True
                            break

                    if wall_found:
                        continue

                    if new_space is None:
                        boundary_spaces = self._is_point_on_boundaries(
                            new_point
                        )

                        if len(boundary_spaces) == 0:
                            wall_found = True  # Outside of the facility

                        if len(boundary_spaces) == 1:  # on exterior wall
                            coords, door = self.find_door_intersect(test_line)
                            if coords is None:  # There is no door here
                                wall_found = True

                    if not wall_found:
                        # Is this a door?
                        coords, door = self.find_door_intersect(test_line)
                        if coords is not None:
                            door.intersect_coords = coords
                            self.excluded_doors.append(door)

                        # We can keep adding point to segment
                        if direction == -1:
                            segments[-1] = [new_point] + segments[-1]
                        else:
                            segments[-1].append(new_point)
                        if new_space is not None:
                            current_space = new_space
                            segments.append([segments[-1][-1], new_point])
                            segment_spaces.append(current_space)

                if stop_at_existing_segments and self.floor_navnet.has_node(
                    (new_point.x, new_point.y)
                ):
                    break

        if len(segments) != len(segment_spaces):
            LOG.fatal("Number of segments should equal number of spaces")
            LOG.info(
                "We have: {%d} * {%d}", len(segments), len(segment_spaces)
            )
            quit()

        good_segments = []
        good_segment_spaces = []
        for seg, seg_space in zip(segments, segment_spaces):
            if len(seg) > 1:
                good_segments.append(seg)
                good_segment_spaces.append(seg_space)

        return good_segments, good_segment_spaces

    def sanitize_graph(self):
        """Make sure navigation paths do not cross any walls, including
        standalone walls.

        Parameters
        -----------

        Returns
        -------
        None

        """

        if len(self.current_floorplan.special_walls) == 0:
            return

        n_intersect = 0
        i = 0
        edges = list(self.floor_navnet.edges(data=True))

        pbar = pb.ProgressBar(max_value=len(edges))
        while i < len(edges):
            pbar.update(i)
            edge = edges[i]
            half_width = edge[2]["half_width"]
            p = Point(x=edge[0][0], y=edge[0][1])
            q = Point(x=edge[1][0], y=edge[1][1])
            path_line = Line(start=p.complex_coords, end=q.complex_coords)
            if path_line.length() <= 1:
                i += 1
                continue
            for wall in self.current_floorplan.special_walls:
                intersects = path_line.intersect(wall)
                if len(intersects) > 0:
                    intersection_point = path_line.point(intersects[0][0])
                    inter_coords = (
                        int(round(intersection_point.real)),
                        int(round(intersection_point.imag)),
                    )
                    self.floor_navnet.remove_edge(edge[0], edge[1])
                    if edge[0] != inter_coords:
                        dx = edge[0][0] - inter_coords[0]
                        dy = edge[0][1] - inter_coords[1]
                        L = (dx ** 2 + dy ** 2) ** 0.5
                        coords2 = (
                            inter_coords[0] + round(dx / L),
                            inter_coords[1] + round(dy / L),
                        )
                        self.floor_navnet.add_edge(
                            edge[0], coords2, half_width=half_width
                        )
                    # TODO: implement support for case when edge crosses
                    # multiple walls
                    #     new_edge = (edge[0], inter_coords,
                    #                 {'half_width': half_width})
                    #     # edges.append(new_edge)

                    if inter_coords != edge[1]:
                        dx = edge[1][0] - inter_coords[0]
                        dy = edge[1][1] - inter_coords[1]
                        L = (dx ** 2 + dy ** 2) ** 0.5
                        coords2 = (
                            inter_coords[0] + round(dx / L),
                            inter_coords[1] + round(dy / L),
                        )
                        self.floor_navnet.add_edge(
                            coords2, edge[1], half_width=half_width
                        )
                    # TODO: implement support for case case when edge crosses
                    # multiple walls
                    #     new_edge = (inter_coords, edge[1],
                    #                 {'half_width': half_width})
                    #     # edges.append(new_edge)

                    n_intersect += 1
            i += 1

        n_edges = self.floor_navnet.number_of_nodes()
        LOG.info("Number of intersections removed: %d", n_intersect)
        LOG.info("Number of edges: %d", n_edges)

        return

    def simplify_navigation_network(self):
        """Remove unnecessary edges and nodes in navigation network.

        A node is unnecessary if it only has 2 neighbors and they together
        form a straight line.

        Parameters
        ------------

        Returns
        --------
        None

        """

        if "is_simplified" in self.floor_navnet.graph:
            if self.floor_navnet.graph["is_simplified"]:
                return
        else:
            n_nodes = self.floor_navnet.number_of_nodes()
            LOG.info("Starting number of nodes: %d", n_nodes)
            n_edges = self.floor_navnet.number_of_edges()
            LOG.info("Starting number of edges: %d", n_edges)

            door_paths = [d.path for d in self.current_floorplan.doors]
            # for space in floorplan.spaces:
            #     door_paths += space.doors

            LOG.info("Number of doors: %d", len(door_paths))

            nodes_removed = 0
            completed = False
            while not completed:
                completed = True
                nodes = list(self.floor_navnet.nodes)
                pbar = pb.ProgressBar(max_value=len(nodes))
                for i, node in enumerate(nodes):
                    pbar.update(i)
                    remove_node = True
                    neighbors = list(self.floor_navnet.neighbors(node))
                    if len(neighbors) == 2:
                        # The nodes have to be on a straight line
                        test_line = Line(
                            start=complex(neighbors[0][0], neighbors[0][1]),
                            end=complex(neighbors[1][0], neighbors[1][1]),
                        )
                        test_point = Point(x=node[0], y=node[1])
                        if not gsu.is_point_on_line(
                            test_line, test_point, tol=1e-1
                        ):
                            remove_node = False
                        # Do not remove node if it belongs to a door path
                        p = Point(x=node[0], y=node[1])
                        for door_path in door_paths:
                            if gsu.is_point_on_line(door_path, p):
                                remove_node = False
                                break

                        if remove_node:
                            edges = self.floor_navnet.edges(node, data=True)
                            half_width = list(edges)[0][2]["half_width"]
                            self.floor_navnet.remove_node(node)
                            self.floor_navnet.add_edge(
                                neighbors[0],
                                neighbors[1],
                                half_width=half_width,
                            )
                            # self.floor_navnet.add_edge(neighbors[1],
                            #                            neighbors[0],
                            #                            half_width=half_width
                            #                            )
                            nodes_removed += 1
                            completed = False

            LOG.info("Number of nodes removed: %d", nodes_removed)
            n_nodes = self.floor_navnet.number_of_nodes()
            LOG.info("New number of nodes: %d", n_nodes)
            n_edges = self.floor_navnet.number_of_edges()
            LOG.info("New number of edges: %d", n_edges)
            self.floor_navnet.graph["is_simplified"] = True

        return

    def find_and_remove_overlaps(self, space):
        """Iterate over segments in this space, test for overlap and remove
        any.
        """

        return

    def find_intersections_in_space(self, space):
        """Iterate through all nav segment pairs in this space, and add
        any interesection found to navnet.

        An intersectin is when 2 nav segments cross each other.

        Parameters
        -----------
        space: Space
            The space of interest

        Returns
        --------
        None
        """

        key = space.unique_name
        if key not in self.space_nav_segments:
            return

        done = False
        while not done:
            done = True
            n_segments = len(self.space_nav_segments[key])
            exit_loop = False
            # if '198' in key:
            #     print('Getting ready to iterate over segments:\n')
            for i in range(n_segments - 1):
                for j in range(i + 1, n_segments):
                    seg1 = self.space_nav_segments[key][i]
                    seg2 = self.space_nav_segments[key][j]

                    if seg1 == seg2:
                        continue

                    point1 = seg1[0]
                    point2 = seg1[1]
                    point3 = seg2[0]
                    point4 = seg2[1]
                    coords1 = (point1.x, point1.y)
                    coords2 = (point2.x, point2.y)
                    coords3 = (point3.x, point3.y)
                    coords4 = (point4.x, point4.y)

                    intersect_coords = (
                        self.find_and_add_intersection_node_to_graph(
                            coords1, coords2, coords3, coords4
                        )
                    )
                    if intersect_coords is not None:
                        # update space seg
                        self.space_nav_segments[key].remove(seg1)
                        self.space_nav_segments[key].remove(seg2)
                        new_point = Point(
                            x=intersect_coords[0], y=intersect_coords[1]
                        )
                        for point in [point1, point2, point3, point4]:
                            if point != new_point:
                                new_segment = [point, new_point]
                                self.space_nav_segments[key].append(
                                    new_segment
                                )

                        exit_loop = True
                        break
                if exit_loop:
                    done = False
                    break

        return

    def find_and_add_intersection_node_to_graph(
        self, point1, point2, point3, point4
    ):
        """Given four points forming 2 lines, check if they intersect
        and if so add new node to graph and create new edges

        Parameters
        ----------
        point1: tuple of x, y coordinates
        point2: tuple of x, y coordinates
            Points 1 and 2 form the first line
        point3: tuple of x, y coordinates
        point4: tuple of x, y coordinates
            Poitns 3 and 4 form the second line

        Results
        --------
        tuple
            Interesect point in the form of (x,y) coordinates. Returns None if
            no interesect was found.
        """

        line1 = Line(
            start=complex(point1[0], point1[1]),
            end=complex(point2[0], point2[1]),
        )
        line2 = Line(
            start=complex(point3[0], point3[1]),
            end=complex(point4[0], point4[1]),
        )

        intersect_point = None
        intersects = line1.intersect(line2)
        if len(intersects) > 0:
            t1, t2 = intersects[0]
            if t1 in [0.0, 1.0] and t2 in [0, 1.0]:
                return None

            intersect_point = (
                round(line1.point(t1).real),
                round(line1.point(t1).imag),
            )

            self.floor_navnet.add_node(intersect_point)

            if self.floor_navnet.has_edge(point1, point2):
                edge1 = self.floor_navnet.get_edge_data(point1, point2)
                half_width1 = edge1["half_width"]
                self.floor_navnet.remove_edge(point1, point2)
            else:
                half_width1 = 1
            if self.floor_navnet.has_edge(point2, point1):
                self.floor_navnet.remove_edge(point2, point1)

            if self.floor_navnet.has_edge(point3, point4):
                edge2 = self.floor_navnet.get_edge_data(point3, point4)
                half_width2 = edge2["half_width"]
                self.floor_navnet.remove_edge(point3, point4)
            else:
                half_width2 = 1
            if self.floor_navnet.has_edge(point4, point3):
                self.floor_navnet.remove_edge(point4, point3)

            if point1 != intersect_point:
                self.floor_navnet.add_edge(
                    point1, intersect_point, half_width=half_width1
                )
                # self.floor_navnet.add_edge(intersect_point,
                #                            point1,
                #                            half_width=half_width1
                #                            )

            if point2 != intersect_point:
                self.floor_navnet.add_edge(
                    point2, intersect_point, half_width=half_width1
                )
                # self.floor_navnet.add_edge(intersect_point,
                #                            point2,
                #                            half_width=half_width1
                #                            )

            if point3 != intersect_point:
                self.floor_navnet.add_edge(
                    point3, intersect_point, half_width=half_width2
                )
                # self.floor_navnet.add_edge(intersect_point,
                #                            point3,
                #                            half_width=half_width2
                #                            )

            if point4 != intersect_point:
                self.floor_navnet.add_edge(
                    point4, intersect_point, half_width=half_width2
                )
                # self.floor_navnet.add_edge(intersect_point,
                #                            point4,
                #                            half_width=half_width2
                #                            )

        return intersect_point

    def export_navdata_to_pkl(self, navnet_pkl_file, hallway_graph_pkl_file):
        """Export the navigation network to a pickle file for later use.

        Parameters
        -----------
        navnet_pkl_file: str
            Full path to where to save the navigation network pickle file

        hallway_graph_pkl_file: str
            Full file path to save the hallways graph

        Returns
        --------
        bool
            Whether the export is successful or not

        """

        try:
            with open(navnet_pkl_file, "wb") as f:
                pickle.dump(self.floor_navnet, f)

            with open(hallway_graph_pkl_file, "wb") as f:
                pickle.dump(self.hallways_graph, f)
        except Exception as e:
            LOG.error(e)
            return False

        return True

    def export_navnet_to_svg(self, svg_file):
        """Export the navigation network to an svg file for visualization.

        Superimposes the navigation network on top of the floorplan for easier
        interpretation.

        Parameters
        -----------
        svg_file: str
            Full path the svg file to export to

        Returns
        --------
        bool
            Whether the export is successful or not

        """
        nav_nodes = []
        nav_paths = []
        for e in list(self.floor_navnet.edges):
            nav_nodes.append(e[0])
            nav_nodes.append(e[1])
            p = Line(
                start=complex(e[0][0], e[0][1]), end=complex(e[1][0], e[1][1])
            )
            nav_paths.append(p)
        LOG.info("Exporting...")
        try:
            bv.export_nav_network_to_svg(
                self.current_floorplan.walls, nav_paths, nav_nodes, svg_file
            )
        except Exception as e:
            LOG.error(e)
            return False

        LOG.info("Navigation network exported to: %s", svg_file)

        return True

    def load_nav_segments_from_svg_file(self, svg_file):

        if not os.path.isfile(svg_file):
            return []

        paths, attributes = svg2paths(svg_file)
        return [
            path
            for path, attr in zip(paths, attributes)
            if "id" in attr and "nav" in attr["id"]
        ]

    def update_network_from_svg_file(self, svg_file):
        """Update the navigation file using paths defined in an svg file.

        Parameters:
        ------------
        svg_file: string
            full path to the svg file

        Returns
        -------
        bool
            If network was successfully updated or not
        """

        if not os.path.isfile(svg_file):
            return False

        self.floor_navnet = self.floor_navnet.to_undirected()
        edges = list(self.floor_navnet.edges)
        new_nav_segments = self.load_nav_segments_from_svg_file(svg_file)
        for nav_seg in new_nav_segments:

            point1 = (round(nav_seg.start.real), round(nav_seg.start.imag))
            self.floor_navnet.add_node(point1)

            point2 = (round(nav_seg.end.real), round(nav_seg.end.imag))
            self.floor_navnet.add_node(point2)

            self.floor_navnet.add_edge(point1, point2, half_width=1.0)
            self.floor_navnet.add_edge(point2, point1, half_width=1.0)

            for edge in edges:
                point3 = edge[0]
                point4 = edge[1]

                self.find_and_add_intersection_node_to_graph(
                    point1, point2, point3, point4
                )
        self.floor_navnet = self.floor_navnet.to_directed()

        return True

    def load_navdata_from_pkl_files(
        self, navnet_pkl_file, hallway_graph_pkl_file
    ):
        """Load the navigation network and the hallway grpah from pickle files.

        Parameters:
        ------------
        navnet_pkl_file: string
            Full path to the navigation graph pickle file

        hallway_graph_pkl_file: str
            Full path to the hallway graph pickle file

        Returns
        -------
        bool
            Whether the data was successfully loaded or not
        """

        n_nodes = self.floor_navnet.number_of_nodes()
        if n_nodes > 0:
            LOG.error(
                "Unable to load new navigation data. The navigation "
                "network currently has %d. Please remove them first.",
                n_nodes,
            )
            return False

        if not os.path.isfile(navnet_pkl_file):
            LOG.error("File does not exist. %s", navnet_pkl_file)
            return False

        if not os.path.isfile(hallway_graph_pkl_file):
            LOG.error(
                "Hallway graph file does not exist: %s", hallway_graph_pkl_file
            )
            return False

        with open(navnet_pkl_file, "rb") as f:
            self.floor_navnet = pickle.load(f)

        with open(hallway_graph_pkl_file, "rb") as f:
            self.hallways_graph = pickle.load(f)

        return True
