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

import pytest
from falcon import testing

from citam.api import server


@pytest.fixture
def client() -> testing.TestClient:
    return testing.TestClient(server.get_wsgi_app())


def test_trajectory_response(client):
    result: testing.Result = client.simulate_get(
        '/v1/sim_id_0001/trajectory'
    )
    assert result.status_code == 200
    assert result.json.get('data')
    assert result.json.get('statistics')
    assert result.json['statistics'].get('max_contacts')


def test_contact_response(client):
    result: testing.Result = client.simulate_get(
        '/v1/sim_id_0001/contact'
    )
    assert result.status_code == 200
    assert isinstance(result.json, list)


def test_contact_distribution_response(client):
    result: testing.Result = client.simulate_get(
        '/v1/sim_id_0001/distribution/coordinate'
    )
    assert result.status_code == 200
    assert isinstance(result.json, list)


def test_map_response(client):
    result: testing.Result = client.simulate_get(
        '/v1/sim_id_0001/map'
    )
    assert result.status_code == 200


def test_list_response(client):
    """
    note: The result here is set by the mock.
    See :mod:`citam.api.tests.conftest` for more information.
    """
    result: testing.Result = client.simulate_get(
        '/v1/list'
    )
    assert result.status_code == 200
    assert isinstance(result.json, list)
    assert len(result.json) == 2
    assert 'sim_id_0001' in result.json
    assert 'sim_id_0002' in result.json


def test_redoc(client):
    result: testing.Result = client.simulate_get('/v1')
    assert result.status_code == 200


def test_openapi_response(client):
    result: testing.Result = client.simulate_get('/v1/openapi.yaml')
    assert result.status_code == 200


def test_index(client):
    result: testing.Result = client.simulate_get('/')
    assert result.status_code == 200
