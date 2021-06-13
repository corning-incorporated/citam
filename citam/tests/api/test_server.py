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
import os

import pytest
from falcon import testing
from falcon.routing import StaticRoute

import citam
from citam.api import server


@pytest.fixture(scope="session")
def static_path(tmp_path_factory):
    """Create a directory with mocked versions of dash static files"""
    static_dir = tmp_path_factory.mktemp(basename="dash")
    with open(os.path.join(static_dir, "main.js"), "w") as f:
        f.write("file: main.js")
    with open(os.path.join(static_dir, "index.html"), "w") as f:
        f.write("file: index.html")
    return str(static_dir)


@pytest.fixture(autouse=True)
def static_route(monkeypatch, static_path):
    """Mock static routes to test dash logic without requiring JS"""

    class MockedStaticRoute(StaticRoute):
        def __init__(self, prefix, directory, *args, **kwargs):  # noqa
            super().__init__(prefix, str(static_path), *args, **kwargs)

    monkeypatch.setattr(citam.api.server, "StaticRoute", MockedStaticRoute)


@pytest.fixture
def client(use_local_storage) -> testing.TestClient:
    return testing.TestClient(server.get_wsgi_app())


def test_get_summary(client):
    result = client.simulate_get("/v1/run_id_0001")
    assert result.status_code == 200


def test_trajectory_response(client):
    result: testing.Result = client.simulate_get(
        "/v1/run_id_0001/trajectory?first_timestep=1&max_steps=5000"
    )
    assert result.status_code == 200
    assert result.json.get("data")
    assert len(result.json["data"]) == 1899
    assert result.json.get("statistics")
    assert result.json["statistics"].get("cfl")


def test_trajectory_response_large_traj(client):
    result: testing.Result = client.simulate_get(
        "/v1/51a37fa7054a3f8e8d55/trajectory?"
        + "first_timestep=0&max_steps=15000"
    )
    assert result.status_code == 200
    assert result.json.get("data")
    assert len(result.json["data"]) == 12200
    assert result.json.get("statistics")
    assert result.json["statistics"].get("cfl")


def test_get_total_timesteps(client):
    result: testing.Result = client.simulate_get(
        "/v1/51a37fa7054a3f8e8d55/total_timesteps"
    )
    assert result.status_code == 200
    assert result.json.get("data")
    assert result.json["data"] == 12200


def test_contact_response(client):
    result: testing.Result = client.simulate_get("/v1/run_id_0001/contact")
    assert result.status_code == 200
    assert isinstance(result.json, list)


def test_contact_distribution_response(client):
    result: testing.Result = client.simulate_get(
        "/v1/run_id_0001/distribution/coordinate"
    )
    assert result.status_code == 200
    assert isinstance(result.json, list)


def test_map_response(client):
    result: testing.Result = client.simulate_get("/v1/run_id_0001/map")
    assert result.status_code == 200


def test_get_heatmap(client):
    result = client.simulate_get("/v1/run_id_0001/heatmap")
    assert result.status_code == 200


def test_get_policy(client):
    result = client.simulate_get("/v1/run_id_0001/policy")
    assert result.status_code == 200


def test_get_statistics(client):
    result = client.simulate_get("/v1/run_id_0001/statistics")
    assert result.status_code == 200
    assert isinstance(result.json, list)


def test_get_pair_contact(client):
    result = client.simulate_get("/v1/run_id_0001/pair")
    assert result.status_code == 200
    assert isinstance(result.json, list)


def test_list_response(client):
    """
    note: The result here is set by the mock.
    See :mod:`citam.api.tests.conftest` for more information.
    """
    result: testing.Result = client.simulate_get("/v1/list")
    assert result.status_code == 200
    assert isinstance(result.json, list)
    assert len(result.json) == 3
    assert "RunID" in result.json[0]
    assert "SimulationHash" in result.json[0]
    assert "FacilityName" in result.json[0]

    run_ids = [
        "run_id_0001",
        "run_id_0002",
        "51a37fa7054a3f8e8d55",
    ]
    assert result.json[0]["RunID"] in run_ids
    assert result.json[1]["RunID"] in run_ids


def test_redoc(client):
    result: testing.Result = client.simulate_get("/v1")
    assert result.status_code == 200


def test_openapi_response(client):
    result: testing.Result = client.simulate_get("/v1/openapi.yaml")
    assert result.status_code == 200


def test_index(client):
    result: testing.Result = client.simulate_get("/")
    assert result.status_code == 200


def test_404(client):
    expected = client.simulate_get("/")
    actual = client.simulate_get("/invalid/path")
    assert actual.status_code == 200
    assert actual.content == expected.content


def test_static_route(client):
    result: testing.Result = client.simulate_get("/main.js")
    assert result.status_code == 200
    assert result.text == "file: main.js"
