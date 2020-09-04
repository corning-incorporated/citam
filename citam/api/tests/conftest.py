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
import pytest
import citam.api.storage

TEST_RESULT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'sample_results',
    'TF',
)


class MockedSession:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.client_args = None
        self.client_kwargs = None
        self.method_calls = {
            'list_objects_v2': [],
            'get_object': [],
        }

    def client(self, *args, **kwargs):
        self.client_args = args
        self.client_kwargs = kwargs
        return self

    def list_objects_v2(self, *args, **kwargs):
        self.method_calls['list_objects_v2'].append(
            {'args': args, 'kwargs': kwargs}
        )
        return {'CommonPrefixes': [{'Prefix': 'test_result/'}]}

    def get_object(self, Key=None, *args, **kwargs):
        self.method_calls['get_object'].append(
            {'Key': Key, 'args': args, 'kwargs': kwargs}
        )

        filename = '/'.join(Key.split('/')[1:])
        return {'Body': open(
            os.path.join(TEST_RESULT_PATH, filename),
            'rb'
        )}


@pytest.fixture(autouse=True)
def s3_client(monkeypatch):
    monkeypatch.setenv('CITAM_STORAGE_SECRET', 'xyz')
    monkeypatch.setenv('CITAM_STORAGE_KEY', 'abc')
    monkeypatch.setenv('CITAM_STORAGE_BUCKET', 'abc')
    monkeypatch.setenv('CITAM_STORAGE_REGION', 'us-east-1')
    monkeypatch.setenv('CITAM_STORAGE_URL', 'amazonaws.com')
    monkeypatch.setattr(
        citam.api.storage.s3.boto3.session,
        'Session',
        lambda *args, **kwargs: MockedSession()
    )
