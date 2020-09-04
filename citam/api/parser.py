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

__all__ = [
    'get_contacts',
    'get_trajectories',
    'get_coordinate_distribution'
]

import logging
from citam.api.settings_parser import get_storage_driver
import json

LOG = logging.getLogger(__name__)


def get_trajectories(sim_id, floor=None):
    """
    Get trajectory information for a simulation

    :param str sim_id: simulation identifier
    :param str|int|None floor: Floor number.  Use None to return all floors
    :return: List of trajectories broken down by step
    :rtype: list[list[dict[str,float]]
    """
    result_file = get_storage_driver().get_trajectory_file(sim_id)
    LOG.info(
        "trajectory file parsing process started",
    )
    if floor is not None:
        floor = int(floor)
        LOG.info("Filtering trajectories for floor %d", floor)

    steps = []
    count_line = result_file.readline().strip()
    while count_line is not None and count_line != '':
        num_contacts = int(count_line)
        step_num = result_file.readline().strip()
        step_num = step_num.replace('step :', '')  # noqa
        step = []
        for i in range(num_contacts):
            data = result_file.readline().strip().split('\t')

            if floor is not None and int(data[3]) != floor:
                continue

            step.append({
                'x': float(data[1]),
                'y': float(data[2]),
                'z': float(data[3]),
                'agent': int(data[0]),
                'count': int(data[4]),
            })
        steps.append(step)
        count_line = result_file.readline().strip()

    LOG.info("trajectory file parsing process is complete")
    try:
        max_contacts = max(max([y['count'] for x in steps for y in x]), 100)
    except ValueError:
        max_contacts = 100
    output = {
        "data": steps,
        "statistics": {"max_contacts": max_contacts}
    }
    return output


def get_contacts(sim_id, floor):
    """
    Retrieve contact information for a simulation

    :param str sim_id: simulation identifier
    :param str floor: Floor number
    :return: List of contacts
    :rtype: list[list[dict[str,float]]
    """
    result_file = get_storage_driver().get_contact_file(sim_id, floor)
    LOG.info("contacts file parsing process started")

    steps = []
    count_line = result_file.readline().strip()
    while count_line is not None and count_line != '':
        num_contacts = int(count_line)
        step_num = result_file.readline().strip()
        step_num = step_num.replace('step :', '')  # noqa
        step = []
        for i in range(num_contacts):
            data = result_file.readline().strip().split('\t')
            step.append({
                'x': float(data[0]),
                'y': float(data[1]),
                'count': int(data[2]),
            })
        steps.append(step)
        count_line = result_file.readline().strip()
    LOG.info("contacts file parsing process is complete. %d steps", len(steps))
    return steps


def get_coordinate_distribution(sim_id, floor):
    """
    Retrieve contact/coordinate distribution for a simulation

    :param str sim_id: simulation identifier
    :param str floor: Floor number
    :return: List of contacts per coordinate
    :rtype: list[dict[str,float]]
    """
    result_file = get_storage_driver().get_coordinate_distribution_file(
        sim_id,
        floor,
    )
    LOG.info("coordinate distribution file parsing process started")

    contacts = []
    result_file.readline()  # header
    line = result_file.readline().strip()
    while line:
        data = line.split(',')
        contacts.append({
            'x': data[0],
            'y': data[1],
            'count': data[2],
        })
        line = result_file.readline().strip()
    LOG.info("coordinate distribution file parsing process complete")
    return contacts


def get_pair_contacts(sim_id):
    """
    Retrieve contact information for a simulation

    :param str sim_id: simulation identifier
    :return: List of pair contacts
    :rtype: list[list[dict[str,str, int, str]]
    """

    result_file = get_storage_driver().get_pair_contact_file(sim_id)
    LOG.info("pair contacts file parsing process started")
    pairs = []

    result_file.readline().strip()
    for line in result_file:
        data = line.strip().split(",")
        if len(data) != 4:
            LOG.error("Corrupted file! 4 values are expected for each line "
                      "in pair_contact.csv. %d found.", len(data))
            return []
        pairs.append({
            'Agent1': data[0],
            'Agent2': data[1],
            'N_Contacts': int(data[2]),
            'TotalContactDuration': data[3]
        })
    return pairs


def get_statistics_json(sim_id):
    """
    Retrieve get_statistics json information for a simulation

    :param str sim_id: simulation identifier
    :return: List of statistics
    :rtype: list[list[dict[str,str, int, str]]
    """

    result_dict = json.loads(
        get_storage_driver().get_statistics_file(sim_id).read()
    )
    LOG.info("Statistics JSON file parsing process started")

    if 'data' not in result_dict or len(result_dict['data']) != 4:
        LOG.error("Corrupted file! Statistics JSON file does "
                  "not have required attributes.")
        return []
    return result_dict["data"]
