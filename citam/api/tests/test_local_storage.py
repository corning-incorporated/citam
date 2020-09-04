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

import os
from citam.api.storage.local import LocalStorageDriver

search_root = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'sample_results',
)


def test_results_found(monkeypatch):
    """
    This test uses a mocked boto3 session, which stores all arguments passed
    to the :class:`boto3.session.Storage()` constructor, then asserts the
    correct arguments were used
    """
    driver = LocalStorageDriver(search_path=search_root)
    assert len(driver.result_dirs) == 2


def test_list_runs():
    expected = [
        'sim_id_0001',
        'sim_id_0002'
    ]
    driver = LocalStorageDriver(search_path=search_root)
    runs = driver.list_runs()
    print(runs)
    assert isinstance(runs, list)
    assert len(runs) == len(expected)
    for expected_run in expected:
        assert expected_run in runs


def test_get_trajectory_file():
    driver = LocalStorageDriver(search_path=search_root)
    trajectory_file = driver.get_trajectory_file('sim_id_0001').readlines()
    assert trajectory_file[0].strip() == "0"


def test_get_contact_file():
    driver = LocalStorageDriver(search_path=search_root)
    contact_file = driver.get_contact_file('sim_id_0001', '0').readlines()
    assert contact_file[0].strip() == "0"


def test_get_map_file():
    driver = LocalStorageDriver(search_path=search_root)
    driver.get_map_file('sim_id_0001', '0')


def test_get_coordinate_distribution_file():
    driver = LocalStorageDriver(search_path=search_root)
    driver.get_coordinate_distribution_file('sim_id_0001', '0')


def test_get_manifest():
    driver = LocalStorageDriver(search_path=search_root)
    driver.get_manifest('sim_id_0001')
