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
import pathlib
import os
from typing import Tuple, List, Dict, Optional, Union
import json

import networkx as nx
import progressbar as pb
from svgpathtools import Line, svg2paths, Path

import citam.engine.io.visualization as bv
import citam.engine.map.utils as fu
import citam.engine.map.geometry as gsu
from citam.engine.map.door import Door
from citam.engine.map.point import Point
from citam.engine.map.floorplan import Floorplan
from citam.engine.map.space import Space

LOG = logging.getLogger(__name__)


class NavigationBuilder:
    """
    Create the navigation network (navnet) for a given floorplan.

    Each node in the navigation network is a notable xy coordinate in the
    floorplan corresponding to entrances to various spaces and intersections
    between navigation segments. The correspondence between nodes and
    actual locations is handled at the floorplan and navigation (see the
    navigation class) level.
    """

    def __init__(self, floorplan: Floorplan, add_all_nav_points=False):
        """
        Initialize a new navnet builder.

        Whether 'add_all_nav_points' is True of False, the final simplification
        process will remove any unnecessary nodes in the last step of the
        navnet creation process. The tradeoff here is the speed of finding
        intersections between segments. If all points are added, intersections
        are found almost for free (nodes with more than 2 edges) but the
        simplification process takes longer because there are more superfluous
        points to remove. If only the endpoints are added, an iteration over
        pairs of nav segments that fall within the same space is required to
        find intersections.

        :param current_floorplan: The floorplan for which to create the navnet.
        :type current_floorplan: Floorplan
        :param add_all_nav_points: whether to add all points from navigation
            segments to the network or just the endpoints, defaults to False
        :type add_all_nav_points: bool, optional
        """

        self.floorplan = floorplan
        self.add_all_nav_points = add_all_nav_points

        self.floor_navnet = nx.Graph()
        self.hallways_graph = nx.Graph()

        # Keys will be space unique names and each entry will be a list of nav
        # segments where each segment is a tuple of the 2 endpoints
        self.space_nav_segments: Dict[str, List[Tuple[Point, Point]]] = {}

        # self.current_space = None  # for testing and debugging purposes

        # To avoid parallel nav segments (if a door is already part of the
        # navnet, no need to use it to start new nav segments)
        self.excluded_doors: List[Door] = []

        return

    def build(self):
        """
        Build the navigation network (navnet) for a given floorplan.

        The navigation network is created by adding a navigation segment
        at the center of each aisle and then adding perpendicular nav segments
        acroos each door that hasn't been added to the navnet yet.
        """

        # Create nav segements for all aisles and doors
        LOG.info("Creating nav segments for each aisle...")
        self._create_nav_segments_for_aisles()

        LOG.info("Processing doors for each space...")
        self._create_nav_segments_for_doors()

        # Simplify nav network by removing unncesssary edges and nodes
        LOG.info("Removing unnecessary nodes from nav network...")
        self.simplify_navigation_network()

        # Make sure no intersection was missed
        if self.add_all_nav_points:
            for space in list(set(self.floorplan.spaces)):
                self.find_intersections_in_space(space)

        # Ensure no nav path crosses a special wall
        LOG.info("Make sure nav paths do not cross any walls...")
        self.sanitize_navnet()

        # Label all intersection nodes accordingly
        nodes = list(self.floor_navnet.nodes())
        for node in nodes:
            nneigh = list(self.floor_navnet.neighbors(node))
            if len(nneigh) > 2:
                self.floor_navnet.nodes[node]["node_type"] = "intersection"

        # Convert to directed graph
        self.floor_navnet = self.floor_navnet.to_directed()

        LOG.info("Done.")

    def _create_nav_segments_for_doors(self):
        """
        Iterate over each door in floorplan and create perpendicular nav
        segments for each.
        """
        pbar = pb.ProgressBar(max_value=len(self.floorplan.doors))
        for i, door in enumerate(self.floorplan.doors):
            pbar.update(i)
            if door in self.excluded_doors:
                continue

            # Add mid-point of door path to navnet as a door node
            self.floor_navnet.add_node(door.midpoint_coords, node_type="door")
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

    def _create_nav_segments_for_aisles(self):
        """
        Iterate over each hallway and create nav segments along each
        aisle.
        """
        pbar = pb.ProgressBar(max_value=len(self.floorplan.spaces))
        for i, space in enumerate(self.floorplan.spaces):
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

    def _update_navnet(
        self,
        segments: List[List[Point]],
        seg_spaces: List[Space],
        width: float,
    ) -> None:
        """
        For each segment in list of nav segments, create nodes and edges
        in navnet. Also keep track in which space each segment falls.

        [extended_summary]

        :param segments: List of segments where each segment is a list of
             points.
        :type segments: List[List[Point]]
        :param seg_spaces: List of spaces where each segment falls.
        :type seg_spaces: List[Space]
        :param width: Width of each edge to be added to navent.
        :type width: float
        """

        # Add segments to navnet
        self._add_segments_to_navnet(segments, seg_spaces, width)

        # Add segments to space
        for seg, seg_space in zip(segments, seg_spaces):
            full_line: Tuple[Point, Point] = (seg[0], seg[-1])
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
                # self.find_and_remove_overlaps(seg_space)
                # TODO: Also look for overlapping segments and merge them while
                # keeping all existing intersections. Would be great to
                # merge parallel segments as well

    def _aisle_has_nav_segment(
        self, aisle: Tuple[Line, Line], space: Space
    ) -> bool:
        """
        Check if aisle already has a navigation segment.

        :param aisle: Aisle, given as a tuple of 2 walls.
        :type aisle: Tuple[Line, Line]
        :param space: The space where this aisle is located.
        :type space: Space
        :return: Whether a nav segment was found in this aisle or not.
        :rtype: bool
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

    def _find_valid_boundaries(self, space: Space) -> List[Line]:
        """
        Iterate over boundary walls of a space and return only the
         ones that are not between two hallways.

        :param space: The space of interest.
        :type space: Space
        :return: List of valid boundaries.
        :rtype: List[Line]
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

    def create_nav_segment_for_aisle(self, aisle: tuple) -> None:
        """
        Create navigation segements (edges in the navnet) to handle
        circulation in this aisle.

        :param aisle: An aisle, given by two parallel walls.
        :type aisle: Tuple[Line, Line]
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

    def _find_location_of_point(
        self, point: Point
    ) -> Tuple[Optional[Space], Optional[int]]:
        """
        Find the space inside which this point is located.

        :param point: The point of interest
        :type point: Point
        :return: Space object where the point is located (None if not found)
                and its index in the list of spaces (None if not found).
        :rtype: Tuple[Optional[Space], Optional[int]]
        """

        for i, space in enumerate(self.floorplan.spaces):
            if space.is_point_inside_space(point):
                return space, i

        return None, None

    def _is_point_on_boundaries(self, point: Point) -> List[Space]:
        """
        Check if point falls on any boundary and return list of
        corresponding spaces. If only one space, then this is an exterior
        boundary.

        :param point: The point of interest.
        :type point: Point
        :return: List of spaces on which boundaries this point lies.
        :rtype: List[Space]
        """

        boundary_spaces = []
        for i, space in enumerate(self.floorplan.spaces):
            if space.is_point_on_space_boundaries(point):
                boundary_spaces.append(space)

        return boundary_spaces

    def _add_segments_to_navnet(
        self,
        segments: List[List[Point]],
        seg_spaces: List[Space],
        width: float,
    ) -> None:
        """
        Add nodes and edges to the navigation network based on a given list of
        nav segments.

        Each point in each segment is added as a node in the nav network
        and a connection (edge) is created between each successive pair of
        points.

        :param segments: List of segments to consider.
        :type segments: List[List[Point]]
        :param seg_spaces: List of spaces where the segments fall.
        :type seg_spaces: List[Space]
        :param width: Width to assign to each edge in the navnet.
        :type width: float
        :raises ValueError: If a segment has less than 2 points.
        """

        for i, seg in enumerate(segments):
            if len(seg) in [0, 1]:
                raise ValueError("Each segment must have two points.")

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

    def _add_spaces_to_hallway_graph(self, spaces: List[Space]) -> None:
        """
        Add hallways to the hallway graph.

        The hallway graph keeps track of which hallway is accessible from
        which hallway. A connection is created between each space given
        as input.

        :param spaces: The list of space objects to add to the graph.
        :type spaces: List[Space]
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
                and old_space.is_space_a_hallway()
                and current_space.is_space_a_hallway()
            ):

                self.hallways_graph.add_edge(
                    old_space.unique_name, current_space.unique_name
                )
            old_space = current_space

    def find_door_intersect(
        self, test_line: Line
    ) -> Tuple[Optional[Tuple[int, int]], Optional[Door]]:
        """
        Check if the given line intersects with a door.

        Intersect coords are to the nearest integer.

        :param test_line: The line of interest.
        :type test_line: Line
        :return: The intersect xy coordinates and the door object, (None, None)
                if not found.
        :rtype: Tuple[Optional[Tuple[int, int]], Optional[Door]]
        """
        """"""
        coords = None
        door_found = None
        for door in self.floorplan.doors:
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

    def find_if_valid_nearby_space_exits(
        self, current_point: Point, direction: int, dx: float, dy: float
    ) -> Space:
        """
        Given a point and direction, look ahead by (dx, dy) to verify if a
        valid space exists there and return that space.

        This function is expected to be used to decide whether to continue with
        a navigation segment or not when crossing the boundaries of the current
        space (hence the direction parameter). Keep in mind that a boundary
        does not need to correspond to a wall).

        :param new_point: The current point that falls on the boundaries.
        :type new_point: Point
        :param direction: The current direction of the nav segment.
        :type direction: int
        :param dx: The look ahead distance in the x direction.
        :type dx: float
        :param dy: The look ahead distance in the y direction.
        :type dy: float
        :raises ValueError: If point is not on any boundary.
        :raises ValueError: If space is found to be on the boundary of 2 or
                more spaces but no space is found ahead (clearly something is
                wrong).
        :return: The space ahead
        :rtype: Space
        """
        boundary_spaces = self._is_point_on_boundaries(current_point)
        if len(boundary_spaces) == 0:
            raise ValueError(
                "Unable to compute a nav segment from %s",
                str(current_point),
            )
        elif len(boundary_spaces) == 1:
            LOG.info(
                "{%s} on space boundary. Is it an entrance?", current_point
            )
            current_space = boundary_spaces[0]
            return current_space
        else:
            test_point = Point(
                x=round(current_point.x + direction * dx),
                y=round(current_point.y + direction * dy),
            )
            current_space, _ = self._find_location_of_point(test_point)
            if current_space is None:
                raise ValueError(
                    "Unable to compute a nav segment from %s",
                    str(current_point),
                )
        return current_space

    def _update_segments(
        self, new_point: Point, direction: int, segments: List[Point]
    ) -> None:
        """
        Given a valid new point, update the current navigation segments.

        :param new_point: The new point to add to one of the segments
        :type new_point: Point
        :param direction: The current direction of the nav segment.
        :type direction: int
        :param segments: The current list of segments
        :type segments: List[Point]
        """

        if direction == -1:
            segments[-1] = [new_point] + segments[-1]
        else:
            segments[-1].append(new_point)

    def _is_crossing_wall(self, first_point: Point, new_point: Point) -> bool:
        """
        Verify if the current nav segment has reached an existing wall.

        :param first_point: The very first point of the navigation segment.
        :type first_point: Point
        :param new_point: The current point in the navigation segment.
        :type new_point: Point
        :return: Whether a wall is reached or not.
        :rtype: bool
        """

        test_line = Line(
            start=first_point.complex_coords,
            end=new_point.complex_coords,
        )
        # TODO: Change test_line to be the last segment!
        for wall in self.floorplan.walls:
            if wall.length() > 1 and len(test_line.intersect(wall)) > 0:
                # We encountered a wall!!!
                return True

        return False

    def _is_heading_outside_facility(
        self,
        new_point: Point,
        direction: int,
        dx: float,
        dy: float,
        look_ahead_dist=3,
    ) -> bool:
        """
        Verify if current nav segment is heading outside the facility
        within a given look ahead distance.

        [extended_summary]

        :param new_point: The current point of the nav segment.
        :type new_point: Point
        :param direction: The direction (positive or negative) where the
            segment is headed.
        :type direction: int
        :param dx: look ahead distance in the x direction
        :type dx: float
        :param dy: look ahead distance in the y direction
        :type dy: float
        :param look_ahead_dist: look-ahead distance multiplier, defaults to 3
        :type look_ahead_dist: int, optional
        :raises ValueError: If value for the direction is invalid.
        :return: Whether the position ahead is outside the facility or not.
        :rtype: bool
        """

        if direction not in [-1, 1]:
            raise ValueError("Direction must be 1 or -1.")

        test_point = Point(
            x=round(new_point.x + look_ahead_dist * direction * dx),
            y=round(new_point.y + look_ahead_dist * direction * dy),
        )
        test_point_space, _ = self._find_location_of_point(test_point)
        if test_point_space is None:
            return True

        return False

    def _is_crossing_door(
        self, first_point: Point, current_point: Point
    ) -> Optional[Tuple[int, int]]:
        """
        Verify if current nav segment is crossing a door, if so add door
        to list of excluded doors and update segments accordingly.

        ..Note: Expected to cross only one door at a time.

        :param first_point: The very first point in the current nav segment.
        :type first_point: Point
        :param new_point: The current point in the nav segment.
        :type new_point: Point
        :return: The intersect coordinates with a door, if any, None otherwise.
        :rtype: Optional[Tuple[int, int]]
        """

        test_line = Line(
            start=first_point.complex_coords,
            end=current_point.complex_coords,
        )
        coords, door = self.find_door_intersect(test_line)
        if coords is not None and door is not None:
            door.intersect_coords = coords
            self.excluded_doors.append(door)
            return coords

        return None

    def compute_nav_segments(
        self,
        first_point: Point,
        direction_vector: complex,
        width: float,
        stop_at_existing_segments: bool = False,
    ) -> Tuple[List, List]:
        """
        Compute navigation segments from a given point and direction.
        2 segments are created from the starting point going in opposite
        directions.

        A navigation segment corresponds to an edge in the navigation graph
        connecting 2 nodes (usually doors or walls marking the end of the
        navigation segment).

        :param first_point: The initial point from which to start the segments
        :type first_point: Point
        :param direction_vector: Vector indicating the directions (positive and
                 negative) of the segments.
        :type direction_vector: complex
        :param width: The width to assign to edges in the navnet.
        :type width: float
        :param stop_at_existing_segments: Whether to stop if the segment
             crosses an existing navigation segment in the navnet or not,
             defaults to False
        :type stop_at_existing_segments: bool, optional
        :raises ValueError: if the number of segments is different from the
            number of spaces at the end of the process, indicating that
            something went wrong.
        :return: list of segments and corresponding space ids where they fall.
        :rtype: Tuple[List, List]
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
                current_space = self.find_if_valid_nearby_space_exits(
                    new_point, direction, dx, dy
                )

            segment_spaces.append(current_space)

            while True:
                # move one point in the given direction
                new_point = Point(
                    x=round(new_point.x + direction * dx),
                    y=round(new_point.y + direction * dy),
                )

                if current_space.is_point_inside_space(new_point):
                    self._update_segments(new_point, direction, segments)
                else:
                    # Check if this is a wall
                    if self._is_crossing_wall(first_point, new_point):
                        break

                    new_space, _ = self._find_location_of_point(new_point)

                    # Check if heading outside facility
                    if (
                        new_space is None
                        and self._is_heading_outside_facility(
                            new_point, direction, dx, dy
                        )
                    ):
                        break

                    if new_space:

                        current_space = new_space
                        segment_spaces.append(current_space)
                        door_inters_coords = self._is_crossing_door(
                            first_point, new_point
                        )

                        if door_inters_coords:
                            # create new segment from intersect coords
                            inters_point = Point(
                                door_inters_coords[0], door_inters_coords[1]
                            )
                            self._update_segments(
                                inters_point, direction, segments
                            )
                            segments.append([inters_point])
                            current_space = new_space

                        else:  # Create new segment from last point
                            if direction == 1:
                                segments.append([segments[-1][-1], new_point])
                            else:
                                segments.append([new_point, segments[-1][0]])

                    else:
                        # Just update segment. This is to support edge case
                        # where a small gap exists between valid spaces
                        self._update_segments(new_point, direction, segments)

                if stop_at_existing_segments and self.floor_navnet.has_node(
                    (new_point.x, new_point.y)
                ):
                    break

        if len(segments) != len(segment_spaces):
            LOG.fatal("Number of segments should equal number of spaces")
            LOG.info(
                "We have: {%d} * {%d}", len(segments), len(segment_spaces)
            )
            raise ValueError("Failed to build nav segments in this floorplan")

        good_segments = []
        good_segment_spaces = []
        for seg, seg_space in zip(segments, segment_spaces):
            if len(seg) > 1:
                good_segments.append(seg)
                good_segment_spaces.append(seg_space)

        return good_segments, good_segment_spaces

    def sanitize_navnet(self) -> None:
        """
        Make sure navigation paths do not cross any walls, including
        standalone walls.
        """

        if len(self.floorplan.special_walls) == 0:
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
            for wall in self.floorplan.special_walls:
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

    def simplify_navigation_network(self) -> None:
        """
        Remove unnecessary edges and nodes in navigation network.

        A node is unnecessary if it only has 2 neighbors and all 3 together
        form a straight line.
        """

        if "is_simplified" in self.floor_navnet.graph:
            if self.floor_navnet.graph["is_simplified"]:
                return
        else:
            n_nodes = self.floor_navnet.number_of_nodes()
            LOG.info("Starting number of nodes: %d", n_nodes)
            n_edges = self.floor_navnet.number_of_edges()
            LOG.info("Starting number of edges: %d", n_edges)

            door_paths = [d.path for d in self.floorplan.doors]
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

    def find_and_remove_overlaps(self, space: Space) -> None:
        """
        Iterate over segments in this space, test for overlap (parallel
        segments) and remove any.
        """
        raise NotImplementedError("Not implemented yet")

    def find_intersections_in_space(self, space: Space) -> None:
        """
        Iterate through all nav segment pairs in this space, find any
        intersections and add to navnet.

        An intersection is when 2 nav segments cross each other.

        :param space: The space of interest
        :type space: Space
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
                                new_segment = (point, new_point)
                                self.space_nav_segments[key].append(
                                    new_segment
                                )

                        exit_loop = True
                        break
                if exit_loop:
                    done = False
                    break

    def find_and_add_intersection_node_to_graph(
        self,
        coords1: Tuple[int, int],
        coords2: Tuple[int, int],
        coords3: Tuple[int, int],
        coords4: Tuple[int, int],
    ) -> Point:
        """
        Given four points forming 2 lines, check if they intersect
        and if so add new node to graph and create new edges.

        :param coords1: Coordinates of first point.
        :type coords1: Tuple[int, int]
        :param coords2: Coordinates of first point.
        :type coords2: Tuple[int, int]
        :param coords3: Coordinates of first point.
        :type coords3: Tuple[int, int]
        :param coords4: Coordinates of first point.
        :type coords4: Tuple[int, int]
        :return: xy coordinates of the intersection. None if none.
        :rtype: Point
        """

        line1 = Line(
            start=complex(coords1[0], coords1[1]),
            end=complex(coords2[0], coords2[1]),
        )
        line2 = Line(
            start=complex(coords3[0], coords3[1]),
            end=complex(coords4[0], coords4[1]),
        )

        if line1.length() <= 1.0 or line2.length() <= 1.0:
            return

        intersect_coords = None
        intersects = line1.intersect(line2)
        if len(intersects) > 0:
            t1, t2 = intersects[0]
            if t1 in (0.0, 1.0) and t2 in (0.0, 1.0):
                return

            intersect_coords = (
                round(line1.point(t1).real),
                round(line1.point(t1).imag),
            )

            self.floor_navnet.add_node(intersect_coords)

            if self.floor_navnet.has_edge(coords1, coords2):
                edge1 = self.floor_navnet.get_edge_data(coords1, coords2)
                half_width1 = edge1["half_width"]
                self.floor_navnet.remove_edge(coords1, coords2)
            else:
                half_width1 = 1

            if self.floor_navnet.has_edge(coords2, coords1):
                self.floor_navnet.remove_edge(coords2, coords1)

            if self.floor_navnet.has_edge(coords3, coords4):
                edge2 = self.floor_navnet.get_edge_data(coords3, coords4)
                half_width2 = edge2["half_width"]
                self.floor_navnet.remove_edge(coords3, coords4)
            else:
                half_width2 = 1

            if self.floor_navnet.has_edge(coords4, coords3):
                self.floor_navnet.remove_edge(coords4, coords3)

            if coords1 != intersect_coords:
                self.floor_navnet.add_edge(
                    coords1, intersect_coords, half_width=half_width1
                )

            if coords2 != intersect_coords:
                self.floor_navnet.add_edge(
                    coords2, intersect_coords, half_width=half_width1
                )

            if coords3 != intersect_coords:
                self.floor_navnet.add_edge(
                    coords3, intersect_coords, half_width=half_width2
                )

            if coords4 != intersect_coords:
                self.floor_navnet.add_edge(
                    coords4, intersect_coords, half_width=half_width2
                )

        return intersect_coords

    def export_navnet_to_svg(self, svg_file: Union[str, pathlib.Path]) -> None:
        """
        Export the navigation network to an svg file for visualization.

        Superimposes the navigation network on top of the floorplan for easier
        interpretation.

        :param svg_file: path the svg file to export to.
        :type svg_file: Union[str, pathlib.Path]
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
        bv.export_nav_network_to_svg(
            self.floorplan.walls, nav_paths, nav_nodes, svg_file
        )
        LOG.info("Navigation network exported to: %s", svg_file)

    def load_nav_paths_from_svg_file(
        self, svg_file: Union[str, pathlib.Path]
    ) -> List[Path]:
        """
        Load all the nav segments found in an SVG file. Nav segments are paths
        tagged with a 'nav' in their id attribute.

        :param svg_file: Path to the SVG file
        :type svg_file: Union[str, pathlib.Path]
        :return: List of nav paths found in SVG file.
        :rtype: List[Path]
        """
        if not os.path.isfile(svg_file):
            return []

        paths, attributes = svg2paths(svg_file)
        return [
            path
            for path, attr in zip(paths, attributes)
            if "id" in attr and "nav" in attr["id"]
        ]

    def update_network_from_svg_file(
        self, svg_file: Union[str, pathlib.Path]
    ) -> None:
        """
        Update the navigation file using nav paths defined in an svg file. Can
        be used to allow a user to edit the navnet after the fact to add, edit
        or remove segments.

        :param svg_file: full path to the svg file.
        :type svg_file: Union[str, pathlib.Path]
        :raises FileNotFoundError: If the svg file is not found.
        """

        if not os.path.isfile(svg_file):
            raise FileNotFoundError(svg_file)

        self.floor_navnet = self.floor_navnet.to_undirected()
        edges = list(self.floor_navnet.edges)
        new_nav_segments = self.load_nav_paths_from_svg_file(svg_file)

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

    def export_navdata_to_json(
        self,
        navnet_json_file: Union[str, pathlib.Path],
        hallway_graph_json_file: Union[str, pathlib.Path],
    ) -> None:
        """
        Export the navigation network data to json file for later use.

        [extended_summary]

        :param navnet_json_file: path to location to save navnet json file
        :type navnet_json_file: Union[str, pathlib.Path]
        :param hallway_graph_json_file: path to location to save the hallways
             graph
        :type hallway_graph_json_file: Union[str, pathlib.Path]
        """

        nav_dict = nx.readwrite.json_graph.node_link_data(self.floor_navnet)
        with open(navnet_json_file, "w") as f:
            json.dump(nav_dict, f)

        hg_dict = nx.readwrite.json_graph.node_link_data(self.hallways_graph)
        with open(hallway_graph_json_file, "w") as f:
            json.dump(hg_dict, f)

    def load_navdata_from_json_files(
        self,
        navnet_json_file: Union[str, pathlib.Path],
        hallway_graph_json_file: Union[str, pathlib.Path],
    ) -> None:
        """
        Load the navigation network and the hallway graph from json files.

        Used to initialize the navnet and hallway graph using data from
        existing files.

        :param navnet_json_file: Full path to the navigation graph json file
        :type navnet_json_file: Union[str, pathlib.Path]
        :param hallway_graph_json_file: Full path to the hallway graph json
                file
        :type hallway_graph_json_file: Union[str, pathlib.Path]
        :raises ValueError: If a navnet or hallway graph currently exists, to
                avoid accidental overwrite.
        """

        n_nodes = self.floor_navnet.number_of_nodes()
        if n_nodes > 0:
            LOG.error(
                "Unable to load new navigation data. The navigation "
                "network currently has %d. Please remove them first.",
                n_nodes,
            )
            raise ValueError(
                "A navnet currently exists. Cannot load new network."
            )

        with open(navnet_json_file, "r") as f:
            navdata = json.load(f)
        self.floor_navnet = nx.readwrite.json_graph.node_link_graph(navdata)

        with open(hallway_graph_json_file, "r") as f:
            hgdata = json.load(f)
        self.hallways_graph = nx.readwrite.json_graph.node_link_graph(hgdata)
