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


import errno
import logging
import os
import time
from copy import deepcopy
from typing import List

import networkx as nx
from networkx.classes.graph import Graph
from svgpathtools import Line

import citam.engine.io.visualization as bv
import citam.engine.map.geometry as gsu
import citam.engine.io.storage_utils as su
from citam.engine.facility.navbuilder import NavigationBuilder
from citam.engine.map.floorplan import floorplan_from_directory
from citam.engine.map.ingester import FloorplanIngester
from citam.engine.map.updater import FloorplanUpdater
from citam.engine.core.simulation import Simulation
from citam.engine.map.point import Point
from citam.engine.facility.indoor_facility import Facility
import json

LOG = logging.getLogger(__name__)

ROUTES_JSON_FILE = "routes.json"


def list_facilities(**kwargs):  # noqa
    """List all the floorplans already ingested"""

    floorplans_directory = su.get_floorplans_directory()
    if not os.path.isdir(floorplans_directory):
        print("No facility found.")
    else:
        subdirs = [
            f
            for f in os.listdir(floorplans_directory)
            if os.path.isdir(os.path.join(floorplans_directory, f))
        ]
        if len(subdirs) == 0:
            print("No facility found")
        else:
            print("Current facilities: ")
            for f in subdirs:
                print(f)


def ingest_floorplan(
    svg: str,
    csv: str,
    facility: str,
    scale: float = 1 / 12,
    floor: str = "0",
    buildings: List[str] = None,
    output_directory=None,
    force_overwrite=False,
    **kwargs
):  # noqa
    """Ingest raw floorplan and data files for a given floor of a facility.

    This method is executed with the CLI call ``citam engine ingest``

    :param svg: Path to the floorplan file in SVG format
    :param csv: Path to the floorplan metadata file in CSV format
    :param facility: Name of this facility
    :param scale: The scale of the drawing (default = 1/12)
    :param floor: Name of this floor (default=0)
    :param output_directory: Custom location to store output (default=cache)
    :param buildings: List of buildings to process(default to all buildings
            found in SVG file)
    :raise FileNotFoundError: If input files are not found
    """

    if not os.path.isfile(svg):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), svg)

    if output_directory is None:
        floor_directory = su.get_datadir(facility, floor)
        if not os.path.isdir(floor_directory):
            su.create_datadir(facility, floor)
    else:
        floor_directory = output_directory
        if not os.path.isdir(floor_directory):
            os.mkdir(floor_directory)

    fp_file = os.path.join(floor_directory, "floorplan.json")
    if os.path.isfile(fp_file) and force_overwrite is False:
        LOG.error(
            "Floorplan exists. Please choose another facility or floor name."
        )
        return

    LOG.info("Ingesting floorplan...")
    floorplan_ingester = FloorplanIngester(
        svg,
        scale,
        csv_file=csv,
        buildings_to_keep=buildings,
        extract_doors_from_file=True,
    )
    floorplan_ingester.run()

    LOG.info("Saving floorplan to json file...")
    floorplan = floorplan_ingester.get_floorplan()
    floorplan.to_json_file(fp_file)
    LOG.info("Done.")


def export_floorplan_to_svg(
    facility: str,
    floor: str,
    outputfile: str,
    doors=False,
    floorplan_directory: str = None,
    **kwargs
):  # noqa
    """Export a given floorplan to an SVG file for visualization and editing.

    :param facility: Name of this facility
    :param floor: Name of this floor
    :param outputfile: Location to store output
    :param floorplan_directory: Custom directory for floorplans (default=cache)
    :raise NotADirectoryError: floorplan_directory is invalid
    :raise FileMotFoundError: could not find floorplan file
    """

    if not floorplan_directory:
        floorplan_directory = su.get_datadir(facility, floor)
    floorplan = floorplan_from_directory(floorplan_directory, floor)

    floorplan.export_to_svg(outputfile, include_doors=doors)
    LOG.info("Floorplan exported to: %s", outputfile)


def build_navigation_network(
    facility: str, floor: str = "0", floorplan_directory: str = None, **kwargs
):  # noqa
    """Build the navigation network for a given facility floor plan.

    :param facility: Name of this facility
    :param floor: Name of this floor (default=0)
    :param floorplan_directory: Custom directory for floorplans (default=cache)
    :raise NotADirectoryError: floorplan_directory is invalid
    :raise FileMotFoundError: could not find floorplan file
    """

    if not floorplan_directory:
        floorplan_directory = su.get_datadir(facility, floor)
    floorplan = floorplan_from_directory(floorplan_directory, floor)

    LOG.info("Building navigation network...")
    navbuilder = NavigationBuilder(floorplan)
    navbuilder.build()

    hw_graph_file = os.path.join(floorplan_directory, "hallways_graph.json")
    floor_navnet_file = os.path.join(floorplan_directory, ROUTES_JSON_FILE)

    navbuilder.export_navdata_to_json(floor_navnet_file, hw_graph_file)


def update_floorplan_from_svg_file(
    svg: str,
    facility: str,
    floor: str = "0",
    floorplan_directory: str = None,
    **kwargs
):  # noqa
    """Update the walls and doors in a floorplan using an SVG file

    :param svg: Path to the floorplan file in SVG format
    :param facility: Name of this facility
    :param floor: Name of this floor (default=0)
    :param floorplan_directory: Custom directory for floorplans (default=cache)
    :raise NotADirectoryError: floorplan_directory is invalid
    :raise FileMotFoundError: could not find floorplan file
    """
    if not os.path.isfile(svg):
        raise FileNotFoundError(svg)

    if not floorplan_directory:
        floorplan_directory = su.get_datadir(facility, floor)

    floorplan = floorplan_from_directory(floorplan_directory, floor)
    fp_updater = FloorplanUpdater(floorplan, svg_file=svg)
    fp_updater.run()

    updated_json_file = os.path.join(
        floorplan_directory, "updated_floorplan.json"
    )
    fp_updater.floorplan.to_json_file(updated_json_file)


def export_navigation_graph_to_svg(
    facility: str,
    floor: str,
    outputfile: str,
    floorplan_directory: str = None,
    **kwargs
):  # noqa
    """Export navigation network to svg file for visualization.

    :param facility: Name of this facility
    :param floor: Name of this floor
    :param outputfile: Location to store output
    :param floorplan_directory: Custom directory for floorplans (default=cache)
    :raise NotADirectoryError: floorplan_directory is invalid
    :raise FileMotFoundError: could not find floorplan file
    """

    if not floorplan_directory:
        floorplan_directory = su.get_datadir(facility, floor)
    floorplan = floorplan_from_directory(floorplan_directory, floor)

    nav_network_file = os.path.join(floorplan_directory, ROUTES_JSON_FILE)
    if not os.path.isfile(nav_network_file):
        raise FileNotFoundError(nav_network_file)

    with open(nav_network_file, "r") as f:
        nav_data = json.load(f)

    nav_graph = nx.readwrite.json_graph.node_link_graph(nav_data)

    nav_nodes = []
    nav_paths = []
    for e in list(nav_graph.edges):
        nav_nodes.append(e[0])
        nav_nodes.append(e[1])
        p = Line(
            start=complex(e[0][0], e[0][1]), end=complex(e[1][0], e[1][1])
        )
        nav_paths.append(p)

    LOG.info("Exporting nav network to svg")
    bv.export_nav_network_to_svg(
        floorplan.walls, nav_paths, nav_nodes, outputfile
    )
    LOG.info("Navigation network exported to: %s", outputfile)


def load_floorplans(floors, facility_name, user_scale=None):
    # TODO: TEST ME
    # TODO: DOCUMENT ME!
    # TODO: TEST ME!
    # TODO: DOCUMENT ME!
    # TODO: TEST ME!
    # TODO: DOCUMENT ME!
    floorplans = []

    if user_scale is not None:
        user_scale = round(user_scale, 6)

    for fn in floors:
        LOG.info("Loading floorplan for floor: %s", fn)
        floorplan_directory = su.get_datadir(facility_name, fn)
        floorplan = floorplan_from_directory(
            floorplan_directory, fn, scale=user_scale
        )
        floorplans.append(floorplan)
    return floorplans


def run_simulation(inputs: dict):
    """Perform an agent-based simulation given a dictionary of input values

    :param inputs: Dictionary of input values
    """
    start_time = time.time()
    upload_results = inputs["upload_results"]
    upload_location = inputs["upload_location"]

    LOG.info("Loading floorplans...")
    floorplans = load_floorplans(inputs["floors"], inputs["facility_name"])

    if len(floorplans) > 0:
        model_inputs = deepcopy(inputs)
        del model_inputs["upload_results"]
        del model_inputs["upload_location"]
        del model_inputs["floors"]
        del model_inputs["output_directory"]
        facility = Facility(
            floorplans,
            model_inputs["entrances"],
            model_inputs["facility_name"],
            traffic_policy=model_inputs["traffic_policy"],
        )
        del model_inputs["entrances"]
        del model_inputs["facility_name"]
        del model_inputs["traffic_policy"]

        model_inputs["facility"] = facility
        my_model = Simulation(**model_inputs)
    else:
        raise ValueError("At least one floorplan must be provided.")

    work_directory = inputs["output_directory"]
    LOG.info("Running simulation...")
    my_model.run_serial(
        workdir=work_directory,
        sim_name=inputs["simulation_name"],
        run_name=inputs["run_name"],
    )

    LOG.info("Extracting stats...")
    my_model.save_outputs(work_directory)

    if upload_results and upload_location is not None:
        LOG.info("Uploading results to server...")
        cwd = os.getcwd()
        foldername = os.path.basename(cwd)
        os.chdir("..")
        try:
            os.system("s3cmd sync " + foldername + " " + upload_location)
        except Exception as e:
            LOG.error("Failed to upload results to S3. Error: %s", e)
        os.chdir(foldername)

    total_time = time.time() - start_time

    with open(work_directory + "timing.txt", "w") as outfile:
        outfile.write(str(total_time))

    LOG.info("Results were saved here: %s", work_directory)
    LOG.info("Elapsed time: %s sec", total_time)
    LOG.info("Done with everything")


def initialize_oneway_network(navnet: Graph) -> Graph:
    oneway_network = nx.Graph()
    for e in list(navnet.to_undirected().edges()):

        if (
            "node_type" not in navnet.nodes[e[0]]
            or "node_type" not in navnet.nodes[e[1]]
        ):
            continue
        if (
            navnet.nodes[e[0]]["node_type"] == "intersection"
            and navnet.nodes[e[1]]["node_type"] == "intersection"
        ):
            oneway_network.add_edge(e[0], e[1], inter_points=[], id=None)
    return oneway_network


def check_and_remove_node_from_oneway_network(node, oneway_network):
    neighbors = list(oneway_network.neighbors(node))
    if len(neighbors) == 2:
        # Verify that both neighbors and this node are collinear
        test_line = Line(
            start=complex(neighbors[0][0], neighbors[0][1]),
            end=complex(neighbors[1][0], neighbors[1][1]),
        )
        test_point = Point(x=node[0], y=node[1])
        if gsu.is_point_on_line(test_line, test_point, tol=1e-3):
            inter_points = []
            node_added = False
            for _, datadict in oneway_network.adj[node].items():
                inter_points += datadict["inter_points"]
                if not node_added:
                    inter_points.append(node)
                    node_added = True
            oneway_network.remove_node(node)
            oneway_network.add_edge(
                neighbors[0], neighbors[1], inter_points=inter_points
            )
            return True
    return False


def find_and_save_potential_one_way_aisles(
    facility: str,
    floor: str,
    outputfile: str,
    floorplan_directory: str = None,
    **kwargs
):  # noqa
    """Iterate over nodes and edges in the navigation network and identify
    segments that could potentially be assigned one-way traffic.

    Creates a list of potential one-way nav segments where each segment is a
    list of successive nodes belonging to that nav segment. Save the list
    for later retrieval and outputs it to an SVG file for the user.

    :param facility: Name of this facility
    :param floor: Name of this floor
    :param outputfile: Location to store output
    :param floorplan_directory: Custom directory for floorplans (default=cache)
    :raise NotADirectoryError: floorplan_directory is invalid
    :raise FileMotFoundError: could not find floorplan file
    :raise FileMotFoundError: could not find navnet file
    """

    if not floorplan_directory:
        floorplan_directory = su.get_datadir(facility, floor)
    floorplan = floorplan_from_directory(floorplan_directory, floor)

    nav_network_file = os.path.join(floorplan_directory, ROUTES_JSON_FILE)
    if not os.path.isfile(nav_network_file):
        raise FileNotFoundError(nav_network_file)

    with open(nav_network_file, "r") as f:
        navnet_data = json.load(f)
    nav_graph = nx.readwrite.json_graph.node_link_graph(navnet_data)

    LOG.info("Finding possible one way aisles from navigation network...")
    oneway_network = initialize_oneway_network(nav_graph)

    completed = False
    while not completed:
        completed = True
        for node in list(oneway_network.nodes()):
            # Remove node from graph if it has 2 neighbors
            if check_and_remove_node_from_oneway_network(node, oneway_network):
                completed = False  # graph has changed, start over
                break

    # Assign a unique name to each edge in oneway network
    for i, edge in enumerate(list(oneway_network.edges())):
        oneway_network[edge[0]][edge[1]]["id"] = str(i)

    # Save oneway network to json file
    oneway_net_json_file = os.path.join(
        floorplan_directory, "oneway_network.json"
    )
    oneway_dict = nx.readwrite.json_graph.node_link_data(oneway_network)
    with open(oneway_net_json_file, "w") as f:
        json.dump(oneway_dict, f)

    LOG.info("File saved: %s", oneway_net_json_file)

    bv.export_possible_oneway_aisles_to_svg(
        floorplan.walls, oneway_network, outputfile
    )
    LOG.info("Possible one-way aisles exported to %s", outputfile)
