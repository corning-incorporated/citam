#  Copyright 2020. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the licenses granted by
#  Corning Incorporated. All other uses as well as any copying, modification
#  or reverse engineering of the software is strictly prohibited.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
#  ==========================================================================

"""The CITAM CLI"""

import argparse
import logging

from citam.api import run_server
from citam.engine import engine_run
from citam.engine.main import ingest_floorplan
from citam.engine.main import export_floorplan_to_svg
from citam.engine.main import list_facilities
from citam.engine.main import build_navigation_network
from citam.engine.main import update_floorplan_from_svg_file
from citam.engine.main import export_navigation_graph_to_svg
from citam.engine.main import find_and_save_potential_one_way_aisles


def main():
    """CLI Entrypoint"""
    parser = get_parser()
    try:
        args = parser.parse_args()
    except TypeError:
        parser.print_help()
    else:
        if args.verbose > 2:
            args.verbose = 2
        log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
        if args.log_file:
            logging.basicConfig(
                filename=args.log_file, level=log_levels[args.verbose]
            )
        else:
            logging.basicConfig(level=log_levels[args.verbose])
        # The below logger is annoying. TODO: Replace with real log config
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
        args.func(**vars(args))


def get_parser():
    """
    Create the CLI argparse instance.

    .. note::
        this is a big CLI, so parser generation has been split into multiple
        methods in an attempt to make reading this easier.

    https://docs.python.org/dev/library/argparse.html
    """
    parser = argparse.ArgumentParser(
        prog="citam",
        description="The CITAM CLI",
    )
    global_args = argparse.ArgumentParser(
        add_help=False,
    )
    global_args.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="can be supplied multiple times to increase verbosity",
    )
    global_args.add_argument("--log-file", type=str, help="log file location")

    subparsers = parser.add_subparsers(
        metavar="<command>",
        required=True,
    )

    _add_engine_commands(subparsers, global_args)
    _add_config_commands(subparsers, global_args)
    _add_dash_commands(subparsers, global_args)

    return parser


def _add_engine_commands(subparser, global_args):
    """
    Add ``engine`` sub-command to the parser

    :params argparse.ArgumentParser subparser:
        Subparsers instance for attaching child parsers to
    :params argparse.ArgumentParser global_args:
        Global arguments to use as parent for spawned parsers
    """
    engine = subparser.add_parser(
        "engine",
        parents=[global_args],
        help="Interact with the CITAM simulation engine",
    )
    engine_commands = engine.add_subparsers(
        metavar="<engine_command>",
        required=True,
    )

    ingest = engine_commands.add_parser(
        "ingest",
        parents=[global_args],
        help="Ingest raw floor plans and metadata files",
    )
    ingest.set_defaults(func=ingest_floorplan)
    ingest.add_argument("facility", type=str, help="Facility name")
    ingest.add_argument("floor", type=str, help="Floor name")
    ingest.add_argument(
        "-c",
        "--csv",
        type=str,
        required=False,
        default=None,
        help="CSV file with metadata for each space found in map file",
    )
    ingest.add_argument(
        "-s",
        "--svg",
        type=str,
        required=True,
        help="Map file to ingest in SVG format.",
    )
    ingest.add_argument(
        "--output_dir",
        type=str,
        required=False,
        help="Directory to save ingestion files",
    )
    ingest.add_argument(
        "-b",
        "--buildings",
        type=str,
        nargs="+",
        required=False,
        help="Buildings to process. Default to 'all'.",
    )
    ingest.add_argument(
        "-f",
        "--force_overwrite",
        action="store_true",
        help="Force overwrite of existing files.",
    )

    update_floorplan = engine_commands.add_parser(
        "update-floorplan",
        parents=[global_args],
        help="Update the floorplan data for a given simulation",
    )
    update_floorplan.set_defaults(func=update_floorplan_from_svg_file)
    update_floorplan.add_argument("facility", type=str, help="Facility name")
    update_floorplan.add_argument("floor", type=str, help="Facility name")
    update_floorplan.add_argument(
        "-s", "--svg", type=str, required=True, help="Raw map SVG file"
    )

    list_fac = engine_commands.add_parser(
        "list",
        parents=[global_args],
        help="List all the floorplans already ingested.",
    )
    list_fac.set_defaults(func=list_facilities)

    export_floorplan = engine_commands.add_parser(
        "export-floorplan",
        parents=[global_args],
        help="Export a floorplan to an SVG file",
    )
    export_floorplan.set_defaults(func=export_floorplan_to_svg)
    export_floorplan.add_argument("facility", type=str, help="facility name")
    export_floorplan.add_argument("floor", type=str, help="Floor name")
    export_floorplan.add_argument(
        "-o", "--outputfile", type=str, required=True, help="Path to svg file"
    )
    export_floorplan.add_argument(
        "-d",
        "--doors",
        action="store_true",
        help="Include doors in output.",
    )

    export_navnet = engine_commands.add_parser(
        "export-navnet",
        parents=[global_args],
        help="Export the navigation newtork to an SVG file",
    )
    export_navnet.set_defaults(func=export_navigation_graph_to_svg)
    export_navnet.add_argument("facility", type=str, help="facility name")
    export_navnet.add_argument("floor", type=str, help="facility name")
    export_navnet.add_argument(
        "-o", "--outputfile", type=str, required=True, help="Path to svg file"
    )

    export_potential_one_way_aisles = engine_commands.add_parser(
        "export-potential-oneways",
        parents=[global_args],
        help="Export potential one-way ailes to an SVG file",
    )
    export_potential_one_way_aisles.set_defaults(
        func=find_and_save_potential_one_way_aisles
    )
    export_potential_one_way_aisles.add_argument(
        "facility", type=str, help="facility name"
    )
    export_potential_one_way_aisles.add_argument(
        "floor", type=str, help="facility name"
    )
    export_potential_one_way_aisles.add_argument(
        "-o", "--outputfile", type=str, required=True, help="Path to svg file"
    )

    build_network = engine_commands.add_parser(
        "build-navnet",
        parents=[global_args],
        help="Build the navigation network",
    )
    build_network.set_defaults(func=build_navigation_network)
    build_network.add_argument("facility", type=str, help="Facility name")
    build_network.add_argument("floor", type=str, help="Floor name")

    run = engine_commands.add_parser(
        "run", parents=[global_args], help="Run a simulation for a facility"
    )
    run.set_defaults(func=engine_run)
    run.add_argument(
        "input_file",
        type=str,
        help="full path of file with simulation inputs",
    )


def _add_config_commands(subparser, global_args):
    """
    Add ``config`` sub-command to the parser

    :params argparse.ArgumentParser subparser:
        Subparsers instance for attaching child parsers to
    :params argparse.ArgumentParser global_args:
        Global arguments to use as parent for spawned parsers
    """

    config = subparser.add_parser(
        "config",
        parents=[global_args],
        help="Interact with the CITAM global configuration",
    )
    config.set_defaults(func=_placeholder_func)
    config.add_argument(
        "get",
        help="Print the current CITAM configuration",
    )


def _add_dash_commands(subparser, global_args):
    """
    Add ``dash`` sub-command to the parser

    :params argparse.ArgumentParser subparser:
        Subparsers instance for attaching child parsers to
    :params argparse.ArgumentParser global_args:
        Global arguments to use as parent for spawned parsers
    """
    dash = subparser.add_parser(
        "dash",
        parents=[global_args],
        help="Start the CITAM dashboard",
    )
    dash.set_defaults(func=run_server)
    dash.add_argument(
        "-p",
        "--port",
        default=8000,
        type=int,
        help="The port to use for the dashboard",
    )
    dash.add_argument(
        "--host",
        default="127.0.0.1",
        type=str,
        help="The host to serve the dashboard from",
    )
    dash.add_argument(
        "-r",
        "--results",
        type=str,
        help="The directory to look for results in",
    )


def _placeholder_func(*args, **kwargs):
    """
    This is a placeholder function for subcommands which
    are not yet implemented
    """
    raise NotImplementedError("This feature has not been implemented yet")


if __name__ == "__main__":
    main()
