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

import os
import pytest
from tempfile import TemporaryDirectory

from citam.api.storage.local import LocalStorageDriver
from citam.api.storage import NoResultsFoundError

search_root = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sample_results",
)


def test_bad_search_path():
    """
    This test uses a similar mechanism as citam.tests.cli.dash to check when
    a directory with a valid name but does not exist is passed into the
    storage driver, the correct exception is thrown.
    """
    # Create, get name of, then delete a temporary directory
    td = TemporaryDirectory()
    bad_dir = os.path.abspath(td.name)
    td.cleanup()
    with pytest.raises(IOError):
        LocalStorageDriver(search_path=bad_dir)


def test_results_found(monkeypatch):
    """
    This test uses a mocked boto3 session, which stores all arguments passed
    to the :class:`boto3.session.Storage()` constructor, then asserts the
    correct arguments were used
    """
    driver = LocalStorageDriver(search_path=search_root)
    assert len(driver.result_dirs) == 2


def test_no_results_found():
    with TemporaryDirectory() as td:
        with pytest.raises(NoResultsFoundError):
            LocalStorageDriver(search_path=td)


def test_list_runs():
    expected = [
        {
            "sim_id": "sim_id_0001",
            "facility_name": "TEST",
            "policy_id": "pol_id_0001",
        },
        {
            "sim_id": "sim_id_0002",
            "facility_name": "TEST",
            "policy_id": "pol_id_0001",
        },
        # the result in TFBAD has a malformed manifest and should be ignored
    ]
    driver = LocalStorageDriver(search_path=search_root)
    runs = driver.list_runs()
    assert isinstance(runs, list)
    assert len(runs) == len(expected)
    for expected_run in expected:
        assert expected_run in runs


def test_get_trajectory_file():
    driver = LocalStorageDriver(search_path=search_root)
    trajectory_file = driver.get_trajectory_file("sim_id_0001").readlines()
    assert trajectory_file[0].strip() == "0"


def test_get_contact_file():
    driver = LocalStorageDriver(search_path=search_root)
    contact_file = driver.get_contact_file("sim_id_0001", "0").readlines()
    assert contact_file[0].strip() == "0"


def test_get_map_file():
    driver = LocalStorageDriver(search_path=search_root)
    driver.get_map_file("sim_id_0001", "0")


def test_get_coordinate_distribution_file():
    driver = LocalStorageDriver(search_path=search_root)
    driver.get_coordinate_distribution_file("sim_id_0001", "0")


def test_get_manifest():
    driver = LocalStorageDriver(search_path=search_root)
    driver.get_manifest("sim_id_0001")


def test_get_policy_file():
    driver = LocalStorageDriver(search_path=search_root)
    policy_file = driver.get_policy_file("sim_id_0001").readlines()
    assert len(policy_file) >= 10
