# Copyright 2021. Corning Incorporated. All rights reserved.
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
import xml.etree.ElementTree as ET

import networkx as nx
import pathlib
from typing import Optional, Union, List, Tuple, Dict, Any
from matplotlib import cm, colors
from svgpathtools import wsvg, Arc, Line, parse_path, Path
from svgpathtools.paths2svg import paths2Drawing

from citam.engine.map.point import Point

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

X_MARKER = 1
LINE_MARKER = 2
PLUS_MARKER = 3

LOG = logging.getLogger(__name__)


def export_possible_oneway_aisles_to_svg(
    walls: List[Path],
    oneway_network: nx.Graph,
    svgfile: Union[str, pathlib.Path],
) -> None:
    """
    Export the one_way network superimposed on the floorplan to an SVG file.

    :param walls: All the walls found in the floorplan.
    :type walls: List[Path]
    :param oneway_network: The one-way network.
    :type oneway_network: nx.Graph
    :param svgfile: location to save the SVG file.
    :type svgfile: Union[str, pathlib.Path]
    """
    texts = []
    text_paths = []
    radius = complex(3, 3)
    small_radius = complex(1.0, 1.0)
    paths = [wall for wall in walls]
    attributes = [
        {"fill": "white", "stroke": "black", "stroke-width": 0.5}
        for _ in paths
    ]

    color = "red"
    for e in list(oneway_network.edges(data=True)):
        p = Line(
            start=complex(e[0][0], e[0][1]), end=complex(e[1][0], e[1][1])
        )
        paths.append(p)
        attributes.append(
            {"fill": color, "stroke": color, "stroke-width": 0.1}
        )
        midx, midy = p.point(0.5).real, p.point(0.5).imag
        t_path = parse_path(
            "M "
            + str(midx)
            + ","
            + str(midy)
            + " L "
            + str(midx + 60)
            + ","
            + str(midy)
        )

        texts.append(str(e[2]["id"]))
        text_paths.append(t_path)

        for coord in (e[0], e[1]):
            x, y = coord
            start = Point(x=x - radius.real, y=y)
            end = Point(x=x + radius.real, y=y)
            agent_top = Arc(
                start=start.complex_coords,
                radius=radius,
                rotation=0,
                large_arc=1,
                sweep=1,
                end=end.complex_coords,
            )
            attributes.append(
                {"fill": color, "stroke": color, "stroke-width": 0.1}
            )
            paths.append(agent_top)
            agent_bottom = agent_top.rotated(180)
            attributes.append(
                {"fill": color, "stroke": color, "stroke-width": 0.1}
            )
            paths.append(agent_bottom)

        for coord in e[2]["inter_points"]:
            x, y = coord
            start = Point(x=x - small_radius.real, y=y)
            end = Point(x=x + small_radius.real, y=y)
            agent_top = Arc(
                start=start.complex_coords,
                radius=small_radius,
                rotation=0,
                large_arc=1,
                sweep=1,
                end=end.complex_coords,
            )
            attributes.append(
                {"fill": color, "stroke": color, "stroke-width": 0.1}
            )
            paths.append(agent_top)
            agent_bottom = agent_top.rotated(180)
            attributes.append(
                {"fill": color, "stroke": color, "stroke-width": 0.1}
            )
            paths.append(agent_bottom)

    wsvg(
        paths,
        attributes=attributes,
        text=texts,
        text_path=text_paths,
        font_size=10,
        filename=svgfile,
    )


def create_arrow_svg_paths(
    arrow: Tuple[Tuple[int, int], Tuple[int, int]]
) -> Tuple[List[Path], List[Dict[str, Any]]]:
    """
    Given two points, create an arrow-like SVG element with the first point as
    the head.

    :param arrow: The haid and tail xy coordinates of the arrow.
    :type arrow: Tuple[Tuple[int,int], Tuple[int,int]]
    :return: List of paths and attributes (color, stroke size, etc.)
    :rtype: Tuple[List[Path], List[Dict[str, str]]
    """
    paths = []
    attributes = []

    radius = complex(0.5, 0.5)

    x_start, y_start = arrow[0]
    x_end, y_end = arrow[1]

    start = Point(x=x_start, y=y_start)
    end = Point(x=x_end, y=y_end)
    line1 = Line(start=start.complex_coords, end=end.complex_coords)
    attributes.append({"stroke": "green", "stroke-width": 0.5})
    paths.append(line1)

    start = Point(x=x_end - radius.real, y=y_end)
    end = Point(x=x_end + radius.real, y=y_end)
    agent_top = Arc(
        start=start.complex_coords,
        radius=radius,
        rotation=0,
        large_arc=1,
        sweep=1,
        end=end.complex_coords,
    )
    attributes.append(
        {"fill": "green", "stroke": "green", "stroke-width": 0.1}
    )
    paths.append(agent_top)
    agent_bottom = agent_top.rotated(180)
    attributes.append(
        {"fill": "green", "stroke": "green", "stroke-width": 0.1}
    )
    paths.append(agent_bottom)

    return paths, attributes


def create_markers_svg_paths(
    x: int, y: int, marker_type: int = None
) -> Tuple[List[Path], List[Dict[str, Any]]]:
    """
    Create SVG paths for arbitrary markers to be used on a floorplan.

    :param x: the x position of the marker
    :type x: int
    :param y: the y position of the marker
    :type y: int
    :param marker_type: the type of the marker (e.g. a plus sign, a line, etc.)
    :type marker_type: int, optional
    :return: The SVG paths and attributes
    :rtype: Tuple[List[Path], List[Dict[str, Any]]]
    """
    paths = []
    attributes = []

    if marker_type == PLUS_MARKER or marker_type is None:

        half_length = 0.5
        start = Point(x=x - half_length, y=y)
        end = Point(x=x + half_length, y=y)
        line1 = Line(start=start.complex_coords, end=end.complex_coords)
        start = Point(x=x, y=y - half_length)
        end = Point(x=x, y=y + half_length)
        line2 = Line(start=start.complex_coords, end=end.complex_coords)

        attributes.append({"stroke": "red", "stroke-width": 0.5})
        paths.append(line1)
        attributes.append({"stroke": "red", "stroke-width": 0.5})
        paths.append(line2)

    elif marker_type == LINE_MARKER:

        half_length = 0.4
        start = Point(x=x - half_length, y=y)
        end = Point(x=x + half_length, y=y)
        line1 = Line(start=start.complex_coords, end=end.complex_coords)
        attributes.append({"stroke": "red", "stroke-width": 0.5})
        paths.append(line1)

    else:
        LOG.info("ERROR: unsupported marker type %s", marker_type)

    return paths, attributes


def export_nav_network_to_svg(
    walls: List[Path],
    nav_paths: List[Path],
    nav_nodes: List[Tuple[int, int]],
    filename: Optional[Union[str, pathlib.Path]] = None,
    marker_type: int = X_MARKER,
    color="blue",
) -> None:
    """
    Export a navigation network superimposed on a floorplan to an SVG file.

    :param walls: All the walls in the floorplan.
    :type walls: List[Path]
    :param nav_paths: The navigation paths of the navnet.
    :type nav_paths: List[Path]
    :param nav_nodes: The key nodes of the navnet to show on the map.
    :type nav_nodes: List[Tuple[int, int]]
    :param filename: The output file location.
    :type filename: Union[str, pathlib.Path]
    :param marker_type: The type of markers , defaults to X_MARKER
    :type marker_type: str, optional
    :param color: The color to used to represent the navnet, defaults to "blue"
    :type color: str, optional
    """
    radius = complex(2, 2)
    paths = [wall for wall in walls]
    attributes = [
        {"fill": "white", "stroke": "black", "stroke-width": 0.5}
        for _ in paths
    ]

    for nn in nav_nodes:
        x, y = nn
        start = Point(x=x - radius.real, y=y)
        end = Point(x=x + radius.real, y=y)
        agent_top = Arc(
            start=start.complex_coords,
            radius=radius,
            rotation=0,
            large_arc=1,
            sweep=1,
            end=end.complex_coords,
        )
        attributes.append(
            {"fill": color, "stroke": color, "stroke-width": 0.1}
        )
        paths.append(agent_top)
        agent_bottom = agent_top.rotated(180)
        attributes.append(
            {"fill": color, "stroke": color, "stroke-width": 0.1}
        )
        paths.append(agent_bottom)

    for np in nav_paths:
        paths.append(np)
        attributes.append(
            {"fill": color, "stroke": color, "stroke-width": 0.1}
        )
    if filename is None:
        return wsvg(paths, attributes=attributes, paths2Drawing=True)
    else:
        wsvg(paths, attributes=attributes, filename=filename)


def export_world_to_svg(
    walls: List[Path],
    agent_positions_and_contacts: Optional[List[Tuple[int, int, int]]] = None,
    svg_file: Optional[Union[str, pathlib.Path]] = None,
    marker_locations: Optional[List[Tuple[int, int, int]]] = None,
    marker_type: int = None,
    arrows: Optional[List[Tuple[Tuple[int, int], Tuple[int, int]]]] = None,
    doors: Optional[List[Path]] = None,
    max_contacts: int = 100,
    current_time: int = None,
    show_colobar=False,
    viewbox: Tuple[float, ...] = None,
) -> None:
    """
    Save a snapshot of a simulation with the floorplan, agent positions and
    number of contacts, doors and any markers to an SVG file.

    :param walls: All the walls in the floorplan.
    :type walls: List[Path]
    :param agent_positions_and_contacts: positions and number of contacts for
            each agent.
    :type agent_positions_and_contacts: List[Tuple[int, int, int]]
    :param svg_file: Location of the output SVG file.
    :type svg_file: Union[str, pathlib.Path]
    :param marker_locations: xy positions of any markers, defaults to []
    :type marker_locations: List[Tuple[int, int, int]], optional
    :param marker_type: the type of marker to use, defaults to None
    :type marker_type: int, optional
    :param arrows: list of heads and tails for any arrow, defaults to []
    :type arrows: List[Tuple[int, int], Tuple[int, int]], optional
    :param doors: list of door elements, defaults to []
    :type doors: List[Path], optional
    :param max_contacts: The maximum number of contacts to use for the
            colorbar, defaults to 100
    :type max_contacts: int, optional
    :param current_time: the time to show on the clock, defaults to None
    :type current_time: int, optional
    :param show_colobar: whether to show a colorbar or not, defaults to False
    :type show_colobar: bool, optional
    :param viewbox: the viewbox of the SVG, defaults to None
    :type viewbox: Tuple[float, ...], optional
    """
    if viewbox is not None:
        xmax = viewbox[2]
        multiplier = round(xmax / 1500, 1)
    else:
        multiplier = 1.0

    doors = [] if doors is None else doors
    marker_locations = [] if marker_locations is None else marker_locations
    arrows = [] if arrows is None else arrows
    agent_positions_and_contacts = (
        []
        if agent_positions_and_contacts is None
        else agent_positions_and_contacts
    )

    radius = complex(2, 2)
    paths = [wall for wall in walls]
    attributes = [
        {"fill": "white", "stroke": "black", "stroke-width": 0.5 * multiplier}
        for _ in paths
    ]

    color_scale = cm.get_cmap("RdYlGn")

    for x, y, n_contacts in agent_positions_and_contacts:
        color = color_scale(1.0 - n_contacts * 1.0 / max_contacts)
        start = Point(x=x - radius.real, y=y)
        end = Point(x=x + radius.real, y=y)
        agent_top = Arc(
            start=start.complex_coords,
            radius=radius,
            rotation=0,
            large_arc=1,
            sweep=1,
            end=end.complex_coords,
        )
        attributes.append(
            {
                "fill": colors.to_hex(color),
                "stroke": "blue",
                "stroke-width": 0.1 * multiplier,
            }
        )
        paths.append(agent_top)
        agent_bottom = agent_top.rotated(180)
        attributes.append(
            {
                "fill": colors.to_hex(color),
                "stroke": "blue",
                "stroke-width": 0.1 * multiplier,
            }
        )
        paths.append(agent_bottom)

    for x, y, n_contacts in marker_locations:
        marker_paths, marker_attr = create_markers_svg_paths(x, y, marker_type)
        paths += marker_paths
        attributes += marker_attr

    for arrow in arrows:
        arrow_path, arrow_attr = create_arrow_svg_paths(arrow)
        paths += arrow_path
        attributes += arrow_attr

    for door in doors:
        paths.append(door.path)
        attributes.append({"stroke": "red", "stroke-width": 3.0 * multiplier})

    t_path = parse_path("M 0,0 L 250,0")

    if viewbox is not None:
        xmin, ymin, xmax, ymax = viewbox
        viewbox_str = (
            str(xmin) + " " + str(ymin) + " " + str(xmax) + " " + str(ymax)
        )
        svg_attributes = {
            "width": "100%",
            "height": "100%",
            "viewBox": viewbox_str,
        }
    else:
        svg_attributes = None  # type: ignore

    if svg_file is None:
        return wsvg(
            paths,
            attributes=attributes,
            text=current_time,
            text_path=t_path,
            svg_attributes=svg_attributes,
            paths2Drawing=True,
        )

    else:
        wsvg(
            paths,
            attributes=attributes,
            text=current_time,
            text_path=t_path,
            filename=svg_file,
            svg_attributes=svg_attributes,
        )

        add_root_layer_to_svg(svg_file, svg_file)


def add_root_layer_to_svg(
    original_svg_filename: Union[str, pathlib.Path],
    updated_filename: Union[str, pathlib.Path],
) -> None:
    """
    Helper function to update an existing SVG file to add a root element.

    :param original_svg_filename: Initial SVG file.
    :type original_svg_filename: Union[str, pathlib.Path]
    :param updated_filename: new SVG file to write.
    :type updated_filename: Union[str, pathlib.Path]
    """
    tree = ET.parse(original_svg_filename)

    root = tree.getroot()

    new_root = ET.Element("g")
    new_root.set("id", "root")

    for path_elem in root:
        new_root.append(path_elem)

    while len(root) > 0:
        root.remove(root[0])

    root.append(new_root)

    tree.write(updated_filename)
