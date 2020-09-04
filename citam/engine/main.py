
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


from citam.engine.floorplan_ingester import FloorplanIngester
from citam.engine.model import FacilityTransmissionModel
from citam.engine.floorplan import Floorplan
import citam.engine.basic_visualization as bv
from citam.engine.navigation_builder import NavigationBuilder
from citam.engine.floorplan_updater import FloorplanUpdater
import citam.engine.storage_utils as su
import citam.engine.geometry_and_svg_utils as gsu
from citam.engine.point import Point

from svgpathtools import Line

import logging
import pickle
import os
import time
import errno
from copy import deepcopy
import networkx as nx


def list_facilities(**kwargs):
    """List all the floorplans already ingested
    """

    location = kwargs['location']
    if location != 'cache':
        print('ERROR: unknown location: ', location, 'Supported values: cache')
    floorplans_directory = su.get_floorplans_directory()
    if not os.path.isdir(floorplans_directory):
        print('No facility found.')
    else:
        subdirs = [f for f in os.listdir(floorplans_directory)
                   if os.path.isdir(os.path.join(floorplans_directory, f))
                   ]
        if len(subdirs) == 0:
            print('No facility found')
        else:
            print('Current facilities: ')
            for f in subdirs:
                print(f)

    return


def ingest_floorplan(**kwargs):
    """Ingest raw floorplan and data files for a given floor of a facility.

    This method is executed with the CLI call ``citam engine ingest``

    Paramters
    ----------
    map: str
        Path to the floorplan file in SVG format
    csv: str
        Path to the floorplan metadata file in CSV format
    facility: str
        Name of this facility
    scale: float (optional)
        The scale of the drawing (default = 1/12)
    floor_name: str (optional)
        Name of this floor (default=0)

    Returns
    --------
    bool
        Whether the process was successful or not

    Raises
    -------
    FileNotFoundError
        If input files are not found
    """

    svg_file = kwargs['map']
    csv_file = kwargs['csv']
    facility_name = kwargs['facility']
    if 'floor_name' in kwargs:
        floor_name = kwargs['floor_name']
    else:
        logging.info('No value provided for floor name. Will use the ' +
                     'default value of "0"'
                     )
        floor_name = '0'
    if 'scale' in kwargs:
        scale = kwargs['scale']
    else:
        logging.info('No value provided for the floorplan scale. Will use ' +
                     'the default value of 1/12 [ft/drawing unit]'
                     )
        scale = 1.0/12.0

    output_directory = None
    if 'output_directory' in kwargs:
        output_directory = kwargs['output_directory']

    if not svg_file.endswith('.svg'):
        logging.error('Only svg files are supported. Error with ' + svg_file)
        return False

    if not csv_file.endswith('.csv'):
        logging.error('Only svg files are supported. Error with ' + csv_file)
        return False

    if not os.path.isfile(svg_file):
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), svg_file)

    if not os.path.isfile(csv_file):
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), csv_file)

    if output_directory is None:
        floor_directory = su.get_datadir(facility_name, floor_name)
        if not os.path.isdir(floor_directory):
            su.create_datadir(facility_name, floor_name)
    else:
        floor_directory = output_directory
        if not os.path.isdir(floor_directory):
            try:
                os.mkdir(floor_directory)
            except Exception as e:
                logging.exception(e)
                return False

    logging.info('Ingesting floorplan...')
    floorplan_ingester = FloorplanIngester(svg_file,
                                           csv_file,
                                           scale,
                                           extract_doors_from_file=True
                                           )
    floorplan_ingester.run()

    logging.info('Saving floorplan to pickle file...')
    fp_pickle_file = os.path.join(floor_directory, 'floorplan.pkl')
    floorplan_ingester.export_data_to_pickle_file(fp_pickle_file)
    logging.info('Done.')

    return True


def export_floorplan_to_svg(**kwargs):
    """Export a given floorplan to an SVG file for visualization and editing.

    Parameters
    -----------
    - facility: str (set to None if floorplan directory is provided)
    - floor: str (set to None if floorplan directory is provided)
    - floorplan_directory: str (optional)
    - outputfile: str (required)

    Returns
    --------
    bool:
        Whether the export was successful or not
    """

    svg_file = kwargs['outputfile']
    if not svg_file.endswith('.svg'):
        logging.fatal('Invalid file type. Can only export to svg.')
        return False

    output_dir = os.path.dirname(svg_file)
    if not os.path.isdir(output_dir):
        logging.fatal('Invalid output directory: ' + str(output_dir))
        return False

    facility_name = kwargs['facility']
    floor_name = kwargs['floor']

    if 'floorplan_directory' in kwargs:
        floor_directory = kwargs['floorplan_directory']
    else:
        floor_directory = su.get_datadir(facility_name, floor_name)

    if not os.path.isdir(floor_directory):
        logging.fatal('Floor directory not found: ' + str(floor_directory))
        return False

    fp_pickle_file = os.path.join(floor_directory, 'updated_floorplan.pkl')
    if not os.path.isfile(fp_pickle_file):
        fp_pickle_file = os.path.join(floor_directory, 'floorplan.pkl')

    if os.path.isfile(fp_pickle_file):

        with open(fp_pickle_file, 'rb') as f:
            spaces, doors, walls, special_walls, aisles, width, height, \
                scale = pickle.load(f)
        logging.info('Floorplan successfully loaded.')

    else:
        logging.fatal('Could not find floorplan file. Please double check.')
        return False

    floorplan = Floorplan(scale=scale,
                          spaces=spaces,
                          doors=doors,
                          walls=walls,
                          special_walls=special_walls,
                          aisles=aisles,
                          width=width,
                          height=height,
                          floor_name=floor_name
                          )

    floorplan.export_to_svg(svg_file)
    logging.info('Floorplan exported to : ' + svg_file)

    return True


def build_navigation_network(**kwargs):
    """Build the navigation network for a given facility floor plan.
    """

    facility_name = kwargs['facility']
    floor_name = kwargs['floor']
    if 'floor_name' in kwargs:
        floor_name = kwargs['floor_name']
    else:
        logging.info('No value provided for floor name. Will use the ' +
                     'default value of "0"'
                     )
        floor_name = '0'

    if 'floorplan_directory' in kwargs:
        floorplan_directory = kwargs['floorplan_directory']
    else:
        floorplan_directory = su.get_datadir(facility_name, floor_name)
    floorplan_pickle_file = os.path.join(floorplan_directory,
                                         'updated_floorplan.pkl'
                                         )
    if not os.path.isfile(floorplan_pickle_file):
        floorplan_pickle_file = os.path.join(floorplan_directory,
                                             'floorplan.pkl'
                                             )

    if os.path.isfile(floorplan_pickle_file):

        with open(floorplan_pickle_file, 'rb') as f:
            spaces, doors, walls, special_walls, aisles, width, height, \
                scale = pickle.load(f)
        print('Floorplan successfully loaded from: ',  floorplan_pickle_file)

    else:
        logging.error('Floorplan file not found: ' + floorplan_pickle_file)
        return False

    floorplan = Floorplan(scale=scale,
                          spaces=spaces,
                          doors=doors,
                          walls=walls,
                          aisles=aisles,
                          width=width,
                          height=height,
                          floor_name=floor_name,
                          special_walls=special_walls)

    logging.info('Building navigation network...')
    navbuilder = NavigationBuilder(floorplan)
    navbuilder.build()

    hw_graph_file = os.path.join(floorplan_directory, 'hallways_graph.pkl')
    floor_route_graph_file = os.path.join(floorplan_directory, 'routes.pkl')

    navbuilder.export_navdata_to_pkl(floor_route_graph_file, hw_graph_file)

    return True


def update_floorplan_from_svg_file(**kwargs):
    """Given a facility floor plan, use data from a user-provided svg file to
    update the walls and doors.
    """
    edited_svg_file = kwargs['map']
    facility_name = kwargs['facility']
    floor_name = kwargs['floor']
    if 'floor_name' in kwargs:
        floor_name = kwargs['floor_name']
    else:
        logging.info('No value provided for floor name. Will use the ' +
                     'default value of "0"'
                     )
        floor_name = '0'

    if not os.path.isfile(edited_svg_file):
        logging.error('File not found: ' + edited_svg_file)
        return False

    if not edited_svg_file.endswith('svg'):
        logging.error('Invalid file type. Only svg files are supported.')
        return False

    if 'floorplan_directory' in kwargs:
        floorplan_directory = kwargs['floorplan_directory']
    else:
        floorplan_directory = su.get_datadir(facility_name, floor_name)

    initial_pickle_file = os.path.join(floorplan_directory, 'floorplan.pkl')
    updated_pickle_file = os.path.join(floorplan_directory,
                                       'updated_floorplan.pkl'
                                       )

    if os.path.isfile(initial_pickle_file):

        with open(initial_pickle_file, 'rb') as f:
            spaces, doors, walls, special_walls, aisles, width, height, \
                scale = pickle.load(f)
        logging.info('Floorplan loaded from: ' + initial_pickle_file)

    else:
        logging.info('Facility floorplan file not found' + initial_pickle_file)
        return False

    logging.info('Initializing floorplan with: ')
    logging.info(str(len(doors)) + ' doors')
    logging.info(str(len(walls)) + ' walls')

    floorplan = Floorplan(scale=scale,
                          spaces=spaces,
                          doors=doors,
                          walls=walls,
                          aisles=aisles,
                          width=width,
                          height=height,
                          special_walls=special_walls,
                          floor_name=floor_name
                          )

    fp_updater = FloorplanUpdater(floorplan, svg_file=edited_svg_file)
    fp_updater.run()
    fp_updater.export_floorplan_to_pickle_file(updated_pickle_file)

    return True


def export_navigation_graph_to_svg(**kwargs):
    """Export navigation network to svg file for visualization.
    """

    svg_file = kwargs['outputfile']
    if not svg_file.endswith('.svg'):
        logging.error('Invalid file type. Can only export to svg.')
        return False

    dirname = os.path.dirname(svg_file)
    if not dirname:
        logging.error('Output directory not found: ' + dirname)
        return False

    facility_name = kwargs['facility']
    floor_name = kwargs['floor']

    if 'floorplan_directory' in kwargs:
        floorplan_directory = kwargs['floorplan_directory']
    else:
        floorplan_directory = su.get_datadir(facility_name, floor_name)
    if not os.path.isdir(floorplan_directory):
        logging.fatal('Directory with facility files not found.')
        return False

    floorplan_file = os.path.join(floorplan_directory, 'updated_floorplan.pkl')
    if not os.path.isfile(floorplan_file):
        floorplan_file = os.path.join(floorplan_directory, 'floorplan.pkl')

    nav_network_file = os.path.join(floorplan_directory, 'routes.pkl')

    logging.info('Loading files...')
    try:
        with open(floorplan_file, 'rb') as f:
            spaces, doors, walls, special_walls, aisles, width, height, \
                scale = pickle.load(f)
    except Exception as e:
        logging.exception(e)
        return False

    try:
        with open(nav_network_file, 'rb') as f:
            nav_graph = pickle.load(f)
    except Exception as e:
        logging.exception(e)
        return False

    nav_nodes = []
    nav_paths = []
    for e in list(nav_graph.edges):
        nav_nodes.append(e[0])
        nav_nodes.append(e[1])
        p = Line(start=complex(e[0][0], e[0][1]),
                 end=complex(e[1][0], e[1][1])
                 )
        nav_paths.append(p)
    logging.info('Exporting...')
    try:
        bv.export_nav_network_to_svg(walls, nav_paths, nav_nodes, svg_file)
    except Exception as e:
        logging.exception(e)
        return False

    logging.info('Navigation nework exported to : ' + svg_file)

    return True


def load_floorplans(floors,
                    facility_name,
                    user_scale=None,
                    buildings_to_keep=['all']
                    ):

    floorplans = []

    for fn in floors:
        logging.info('Loading floorplan for floor: ' + str(fn))

        floorplan_directory = su.get_datadir(facility_name, fn)
        if not os.path.isdir(floorplan_directory):
            logging.fatal('Cannot load data for floor : ' + str(fn) +
                          '\nFloorplan directory is: ' + floorplan_directory)

            return []

        floorplan_file = os.path.join(floorplan_directory,
                                      'updated_floorplan.pkl'
                                      )
        if os.path.isfile(floorplan_file):
            with open(floorplan_file, 'rb') as f:
                spaces, doors, walls, special_walls, aisles, width, height, \
                    scale = pickle.load(f)
                logging.info('.............success')

            if user_scale is not None:
                scale = round(user_scale, 6)

            logging.info('Scale: ' + str(scale) + ' [ft/drawing unit]')
            floorplan = Floorplan(scale=scale,
                                  spaces=spaces,
                                  doors=doors,
                                  walls=walls,
                                  aisles=aisles,
                                  width=width,
                                  height=height,
                                  floor_name=fn,
                                  special_walls=special_walls
                                  )

            floorplans.append(floorplan)

        else:
            logging.error('Could not find floorplan file' + floorplan_file)
            return []

    return floorplans


def run_simulation(inputs):
    """ Perform an agent-based simulation given a dictionary of input values

    Parameters
    -----------
    input_dic: dict
        Dictionary of input values

    Returns
    --------
    None
    """
    start_time = time.time()
    upload_results = inputs['upload_results']
    upload_location = inputs['upload_location']

    logging.info('Loading floorplans...')
    floorplans = load_floorplans(inputs['floors'], inputs['facility_name'])

    if len(floorplans) > 0:
        model_inputs = deepcopy(inputs)
        model_inputs['floorplans'] = floorplans
        del model_inputs['upload_results']
        del model_inputs['upload_location']
        del model_inputs['floors']
        del model_inputs['output_directory']
        my_model = FacilityTransmissionModel(**model_inputs)
    else:
        logging.info('Nothing to do.')
        return False
    # my_model.run_parallel(sim_name=sim_name,
    #                       n_processes=2,
    #                       workdir=work_directory,
    #                       n_agents=10,
    #                     )

    sim_id = 'sim_id_0001'
    work_directory = inputs['output_directory']
    logging.info('Running simulation...')
    my_model.run_serial(sim_name=sim_id, workdir=work_directory)

    logging.info('Extracting stats...')
    my_model.save_outputs(work_directory)

    if upload_results and upload_location is not None:
        logging.info('Uploading results to server...')
        cwd = os.getcwd()
        foldername = os.path.basename(cwd)
        os.chdir('..')
        os.system('s3cmd sync ' + foldername + ' ' + upload_location)
        os.chdir(foldername)
    else:
        pass

    total_time = time.time() - start_time

    with open(work_directory + 'timing.txt', 'w') as outfile:
        outfile.write(str(total_time))

    logging.info('Results were saved here: ' + str(work_directory))
    logging.info('Elapsed time: ' + str(total_time) + ' sec\n')
    logging.info('Done with everything.')

    return True


def find_and_save_potential_one_way_aisles(**kwargs):
    """Iterate over nodes and edges in the navigation network and identify
    segments that could potentially be assigned one-way traffic.

    Creates a list of potential one-way nav segments where each segment is a
    list of successive nodes belonging to that nav segment. Save the list
    for later retrieval and outputs it to an SVG file for the user.
    """

    svg_file = kwargs['outputfile']
    if not svg_file.endswith('.svg'):
        logging.error('Invalid file type. Can only export to svg.')
        return False

    dirname = os.path.dirname(svg_file)
    if not dirname:
        logging.error('Output directory not found: ' + dirname)
        return False

    facility_name = kwargs['facility']
    floor_name = kwargs['floor']

    if 'floorplan_directory' in kwargs:
        floorplan_directory = kwargs['floorplan_directory']
    else:
        floorplan_directory = su.get_datadir(facility_name, floor_name)
    if not os.path.isdir(floorplan_directory):
        logging.fatal('Directory with facility files not found.')
        return False

    floorplan_file = os.path.join(floorplan_directory, 'updated_floorplan.pkl')
    if not os.path.isfile(floorplan_file):
        floorplan_file = os.path.join(floorplan_directory, 'floorplan.pkl')

    nav_network_file = os.path.join(floorplan_directory, 'routes.pkl')

    logging.info('Loading files...')
    try:
        with open(floorplan_file, 'rb') as f:
            spaces, doors, walls, special_walls, aisles, width, height, \
                scale = pickle.load(f)
    except Exception as e:
        logging.exception(e)
        return False

    try:
        with open(nav_network_file, 'rb') as f:
            nav_graph = pickle.load(f)
    except Exception as e:
        logging.exception(e)
        return False

    logging.info('Finding possible one way aisles from navigation network...')
    oneway_network = nx.Graph()
    for e in list(nav_graph.to_undirected().edges()):
        if 'node_type' not in nav_graph.nodes[e[0]]:
            continue
        if 'node_type' not in nav_graph.nodes[e[1]]:
            continue
        if nav_graph.nodes[e[0]]['node_type'] == 'intersection' and \
                nav_graph.nodes[e[1]]['node_type'] == 'intersection':
            oneway_network.add_edge(e[0], e[1], inter_points=[], id=None)

    completed = False
    while not completed:
        completed = True
        for node in list(oneway_network.nodes()):
            neighbors = list(oneway_network.neighbors(node))
            # Remove node from graph if it has 2 neighbors
            if len(neighbors) == 2:
                # Verify that both neighbors and this node are collinear
                test_line = Line(start=complex(neighbors[0][0],
                                               neighbors[0][1]),
                                 end=complex(neighbors[1][0],
                                             neighbors[1][1])
                                 )
                test_point = Point(x=node[0], y=node[1])
                if gsu.is_point_on_line(test_line,
                                        test_point,
                                        tol=1e-3
                                        ):
                    inter_points = []
                    node_added = False
                    for nbr, datadict in oneway_network.adj[node].items():
                        inter_points += datadict['inter_points']
                        if not node_added:
                            inter_points.append(node)
                            node_added = True
                    oneway_network.remove_node(node)
                    oneway_network.add_edge(neighbors[0],
                                            neighbors[1],
                                            inter_points=inter_points
                                            )
                    completed = False
                    break

    # Assign a unique name to each edge in oneway network
    for i, edge in enumerate(list(oneway_network.edges())):
        oneway_network[edge[0]][edge[1]]['id'] = str(i)

    # Save oneway network to pickle file
    oneway_net_pkl_file = os.path.join(floorplan_directory,
                                       'onewway_network.pkl'
                                       )
    with open(oneway_net_pkl_file, 'wb') as f:
        pickle.dump(oneway_network, f)
    try:   # Export to SVG file
        bv.export_possible_oneway_aisles_to_svg(walls,
                                                oneway_network,
                                                svg_file
                                                )
    except Exception as e:
        logging.exception(e)
        return False

    logging.info('Possible one-way aisles exported to : ' + svg_file)

    return True
