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


import csv
import os
import logging
import errno
import json
from typing import List, Tuple, Dict
import xml.etree.ElementTree as ET

from svgpathtools import svg2paths, Line, parse_path, Path

from citam.engine.constants import (
    REQUIRED_SPACE_METADATA,
    OPTIONAL_SPACE_METADATA,
    SUPPORTED_SPACE_FUNCTIONS,
)

LOG = logging.getLogger(__name__)


class MissingInputError(TypeError):
    pass


class InvalidSVGError(ValueError):
    pass


def parse_csv_metadata_file(csv_file: str) -> List[Dict[str, str]]:
    """Read and parse CSV floorplan metadata file.

    :param str csv_file: path to csv file
    :return: List of dictionaries (one dict per entry in the CSV file) with
        column headers as keys
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


def parse_standalone_svg_floorplan_file(
    svg_file: str,
) -> Tuple[List[Path], List[Dict[str, str]], List[Path]]:
    """
    Read standalone svg input file to extract floorplan information.

    :param str svg_file: Floorplan input file in SVG format to parse.
    :return: Tuple with list of space paths, list of space attributes and
        list of door paths
    """
    # Load XML and get root elem
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Find element with tag 'g' and id == contents
    contents_elem = None
    possible_content_elems = []
    for elem in root:
        _, _, elem.tag = elem.tag.rpartition("}")  # Remove namespace
        if elem.tag == "g" and "id" in elem.attrib:
            possible_content_elems.append(elem)

    for level in possible_content_elems:
        if level.attrib["id"].lower() == "contents":
            contents_elem = level
            break

    if contents_elem is None:
        error = "An element with tag 'g' & id==contents is required"
        raise InvalidSVGError(error)

    # Verify that there is data at least for one building
    buildings = []
    for building_elem in contents_elem:
        if (
            "id" not in building_elem.attrib
            or "class" not in building_elem.attrib
        ):
            continue
        if building_elem.attrib["class"].lower() != "floorplan":
            continue
        buildings.append(building_elem)

    if len(buildings) == 0:
        errmsg = "At least 1 building element with class=='floorplan' required"
        raise InvalidSVGError(errmsg)

    space_paths, space_attrib, door_paths = _load_buildings_data(buildings)

    if len(space_paths) == 0:
        raise InvalidSVGError("No space data found in SVG file")

    return space_paths, space_attrib, door_paths


def _load_buildings_data(
    contents_elem: ET.Element,
) -> Tuple[List[Path], List[Dict[str, str]], List[Path]]:
    """
    Given a SVG tree element with sub-elements with building information,
    extract data for each building and add to overall list of space paths,
    space attributes and doors for this floorplan.

    :param ET.ElementTree contents_elem: Element from the SVG file with
        data for each building as subelements.
    :return: tuple with list of space paths, list of space attributes and list
        of door paths.
    """
    space_paths = []
    space_attributes = []
    door_paths = []

    # For each building, extract space paths, space attr and door paths
    for building_elem in contents_elem:

        building_name = building_elem.attrib["id"]
        doors_elem, spaces_elem = None, None

        for sub_elem in building_elem:
            if "class" not in sub_elem.attrib:
                continue
            if sub_elem.attrib["class"].lower() == "spaces":
                spaces_elem = sub_elem
            elif sub_elem.attrib["class"].lower() == "doors":
                doors_elem = sub_elem

        if spaces_elem is None:
            raise InvalidSVGError("Sub-element of class 'spaces' required")

        sp_paths, sp_attr = _extract_spaces(spaces_elem, building_name)
        space_paths += sp_paths
        space_attributes += sp_attr

        if doors_elem is not None:
            door_paths += _extract_doors(doors_elem)

    return space_paths, space_attributes, door_paths


def _extract_spaces(
    spaces_elem: ET.Element, building_name: str
) -> Tuple[List[Path], List[Dict[str, str]]]:
    """
    Given a SVG tree element, extract all space paths and attributes

    :param xml.etree.ElementTree.Element spaces_elem: SVG element with each
        subelement representing a path.
    :return: list of space paths and attributes.
    """
    space_paths, space_attributes = [], []

    for space_elem in spaces_elem:
        # Remove namespace
        _, _, space_elem.tag = space_elem.tag.rpartition("}")
        # Extract space data
        if space_elem.tag == "path" and "d" in space_elem.attrib:
            space_path = parse_path(space_elem.attrib["d"])

            # Add space metadata
            space_metadata = {}
            if "id" in space_elem.attrib and "class" in space_elem.attrib:

                space_metadata["id"] = space_elem.attrib["id"]
                if "unique_name" not in space_elem.attrib:
                    space_metadata["unique_name"] = space_elem.attrib["id"]

                space_function = space_elem.attrib["class"]
                if space_function.lower() not in SUPPORTED_SPACE_FUNCTIONS:
                    raise ValueError(
                        "Unsupported space function %s", space_function
                    )
                space_metadata["space_function"] = space_function

                space_metadata["building"] = building_name

                if "capacity" in space_elem.attrib:
                    space_metadata["capacity"] = space_elem.attrib["capacity"]
            else:
                raise ValueError(
                    "'id' and 'class' attributes required for space paths"
                )
            space_paths.append(space_path)
            space_attributes.append(space_metadata)

    return space_paths, space_attributes


def _extract_doors(doors_elem: ET.Element) -> List[Path]:
    """
    Given a SVG tree element, extract all door paths.

    :param xml.etree.ElementTree.Element doors_elem: SVG element with each
        subelement representing a door.
    :return: list of door paths.
    """
    door_paths = []
    for door_elem in doors_elem:
        # Remove namespace
        _, _, door_elem.tag = door_elem.tag.rpartition("}")
        if door_elem.tag == "path" and "d" in door_elem.attrib:
            door_path = parse_path(door_elem.attrib["d"])
            door_paths.append(door_path)

    return door_paths


def parse_svg_floorplan_file(svg_file):

    """Read and parse SVG floorplan file.

    Each space is represented by a path element with and id that matches the
    id in the csv file.

    :param str svg_file: path to csv file
    :return:
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

        if "id" not in attr or "door" in attr["id"]:
            door_paths.append(path)
        else:
            space_paths.append(path)
            space_attributes.append(attr)

    LOG.info("Number of door paths: %d", len(door_paths))
    LOG.info("Number of space paths: %d", len(space_paths))

    return space_paths, space_attributes, door_paths


def parse_meetings_policy_file(
    json_filepath: str,
) -> Dict[str, int or str or float or dict]:
    """Read and parse the json meeting policy file.

    The meetings policy for a given facility exposes parameters
    for when, where, how often and how long meetings take place
    in the facility.

    :param str json_filepath: path to the scheduling policy file
    :return: data extracted from the file as a dictionary
    """
    meetings_policy_params = None
    if os.path.isfile(json_filepath):
        with open(json_filepath, "r") as f:
            meetings_policy_params = json.load(f)
    else:
        LOG.error("Could not find input file: %s", json_filepath)
        raise FileNotFoundError(json_filepath)

    return meetings_policy_params


def parse_scheduling_policy_file(
    json_filepath: str,
) -> Dict[str, int or str or float or dict]:
    """Read and parse the json scheduling policy file.

    Together with the meetings policy file, this file encodes
    how and when people will be moving within a given facility.
    Scheduling policies revolve around the concept of "scheduling
    purpose" which ties them to a category of space in the floorplan.
    See the documentation for more information.

    TODO: Each employee group can have their own scheduling policy (e.g.
    managers vs technicians).

    :param str json_filepath: path to the scheduling policy file
    :return: data extracted from the file as a dictionary
    """
    if os.path.isfile(json_filepath):
        with open(json_filepath, "r") as f:
            scheduling_policy = json.load(f)
        return scheduling_policy
    else:
        LOG.error("Could not find input file: %s", json_filepath)
        raise FileNotFoundError(json_filepath)


def parse_input_file(
    input_file: str,
) -> Dict[str, str or int or dict or float]:
    """Read primary simulation input file in json format, validate values,
    load floorplans and returns dictionary of model inputs.

    :param str input_file: path to input file expected in json format
    :return: dictionary of inputs
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

    if daylength < buffer + 1800:
        raise ValueError(
            "Daylength is too short (min is 30 min after entrance time)"
        )

    if buffer < 0:
        raise ValueError("Buffer must be a positive value.")

    if n_agents <= 1:
        raise ValueError("At least one agent is required.")

    # Optional arguments
    create_meetings = input_dict.get("create_meetings", True)
    close_dining = input_dict.get("close_dining", False)
    upload_results = input_dict.get("upload_results", False)
    upload_location = input_dict.get("upload_location", None)

    if upload_results and upload_location is None:
        raise ValueError("upload_location must be specified.")

    occupancy_rate = input_dict.get("occupancy_rate", None)

    floorplan_scale = input_dict.get(["floorplan_scale"], 1.0 / 12.0)
    if not isinstance(floorplan_scale, (int, float)):
        raise TypeError("Floorplan scale must be a float or an int")

    contact_distance = input_dict.get("contact_distance", 6.0)

    shifts = input_dict.get(
        "shifts",
        [{"name": "primary", "start_time": buffer, "percent_workforce": 1.0}],
    )
    if not isinstance(shifts, list):
        raise TypeError("shifts must be a list")
    for s in shifts:
        if (
            "name" not in s
            or "start_time" not in s
            or "percent_workforce" not in s
        ):
            raise ValueError(
                "A shift must define a name, start time and percent workforce"
            )
        if (
            not isinstance(s["percent_workforce"], (int, float))
            or s["percent_workforce"] > 1.0
            or s["percent_workforce"] <= 0.0
        ):
            raise TypeError("Percent workforce must be between 0.0 than 1.0")

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
            if (
                "floor" not in pol
                or "segment_id" not in pol
                or "direction" not in pol
            ):
                raise TypeError(
                    "The following keys are expected in each policy:"
                    + "floor, segment_id, direction"
                )
        traffic_policy = input_dict["traffic_policy"]

    total_percent: float = sum(s["percent_workforce"] for s in shifts)
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
        "create_meetings": create_meetings,
        "close_dining": close_dining,
    }
