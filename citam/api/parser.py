#  Copyright 2020. Corning Incorporated. All rights reserved.
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

__all__ = [
    "get_contacts",
    "get_trajectories",
    "get_coordinate_distribution",
    "get_trajectories_lines",
]

import logging
from typing import Dict, List, Union

from citam.conf import settings
import json

import time

LOG = logging.getLogger(__name__)


def get_trajectories_lines(sim_id: str, floor: Union[str, int] = None) -> Dict:
    result_file = settings.storage_driver.get_trajectory_file(sim_id)
    count = 0
    for _ in result_file:
        count += 1
    return {"data": count}


def get_total_timesteps(sim_id: str) -> Dict:
    manifest_data = settings.storage_driver.get_manifest(sim_id)
    nsteps = manifest_data["TotalTimesteps"]
    return {"data": nsteps}


def get_number_of_agents(sim_id: str) -> int:
    manifest_data = settings.storage_driver.get_manifest(sim_id)
    return manifest_data["NumberOfAgents"]


def get_trajectories(
    sim_id: str,
    floor: Union[str, int] = None,
    first_timestep: int = 0,
    max_steps: int = 5000,
) -> Dict:
    """
    Get trajectory information for a simulation

    :param sim_id: simulation identifier
    :param floor: Floor number.  Use None to return all floors
    :param offset: Offset number.  Start with 0
    :return: List of trajectories broken down by step
    """

    result_file = settings.storage_driver.get_trajectory_file_location(sim_id)

    LOG.info(
        "trajectory file parsing process started",
    )
    if floor is not None:
        floor = int(floor)
        LOG.info("Filtering trajectories for floor %d", floor)

    start_time = time.time()
    n_agents = get_number_of_agents(sim_id=sim_id)
    max_count = 0

    if n_agents <= 0:
        return {
            "data": [],
            "first_timestep": first_timestep,
            "max_count": max_count,
            "statistics": {"cfl": 0},
        }
    steps = []
    curr_file_line = 0
    current_pos_line, n_position_lines = 0, 0
    step_num = None
    new_step = True
    step = []
    position_lines = False
    with open(result_file, "r") as infile:
        for line in infile:
            curr_file_line += 1
            if new_step:
                n_position_lines = int(line.strip())
                current_pos_line = 0
                timestep_line = True
                new_step = False
                if step_num is not None and step_num >= first_timestep:
                    steps.append(step)
                    if len(steps) == max_steps:
                        break
                continue
            if timestep_line:
                step_num = int(line.strip().replace("step: ", ""))
                timestep_line = False
                if n_position_lines > 0:
                    position_lines = True
                else:
                    new_step = True
                step = [(None, None, None, None) for _ in range(n_agents)]
                continue
            if position_lines:
                data = line.strip().split()
                if len(data) < 5:
                    continue
                current_pos_line += 1
                if floor is not None and int(data[3]) != floor:
                    continue

                if int(data[0]) > len(step):
                    raise ValueError(
                        "More agents found in trajectory file. "
                        + "Please update NumberOfAgents in manifest file."
                    )

                step[int(data[0])] = (
                    round(float(data[1])),
                    round(float(data[2])),
                    round(float(data[3])),
                    int(data[4]),
                )

                max_count = max(max_count, int(data[4]))
                if current_pos_line == n_position_lines:
                    new_step = True
                    position_lines = False
        if (
            len(steps) < max_steps and step_num >= first_timestep
        ):  # We finished reading the file before max steps reached
            steps.append(step)  # Add last step data

    duration = time.time() - start_time
    LOG.info(f"trajectory file parsing process is complete in {duration} sec")

    return {
        "data": steps,
        "first_timestep": first_timestep,
        "max_count": max_count,
        "statistics": {"cfl": curr_file_line},
    }


def get_contacts(sim_id: str, floor: str) -> List[List[Dict]]:
    """Retrieve contact information for a simulation

    :param sim_id: simulation identifier
    :param floor: Floor number
    :return: List of contacts
    """
    result_file = settings.storage_driver.get_contact_file(sim_id, floor)
    LOG.info("contacts file parsing process started")

    steps = []
    count_line = result_file.readline().strip()
    while count_line is not None and count_line != "":
        num_contacts = int(count_line)
        step_num = result_file.readline().strip()
        step_num = step_num.replace("step :", "")  # noqa
        step = []
        for _ in range(num_contacts):
            data = result_file.readline().strip().split("\t")
            step.append(
                {
                    "x": float(data[0]),
                    "y": float(data[1]),
                    "count": int(data[2]),
                }
            )
        steps.append(step)
        count_line = result_file.readline().strip()
    LOG.info("contacts file parsing process is complete. %d steps", len(steps))
    return steps


def get_coordinate_distribution(sim_id: str, floor: str) -> List[Dict]:
    """Retrieve contact/coordinate distribution for a simulation

    :param sim_id: simulation identifier
    :param floor: Floor number
    :return: List of contacts per coordinate
    """
    result_file = settings.storage_driver.get_coordinate_distribution_file(
        sim_id,
        floor,
    )
    LOG.info("coordinate distribution file parsing process started")

    contacts = []
    result_file.readline()  # header
    line = result_file.readline().strip()
    while line:
        data = line.split(",")
        contacts.append(
            {
                "x": data[0],
                "y": data[1],
                "count": data[2],
            }
        )
        line = result_file.readline().strip()
    LOG.info("coordinate distribution file parsing process complete")
    return contacts


def get_pair_contacts(sim_id: str) -> List[Dict]:
    """Retrieve pair contact information for a simulation

    :param sim_id: simulation identifier
    :return: List of pair contacts
    """

    result_file = settings.storage_driver.get_pair_contact_file(sim_id)
    LOG.info("pair contacts file parsing process started")
    pairs = []

    result_file.readline().strip()
    for line in result_file:
        data = line.strip().split(",")
        if len(data) != 4:  # pragma: nocover
            LOG.error(
                "Corrupted file! 4 values are expected for each line "
                "in pair_contact.csv. %d found.",
                len(data),
            )
            return []
        pairs.append(
            {
                "Agent1": data[0],
                "Agent2": data[1],
                "N_Contacts": int(data[2]),
                "TotalContactDuration": data[3],
            }
        )
    return pairs


def get_statistics_json(sim_id: str) -> List[Dict]:
    """Retrieve get_statistics json information for a simulation

    :param str sim_id: simulation identifier
    :return: List of statistics
    """

    result_dict = json.loads(
        settings.storage_driver.get_statistics_file(sim_id).read()
    )
    LOG.info("Statistics JSON file parsing process started")

    if "data" not in result_dict or len(result_dict["data"]) != 4:
        LOG.error(
            "Corrupted file! Statistics JSON file does "
            "not have required attributes."
        )
        return []
    return result_dict["data"]


def get_policy_json(sim_id: str) -> List[Dict]:

    result_dict = json.loads(
        settings.storage_driver.get_policy_file(sim_id).read()
    )
    LOG.info("Statistics JSON file parsing process started")

    return result_dict
