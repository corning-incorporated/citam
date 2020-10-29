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

"""
    Author: Mardochee Reveil

"""
import csv
import os
import logging
import errno
import json

from svgpathtools import svg2paths, Line

from citam.engine.constants import REQUIRED_SPACE_METADATA
from citam.engine.constants import OPTIONAL_SPACE_METADATA
from citam.engine.constants import SUPPORTED_SPACE_FUNCTIONS

LOG = logging.getLogger(__name__)


class MissingInputError(TypeError):
    pass


def parse_csv_metadata_file(csv_file):
    """Read and parse CSV floorplan metadata file.

    Ensure all expected columns are present, there is no missing
    entry and values are valid. Ignore unncessary columns. The expected
    columns are (see constants.py for full updated list):
    - ID
    - Campus
    - Building
    - Unique_name
    - Space_function
    - Space_category (optional)
    - Department (optional)
    - Capacity (optional)
    - Square_Footage (optional)

    Parameters
    ----------
    csv_file: str
        Absolute path to csv file

    Returns
    --------
    list
        List of dictionaries (one dict per entry in the CSV file) with column
        headers as keys
    """

    if not os.path.isfile(csv_file):
        LOG.fatal("File not found. %s", csv_file)
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), csv_file
        )

    supported_columns = REQUIRED_SPACE_METADATA + OPTIONAL_SPACE_METADATA
    space_info = []
    with open(csv_file, mode="r") as infile:
        reader = csv.reader(infile)
        for i, row in enumerate(reader):

            if i == 0:
                header = [v.lower() for v in row]
                for required_data in REQUIRED_SPACE_METADATA:
                    if required_data not in header:
                        msg = f"{required_data} column is missing in csv file"
                        raise ValueError(msg)
            else:
                row_data = {}
                if len(row) != len(header):
                    raise ValueError(f"Wrong number of columsn in row {i+1}")
                for c, name in enumerate(header):
                    value = row[c]
                    if str(value) == "" and name in required_data:
                        msg = f"No '{name}' found in this row {i+1}"
                        raise ValueError(msg)

                    if header[c] in supported_columns:
                        row_data[header[c]] = value.lower()
                        if (
                            header[c] == "space_function"
                            and value.lower() not in SUPPORTED_SPACE_FUNCTIONS
                        ):

                            msg = f"Invalid space function: '{value}' in row \
                                    {i+1}. Valid entries are: \
                                    {SUPPORTED_SPACE_FUNCTIONS}"
                            raise ValueError(msg)

                space_info.append(row_data)

    return space_info


def parse_svg_floorplan_file(svg_file):

    """Read and parse SVG floorplan file.

    Each space is represented by a path element with and id that matches the
    id in the csv file.

    Parameters
    ----------
    svg_file: str
        Absolute path to csv file

    Returns
    --------
    space_paths: list of Path
        List of path elements
    space_attributes: list of dict
        List of attributres (key:value) pairs found in the svg file
    door_paths: list of Path
        Paths labeled as doors in the svg file
    """

    if not os.path.isfile(svg_file):
        LOG.fatal("File not found. %s", svg_file)
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), svg_file
        )

    paths, attributes = svg2paths(svg_file)

    door_paths = []
    space_paths = []
    space_attributes = []

    # TODO: Change this to expect a path_type attribute for each path
    for path, attr in zip(paths, attributes):
        for i, line in enumerate(path):
            new_start = complex(
                int(round(line.start.real)), int(round(line.start.imag))
            )
            new_end = complex(
                int(round(line.end.real)), int(round(line.end.imag))
            )
            new_line = Line(start=new_start, end=new_end)
            path[i] = new_line

        if "id" not in attr:
            door_paths.append(path)
        else:
            space_paths.append(path)
            space_attributes.append(attr)

    LOG.info("Number of door paths: %d", len(door_paths))
    LOG.info("Number of space paths: %d", len(space_paths))

    return space_paths, space_attributes, door_paths


def parse_meetings_policy_file(json_filepath):
    """Read and parse the json meeting policy file.

    The meetings policy for a given facility exposes parameters
    for when, where, how often and how long meetings take place
    in the facility.
    """
    meetings_policy_params = None
    if os.path.isfile(json_filepath):
        with open(json_filepath, "r") as f:
            meetings_policy_params = json.load(f)
    else:
        LOG.error("Could not find input file: {%s}", json_filepath)
        raise FileNotFoundError(json_filepath)

    return meetings_policy_params


def parse_scheduling_policy_file(json_filepath):
    """Read and parse the json scheduling policy file.

    Together with the meetings policy file, this file encodes
    how and when people will be moving within a given facility.
    Scheduling policies revolve around the concept of "scheduling
    purpose" which ties them to a category of space in the floorplan.
    See the documentation for more information.

    TODO: Each employee group can have their own scheduling policy (e.g.
    managers vs technicians).
    """
    if os.path.isfile(json_filepath):
        with open(json_filepath, "r") as f:
            scheduling_policy = json.load(f)
        return scheduling_policy
    else:
        LOG.error("Could not find input file: {%s}", json_filepath)
        raise FileNotFoundError(json_filepath)


def parse_input_file(input_file):
    """Read primary simulation input file in json format, validate values,
    load floorplans and returns dictionary of model inputs.

    Parameters
    -----------
    input_file: str
        Full path to input file expected in json format

    Returns
    --------
    dict
        The dictionary of inputs
    """

    if os.path.isfile(input_file):
        with open(input_file, "r") as f:
            try:
                input_dict = json.load(f)
            except json.JSONDecodeError as err:
                raise ValueError(
                    f"{input_file} is not a valid JSON file."
                ) from err
    else:
        LOG.error("Could not find input file: %s", input_file)
        raise FileNotFoundError(input_file)

    # Make sure all required values are provided
    if "facility_name" not in input_dict:
        raise MissingInputError('"facility_name" is a required input')

    if "floors" not in input_dict:
        raise MissingInputError('"floors" is a required input')

    if "entrances" not in input_dict:
        raise MissingInputError('"entrances" is a required input')

    if "daylength" not in input_dict:
        raise MissingInputError('"daylenth" is a required input')

    if "entrance_time" not in input_dict:
        raise MissingInputError('"entrance_time" is a required input.')

    if "n_agents" not in input_dict:
        raise MissingInputError('"n_agents" is a required input')

    # Make sure all required values are of the correct type
    facility_name = input_dict["facility_name"]
    if not isinstance(facility_name, str):
        raise TypeError("facility_name must be a string")

    floors = input_dict["floors"]
    if not isinstance(floors, list):
        raise TypeError("floors must be a list")
    if len(floors) == 0:
        raise ValueError("At least one floor is required.")
    if len(set(floors)) != len(floors):
        raise ValueError("Duplicates found in list of floors")

    n_agents = input_dict["n_agents"]
    if not isinstance(n_agents, int):
        raise TypeError("n_agents must be an integer")

    daylength = input_dict["daylength"]
    if not isinstance(daylength, int):
        raise TypeError("daylength must be an integer.")

    entrances = input_dict["entrances"]
    if not isinstance(entrances, list):
        raise TypeError("entrances must be a list")

    buffer = input_dict["entrance_time"]
    if not isinstance(buffer, int):
        raise TypeError("entrance time must be an integer")

    # Optional arguments
    upload_results = False
    if "upload_results" in input_dict:
        upload_results = input_dict["upload_results"]

    upload_location = None
    if "upload_location" in input_dict:
        upload_location = input_dict["upload_location"]

    if upload_results and upload_location is None:
        raise ValueError("upload_location must be specified.")

    occupancy_rate = None
    if "occupancy_rate" in input_dict:
        occupancy_rate = input_dict["occupancy_rate"]

    floorplan_scale = 1.0 / 12.0
    if "floorplan_scale" in input_dict:
        floorplan_scale = input_dict["floorplan_scale"]

    if not isinstance(floorplan_scale, float):
        raise TypeError("Floorplan scale must be a float")

    contact_distance = 6.0
    if "contact_distance" in input_dict:
        contact_distance = input_dict["contact_distance"]

    shifts = [
        {"name": "primary", "start_time": buffer, "percent_workforce": 1.0}
    ]
    if "shifts" in input_dict:
        shifts = input_dict["shifts"]
    if not isinstance(shifts, list):
        raise TypeError("shifts must be a list")

    scheduling_policy = None
    if "scheduling_policy_file" in input_dict:
        if os.path.isfile(input_dict["scheduling_policy_file"]):
            scheduling_policy = parse_scheduling_policy_file(
                input_dict["scheduling_policy_file"]
            )
        else:
            raise FileNotFoundError(input_dict["scheduling_policy_file"])

    meetings_policy = None
    if "meetings_file" in input_dict:
        if os.path.isfile(input_dict["meetings_file"]):
            meetings_policy = parse_meetings_policy_file(
                input_dict["meetings_file"]
            )
        else:
            raise FileNotFoundError(input_dict["meetings_file"])

    traffic_policy = None
    if "traffic_policy" in input_dict:
        if not isinstance(input_dict["traffic_policy"], list):
            raise TypeError(
                "traffic_policy must be a list. Found {%s}",
                type(traffic_policy),
            )

        for pol in input_dict["traffic_policy"]:
            if not isinstance(pol, dict):
                raise TypeError(
                    "A dictionary with these keys expected:"
                    + "floor, segment_id, direction"
                )
        traffic_policy = input_dict["traffic_policy"]

    total_percent = sum(s["percent_workforce"] for s in shifts)
    if total_percent > 1.0:
        raise ValueError("Total percent workforce greater than 1.0")

    LOG.info("Number of agents: %d", n_agents)
    LOG.info("User provided floorplan scale is: %s", floorplan_scale)

    converted_contact_distance = contact_distance / floorplan_scale
    return {
        "upload_results": upload_results,
        "upload_location": upload_location,
        "facility_name": facility_name,
        "floors": floors,
        "n_agents": n_agents,
        "occupancy_rate": occupancy_rate,
        "daylength": daylength,
        "buffer": buffer,
        "timestep": 1.0,
        "entrances": entrances,
        "contact_distance": converted_contact_distance,
        "shifts": shifts,
        "meetings_policy_params": meetings_policy,
        "scheduling_policy": scheduling_policy,
        "traffic_policy": traffic_policy,
        "output_directory": os.getcwd() + "/",
    }
