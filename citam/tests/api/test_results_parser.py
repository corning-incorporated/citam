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

from citam.api.parser import get_contacts, get_trajectories


def test_contacts_parsing_num_steps(use_local_storage):
    contacts = get_contacts("sim_id_0001", "0")
    assert len(contacts) == 1900


def test_get_contacts_no_contact_step(use_local_storage):
    """
    Test that the correct data is parsed when a single contact was made in a
    step
    """
    contacts = get_contacts("sim_id_0001", "0")
    assert len(contacts[0]) == 0


def test_get_contacts_single_contact_step(use_local_storage):
    """
    Test that the correct data is parsed when a single contact was made in a
    step
    """
    contacts = get_contacts("sim_id_0001", "0")
    step = contacts[87]
    assert len(step) == 1
    assert step[0]["x"] == 120.0
    assert step[0]["y"] == 600.0
    assert step[0]["count"] == 1


def test_get_contacts_multiple_contact_step(use_local_storage):
    """
    Test that the correct data is parsed when a multiple contacts were made
    in a step
    """
    contacts = get_contacts("sim_id_0001", "0")
    step = contacts[86]
    assert len(step) == 2
    expected = [
        {"x": 120, "y": 602, "count": 2},
        {"x": 168.0, "y": 600.0, "count": 1},
    ]
    for ix, contact in enumerate(step):
        assert contact == expected[ix]


def test_trajectories_num_structure(use_local_storage):
    trajectories = get_trajectories("sim_id_0001")
    assert trajectories.get("data")
    assert trajectories.get("statistics")


def test_trajectories_num_steps(use_local_storage):
    trajectories = get_trajectories("sim_id_0001")
    assert len(trajectories["data"]) == 1900


def test_get_trajectories_2agents(use_local_storage):
    trajectories = get_trajectories("sim_id_0001")
    expected_trajectories = [
        {"agent": 5, "x": 0, "y": 602, "z": 0, "count": 0},
        {"agent": 6, "x": 0, "y": 602, "z": 0, "count": 0},
    ]
    for ix, expected in enumerate(expected_trajectories):
        assert trajectories["data"][82][ix] == expected


def test_get_trajectories_2agents_filtered(use_local_storage):
    trajectories = get_trajectories("sim_id_0001", floor=1)
    expected_trajectories = [
        {"agent": 5, "x": 0, "y": 602, "z": 1, "count": 0},
    ]
    for ix, expected in enumerate(expected_trajectories):
        assert trajectories["data"][79][ix] == expected
