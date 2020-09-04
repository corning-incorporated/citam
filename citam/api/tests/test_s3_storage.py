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

from citam.api.storage.s3 import S3StorageDriver


def test_client_custom_config(monkeypatch):
    """
    This test uses a mocked boto3 session, which stores all arguments passed
    to the :class:`boto3.session.Storage()` constructor, then asserts the
    correct arguments were used
    """
    driver = S3StorageDriver(
        bucket='test_bucket',
        access_key='aBc',
        secret_key='dEf',
        storage_region='my_region',
        storage_url='http://example',
    )
    assert driver.bucket == 'test_bucket'
    assert driver.client.client_kwargs.get('aws_access_key_id') == 'aBc'
    assert driver.client.client_kwargs.get('aws_secret_access_key') == 'dEf'
    assert driver.client.client_kwargs.get('region_name') == 'my_region'
    assert driver.client.client_kwargs.get('endpoint_url') == 'http://example'


def test_list_runs():
    driver = S3StorageDriver(bucket='test_bucket')
    runs = driver.list_runs()
    assert isinstance(runs, list)
    assert len(runs) == 1
    assert runs[0] == 'test_result'
    assert len(driver.client.method_calls['list_objects_v2']) == 1


def test_get_trajectory_file():
    driver = S3StorageDriver(bucket='test_bucket')
    driver.get_trajectory_file('xyz')
    call_args = driver.client.method_calls['get_object'][-1]
    assert call_args['Key'] == 'xyz/trajectory.txt'


def test_get_contact_file():
    driver = S3StorageDriver(bucket='test_bucket')
    driver.get_contact_file('xyz', '0')
    call_args = driver.client.method_calls['get_object'][-1]
    assert call_args['Key'] == 'xyz/floor_0/contacts.txt'


def test_get_map_file():
    driver = S3StorageDriver(bucket='test_bucket')
    driver.get_map_file('xyz', '0')
    call_args = driver.client.method_calls['get_object'][-1]
    assert call_args['Key'] == 'xyz/floor_0/map.svg'


def test_get_coordinate_distribution_file():
    driver = S3StorageDriver(bucket='test_bucket')
    driver.get_coordinate_distribution_file('xyz', '0')
    call_args = driver.client.method_calls['get_object'][-1]
    assert call_args['Key'] == 'xyz/floor_0/contact_dist_per_coord.csv'


def test_get_manifest():
    driver = S3StorageDriver(bucket='test_bucket')
    driver.get_manifest('xyz')
    call_args = driver.client.method_calls['get_object'][-1]
    assert call_args['Key'] == 'xyz/manifest.json'
