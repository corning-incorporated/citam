#  Copyright 2021. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
#  ==========================================================================


import csv
import os
import logging
import errno
import json
from typing import List, Optional, Tuple, Dict, Union, Any
import xml.etree.ElementTree as ET
import pathlib

from svgpathtools import svg2paths, Line, parse_path, Path

from citam.engine.constants import (
    REQUIRED_SPACE_METADATA,
    OPTIONAL_SPACE_METADATA,
    SUPPORTED_SPACE_FUNCTIONS,
)

LOG = logging.getLogger(__name__)
UNABLE_TO_READ_FILE_STR = "Could not read input file"


class MissingInputError(ValueError):
    pass


class InvalidSVGError(ValueError):
    pass


def _process_row(header: List[str], row_id: int, row: List[str]):
    """
    Process row data from floorplan CSV file.

    :param header: List of header values.
    :type header: List[str]
    :param row_id: index of this row
    :type row_id: int
    :param row: row data as list of values
    :type row: List[str]
    :raises ValueError: if row has the wrong number of values.
    :raises ValueError: if required value(s) missing.
    :raises ValueError: if unrecoginzed space function is found.
    :return: row data as a dictionary with key taken from header
    :rtype: [type]
    """
    SUPPORTED_METADATA = REQUIRED_SPACE_METADATA + OPTIONAL_SPACE_METADATA

    row_data = {}
    if len(row) != len(header):
        raise ValueError(f"Wrong number of columsn in row {row_id+1}")
    for c, name in enumerate(header):
        value = row[c]
        if str(value) == "" and name in REQUIRED_SPACE_METADATA:
            msg = f"No '{name}' found in this row {row_id+1}"
            raise ValueError(msg)

        if header[c] in SUPPORTED_METADATA:
            row_data[header[c]] = value.lower()
            if (
                header[c] == "space_function"
                and value.lower() not in SUPPORTED_SPACE_FUNCTIONS
            ):

                msg = f"Invalid space function: '{value}' in row \
                        {row_id+1}. Valid entries are: \
                        {SUPPORTED_SPACE_FUNCTIONS}"
                raise ValueError(msg)
    return row_data


def parse_csv_metadata_file(
    csv_file: Union[str, pathlib.Path]
) -> List[Dict[str, str]]:
    """
    Read and parse CSV floorplan metadata file with list of spaces and their
    attributes (id, function, etc.).

    :param csv_file: path to csv file.
    :type csv_file: Union[str, pathlib.Path]
    :raises FileNotFoundError: If CSV file is not found.
    :raises ValueError: If a required column is missing from file.
    :return: List of dictionaries (one dict per entry in the CSV file) with
            column headers as keys
    :rtype: List[Dict[str, str]]
    """

    if not os.path.isfile(csv_file):
        LOG.fatal("File not found. %s", csv_file)
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), csv_file
        )

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
                row_data = _process_row(header, i, row)
                space_info.append(row_data)

    return space_info


def extract_buildings_elem(
    contents_elem: List[ET.Element],
) -> List[ET.Element]:
    """
    Extract building elements from SVG contents

    :param contents_elem: The list of SVG elements with building info
    :type contents_elem: List[ET.Element]
    :raises InvalidSVGError: if no building elem found
    :return: List of building elements
    :rtype: List[ET.Element]
    """
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

    return buildings


def parse_standalone_svg_floorplan_file(
    svg_file: Union[str, pathlib.Path],
) -> Tuple[List[Path], List[Dict[str, str]], List[Path]]:
    """
    Read standalone svg input file to extract floorplan information. The SVG
    file should include and ID and a function for each space.

    :param svg_file: input file in SVG format to parse.
    :type svg_file: Union[str, pathlib.Path]
    :raises InvalidSVGError: If no element with id=contents is found
    :raises InvalidSVGError: If no element with class=floorplan is found.
    :raises InvalidSVGError: If no buildings were found (elements with
            id=spaces and id=doors)
    :return: Tuple with list of space paths, list of space attributes and
            list of door paths
    :rtype: Tuple[List[Path], List[Dict[str, str]], List[Path]]
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

    # Verify that there is data at least for one building and extract spaces
    buildings_elem = extract_buildings_elem(contents_elem)
    space_paths, space_attrib, door_paths = _load_buildings_data(
        buildings_elem
    )

    if len(space_paths) == 0:
        raise InvalidSVGError("No space data found in SVG file")

    return space_paths, space_attrib, door_paths


def _load_buildings_data(
    contents_elem: List[ET.Element],
) -> Tuple[List[Path], List[Dict[str, str]], List[Path]]:
    """
    Given a SVG tree element with sub-elements with building information,
    extract data for each building and add to overall list of space paths,
    space attributes and doors for this floorplan.

    :param contents_elem: Element from the SVG file with data for each building
            as subelements.
    :type contents_elem: List[ET.Element]
    :raises InvalidSVGError: If no sub-element with class spaces were found.
    :return: tuple with list of space paths, list of space attributes and list
        of door paths.
    :rtype: Tuple[List[Path], List[Dict[str, str]], List[Path]]
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


def _extract_space_metadata(
    space_elem: ET.Element, building_name: str
) -> Dict[str, str]:
    """
    Extract data from space SVG element and return dictionary of values.

    :param space_elem: The space SVG element.
    :type space_elem: ET.Element
    :param building_name: Name of the building where this space is found.
    :type building_name: str
    :raises ValueError: if space ID or function is missing.
    :raises ValueError: if space function is invalid.
    :return: Dictionary with key-value pairs of space metadata.
    :rtype: Dict[str, str]
    """
    if "id" not in space_elem.attrib or "function" not in space_elem.attrib:
        raise ValueError(
            "'id' and 'function' required for space paths %s",
            space_elem.attrib,
        )
    space_metadata = {}
    space_metadata["id"] = space_elem.attrib["id"]
    if "unique_name" not in space_elem.attrib:
        space_metadata["unique_name"] = space_elem.attrib["id"]

    space_function = space_elem.attrib["function"]
    if space_function.lower() not in SUPPORTED_SPACE_FUNCTIONS:
        raise ValueError("Unsupported space function %s", space_function)
    space_metadata["space_function"] = space_function

    space_metadata["building"] = building_name

    if "capacity" in space_elem.attrib:
        space_metadata["capacity"] = space_elem.attrib["capacity"]

    return space_metadata


def _extract_spaces(
    spaces_elem: ET.Element, building_name: str
) -> Tuple[List[Path], List[Dict[str, str]]]:
    """
    Given a SVG tree element, extract all space paths and attributes.

    :param spaces_elem: SVG element with each subelement representing a space.
    :type spaces_elem: ET.Element
    :param building_name: The name of the building
    :type building_name: str
    :raises ValueError: If the function assigned to the space is unknown.
    :raises ValueError: If the space path has no ID or function specified.
    :return: list of space paths and attributes.
    :rtype: Tuple[List[Path], List[Dict[str, str]]]
    """

    space_paths, space_attributes = [], []

    for space_elem in spaces_elem:
        # Remove namespace
        _, _, space_elem.tag = space_elem.tag.rpartition("}")
        # Extract space data
        if space_elem.tag == "path" and "d" in space_elem.attrib:
            space_path = parse_path(space_elem.attrib["d"])
            space_paths.append(space_path)

            # Add space metadata
            space_metadata = _extract_space_metadata(space_elem, building_name)
            space_attributes.append(space_metadata)

    return space_paths, space_attributes


def _extract_doors(doors_elem: ET.Element) -> List[Path]:
    """
    Given a SVG tree element, extract all door paths.

    :param doors_elem: SVG element with each subelement representing a door.
    :type doors_elem: ET.Element
    :return: list of door paths.
    :rtype: List[Path]
    """
    door_paths = []
    for door_elem in doors_elem:
        # Remove namespace
        _, _, door_elem.tag = door_elem.tag.rpartition("}")
        if door_elem.tag == "path" and "d" in door_elem.attrib:
            door_path = parse_path(door_elem.attrib["d"])
            door_paths.append(door_path)

    return door_paths


def parse_svg_floorplan_file(
    svg_file: Union[str, pathlib.Path]
) -> Tuple[List[Path], List[Dict[str, str]], List[Path]]:
    """
    Read and parse SVG floorplan file.

     Each space is represented by a path element with and id that matches the
    id in the csv file.

    :param svg_file: path to csv file
    :type svg_file: Union[str, pathlib.Path]
    :raises FileNotFoundError: If SVG file is not found.
    :return: List of path elements and their attributes as well as door paths.
    :rtype: Tuple[List[Path], List[Dict[str, str]], List[Path]]
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
    input_dict: dict,
) -> Optional[Dict[str, Union[int, str, float, dict]]]:
    """
    Read and parse the json meeting policy file if found in input dict.

    The meetings policy for a given facility exposes parameters
    for when, where, how often and how long meetings take place
    in the facility.

    :param input_dict: dictionary of inputs with path to meetings policy file.
    :type input_dict: dict
    :raises FileNotFoundError: IIf the file is not found.
    :return: data extracted from the file as a dictionary
    :rtype: Optional[Dict[str, Union[int, str, float, dict]]
    """
    if "meetings_file" not in input_dict:
        return None

    json_filepath = input_dict["meetings_file"]
    try:
        with open(json_filepath, "r") as f:
            meetings_policy_params = json.load(f)
        return meetings_policy_params

    except Exception as exception:
        LOG.error(f"{UNABLE_TO_READ_FILE_STR}: {json_filepath}")
        raise exception


def parse_scheduling_policy_file(
    input_dict: dict,
) -> Optional[Dict[str, Union[int, str, float, dict]]]:
    """
    Read and parse the json scheduling policy file if found in input dict.

    Together with the meetings policy file, this file encodes
    how and when people will be moving within a given facility.
    Scheduling policies revolve around the concept of "scheduling
    purpose" which ties them to a category of space in the floorplan.
    See the documentation for more information.

    :param input_dict: dictionary with path to scheduling policy file.
    :type input_dict: dict
    :raises FileNotFoundError: [description]
    :return: data extracted from the file as a dictionary.
    :rtype: Optional[Dict[str, Union[int, str, float, dict]]]
    """
    if "scheduling_policy_file" not in input_dict:
        return None

    json_filepath = input_dict["scheduling_policy_file"]

    try:
        with open(json_filepath, "r") as f:
            scheduling_policy = json.load(f)
        return scheduling_policy

    except Exception as exception:
        LOG.error(f"{UNABLE_TO_READ_FILE_STR}: {json_filepath}")
        raise exception


def parse_office_assignment_file(
    input_dict: dict,
) -> Optional[List[Tuple[int, int]]]:
    """
    Read and parse office assignment file if found in input dic.

    :param input_dict: dictionary with path to office assignment file.
    :type input_dict: dict
    :raises exception: if unable to read file
    :raises ValueError: if invalid values are found in assignment file.
    :return: office space ID and floor number assigned to each agent.
    :rtype: Optional[List[Tuple[int, int]]]
    """
    if "office_assignment_file" not in input_dict:
        return None
    office_assignment = []
    filepath = input_dict["office_assignment_file"]
    try:
        with open(filepath, "r") as infile:
            infile.readline()
            for line in infile:
                values = line.strip().split(",")
                if len(values) == 3:
                    office_assignment.append((int(values[1]), int(values[2])))
                elif len(values) != 0:
                    raise ValueError(
                        "Invalid file: three comma-seperated values expected \
                            (index, base_location, floor_id)"
                    )
    except Exception as exception:
        LOG.error(f"{UNABLE_TO_READ_FILE_STR}: {filepath}")
        raise exception

    if len(office_assignment) == 0:
        raise ValueError(
            "Could not load any office assignment from file %s", filepath
        )

    return office_assignment


def check_for_required_values(input_dict: dict) -> None:
    """
    Verify that all required values are found in the input dict.

    :param input_dict: dictionary of inputs
    :type input_dict: dict
    :raises MissingInputError: if a required value is missing
    """

    required_values = [
        "facility_name",
        "floors",
        "entrances",
        "daylength",
        "entrance_time",
        "n_agents",
        "simulation_name",
        "run_name",
    ]
    for key in required_values:
        if key not in input_dict:
            raise MissingInputError("{%s} is a required input", key)


def validate_input_values(
    facility_name: str,
    floors: List[int],
    n_agents: int,
    daylength: int,
    entrances: List[dict],
    buffer: int,
) -> None:
    """
    Verify that input values are of the correct type and have valid values.

    :param facility_name: Name of the facility of interest.
    :type facility_name: str
    :param floors: List of floors for this simulation
    :type floors: List[int]
    :param n_agents: Number of agents in this simulation
    :type n_agents: int
    :param daylength: duration of the simulaiton
    :type daylength: int
    :param entrances: Entrances available for agents to enter the facility
    :type entrances: List[dict]
    :param buffer: when do agents start entering the facility.
    :type buffer: int
    :raises TypeError: if any input value is of the wrong type
    :raises ValueError: if invalid input values are found.
    """
    if not isinstance(facility_name, str):
        raise TypeError("facility_name must be a string")

    if not isinstance(floors, list):
        raise TypeError("floors must be a list")

    if len(floors) == 0:
        raise ValueError("At least one floor is required.")

    if len(set(floors)) != len(floors):
        raise ValueError("Duplicates found in list of floors")

    if not isinstance(n_agents, int):
        raise TypeError("n_agents must be an integer")

    if not isinstance(daylength, int):
        raise TypeError("daylength must be an integer.")

    if not isinstance(entrances, list):
        raise TypeError("entrances must be a list")

    if not isinstance(buffer, int):
        raise TypeError("entrance time must be an integer")

    if daylength < 1800:
        raise ValueError(
            "Daylength is too short (min is 30 min after entrance time)"
        )

    if buffer < 0:
        raise ValueError("Buffer must be a positive value.")

    if n_agents <= 1:
        raise ValueError("At least one agent is required.")


def validate_shifts(shifts: List[dict]) -> None:
    """
    Validate input values for shifts. A shift is a group of agents who enter
    the facility at the same time.

    :param shifts: List of shifts
    :type shifts: List[dict]
    :raises TypeError: if shifts is not a list.
    :raises ValueError: if shift does not define a name, start time and percent
        agents.
    :raises TypeError: if percent agents is not a number
    :raises ValueError: if percent agents is not a number between 0.0 and 1.0.
    """
    if not isinstance(shifts, list):
        raise TypeError("shifts must be a list")

    for s in shifts:
        if (
            "name" not in s
            or "start_time" not in s
            or "percent_agents" not in s
        ):
            raise ValueError(
                "A shift must define a name, start time and percent agents"
            )
        if not isinstance(s["percent_agents"], (int, float)):
            raise TypeError("Percent agents must be a number")

        if s["percent_agents"] > 1.0 or s["percent_agents"] <= 0.0:
            raise ValueError("Percent agents must be between 0.0 than 1.0")


def validate_traffic_policy(traffic_policy):
    if traffic_policy is None:
        return

    if not isinstance(traffic_policy, list):
        raise TypeError(
            "traffic_policy must be a list. Found {%s}", type(traffic_policy),
        )

    for pol in traffic_policy:
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


def parse_input_file(input_file: Union[str, pathlib.Path],) -> Dict[str, Any]:
    """
    Read primary simulation input file in json format, validate values,
    load floorplans and returns dictionary of model inputs.

    :param input_file: path to input file expected in json format
    :type input_file: Union[str, pathlib.Path]
    :raises ValueError: If unable to decode JSON file.
    :raises FileNotFoundError: If the file is not found.
    :raises MissingInputError: If a required value is not found
    :raises TypeError: If incorrect value type is found for one or more inputs.
    :raises ValueError: If an input value is invalid.
    :raises FileNotFoundError: If path to another to a meetings policy is file
            is not valid.
    :raises FileNotFoundError: If path to another to a scheduling policy is
            file is not valid.
    :return: dictionary of inputs
    :rtype: Dict[str, Any]
    """

    try:
        with open(input_file, "r") as f:
            input_dict = json.load(f)
    except Exception as exception:
        LOG.error(f"{UNABLE_TO_READ_FILE_STR}: {input_file}")
        raise exception

    # Make sure all required values are provided
    check_for_required_values(input_dict)

    # extract required values
    facility_name = input_dict["facility_name"]
    floors = input_dict["floors"]
    n_agents = input_dict["n_agents"]
    daylength = input_dict["daylength"]
    entrances = input_dict["entrances"]
    buffer = input_dict["entrance_time"]
    simulation_name = input_dict["simulation_name"]
    run_name = input_dict["run_name"]

    # Make sure all required values are of the correct type
    validate_input_values(
        facility_name, floors, n_agents, daylength, entrances, buffer
    )

    # Optional arguments
    create_meetings = input_dict.get("create_meetings", True)
    close_dining = input_dict.get("close_dining", False)
    upload_results = input_dict.get("upload_results", False)
    upload_location = input_dict.get("upload_location", None)
    occupancy_rate = input_dict.get("occupancy_rate", None)
    contact_distance = input_dict.get("contact_distance", 6.0)

    # Handle pre-assigned offices, if any
    preassigned_offices = parse_office_assignment_file(input_dict)

    if upload_results and upload_location is None:
        raise ValueError("upload_location must be specified.")

    # Floorplan scale, defautls to 1 drawing unit = 12 inches
    floorplan_scale = input_dict.get("floorplan_scale", 1.0 / 12.0)
    if not isinstance(floorplan_scale, (int, float)):
        raise TypeError("Floorplan scale must be a float or an int")

    # Shifts
    default_shifts = [
        {"name": "primary", "start_time": buffer, "percent_agents": 1.0}
    ]
    shifts = input_dict.get("shifts", default_shifts)
    validate_shifts(shifts)

    # Meetings and scheduling policies
    scheduling_policy = parse_scheduling_policy_file(input_dict)
    meetings_policy = parse_meetings_policy_file(input_dict)

    # Traffic policy
    traffic_policy = input_dict.get("traffic_policy", None)
    validate_traffic_policy(traffic_policy)

    total_percent = sum(s["percent_agents"] for s in shifts)  # type: ignore
    if total_percent > 1.0:  # type: ignore
        raise ValueError("Total percent of agents cannot be greater than 1.0")

    LOG.info("Number of agents: %d", n_agents)
    LOG.info("User provided floorplan scale is: %s", floorplan_scale)

    converted_contact_distance = contact_distance / floorplan_scale
    return {
        "simulation_name": simulation_name,
        "run_name": run_name,
        "upload_results": upload_results,
        "upload_location": upload_location,
        "facility_name": facility_name,
        "floors": floors,
        "n_agents": n_agents,
        "occupancy_rate": occupancy_rate,
        "total_timesteps": daylength,
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
        "preassigned_offices": preassigned_offices,
    }
