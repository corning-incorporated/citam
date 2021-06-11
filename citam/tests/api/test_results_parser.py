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

from citam.api.parser import (
    get_contacts,
    get_total_timesteps,
    get_trajectories,
)


def test_contacts_parsing_num_steps(use_local_storage):
    contacts = get_contacts("run_id_0001", "0")
    assert len(contacts) == 1900


def test_get_contacts_no_contact_step(use_local_storage):
    """
    Test that the correct data is parsed when a single contact was made in a
    step
    """
    contacts = get_contacts("run_id_0001", "0")
    assert len(contacts[0]) == 0


def test_get_contacts_single_contact_step(use_local_storage):
    """
    Test that the correct data is parsed when a single contact was made in a
    step
    """
    contacts = get_contacts("run_id_0001", "0")
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
    contacts = get_contacts("run_id_0001", "0")
    step = contacts[86]
    assert len(step) == 2
    expected = [
        {"x": 120, "y": 602, "count": 2},
        {"x": 168, "y": 600, "count": 1},
    ]
    for ix, contact in enumerate(step):
        assert contact == expected[ix]


def test_trajectories_num_structure(use_local_storage):
    trajectories = get_trajectories("run_id_0001")
    assert trajectories.get("data")
    assert trajectories.get("statistics")


def test_trajectories_num_steps(use_local_storage):
    trajectories = get_trajectories("run_id_0001")
    assert len(trajectories["data"]) == 1900


def test_get_total_timesteps(use_local_storage):
    nsteps = get_total_timesteps("51a37fa7054a3f8e8d55")
    assert nsteps["data"] == 12200


def test_get_trajectories_2agents(use_local_storage):
    trajectories = get_trajectories("run_id_0001")
    expected_trajectories = {5: (0, 602, 0, 0), 6: (0, 602, 0, 0)}

    for idx, expected in expected_trajectories.items():
        assert trajectories["data"][82][idx] == expected


def test_get_trajectories_2agents_filtered(use_local_storage):
    trajectories = get_trajectories("run_id_0001", floor=1)
    expected_trajectories = {5: (0, 602, 1, 0)}

    for idx, expected in expected_trajectories.items():
        assert trajectories["data"][79][idx] == expected


def test_get_trajectories_long_trajectory_next_block(use_local_storage):
    trajectories = get_trajectories(
        "51a37fa7054a3f8e8d55", first_timestep=5000
    )
    assert len(trajectories["data"]) == 5000
    assert len(trajectories["data"][0]) == 207


def test_get_trajectories_long_trajectory_no_block(use_local_storage):
    trajectories = get_trajectories(
        "51a37fa7054a3f8e8d55", first_timestep=30000
    )  # File has less than 30,000 steps
    assert len(trajectories["data"]) == 0


def test_get_trajectories_long_trajectory_last_block(use_local_storage):
    trajectories = get_trajectories(
        "51a37fa7054a3f8e8d55", first_timestep=10000
    )
    assert len(trajectories["data"]) == 2200
    assert len(trajectories["data"][0]) == 207


def test_get_trajectories_long_trajectory_all(use_local_storage):
    trajectories = get_trajectories(
        "51a37fa7054a3f8e8d55",
        first_timestep=0,
        max_steps=15000,
    )
    assert len(trajectories["data"]) == 12200
    assert trajectories["data"][0] == [(None, None, None, None)] * 207
    assert len(trajectories["data"][-1]) == 207
