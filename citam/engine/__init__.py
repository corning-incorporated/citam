# __all__ = [
#     'basic_visualization',
#     'citam',
#     'constants',
#     'contact_events',
#     'daily_schedule',
#     'door',
#     'employee',
#     'floorplan',
#     'floorplan_ingester',
#     'floorplan_utils',
#     'geometry_and_svg_utils',
#     'meeting_policy',
#     'model',
#     'navigation',
#     'navigation_builder',
#     'point',
#     'space',
# ]

import logging
import os

from citam.engine.main import run_simulation
from citam.engine.input_parser import parse_input_file

LOG = logging.getLogger(__name__)


def engine_run(**kwargs):
    """Run a simulation

    This method is executed with the CLI call ``citam engine run``
    """
    LOG.info("Preparing to run simulation")
    work_directory = kwargs.get(
        'work_dir',
        os.path.abspath(os.getcwd())
    )
    LOG.debug("Working directory: '%s'", work_directory)
    LOG.debug("Loading input file: %s", kwargs['input_file'])

    input_dict = parse_input_file(kwargs['input_file'])
    if input_dict is None:
        logging.fatal('Error loading input file. Please double check.')
        logging.info('Done.')
        return
    LOG.info("Starting simulation")
    run_simulation(input_dict)
    LOG.info("Simulation has completed")
