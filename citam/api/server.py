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

"""WSGI Server Entrypoint

The CITAM results API is for retrieving results and SVG maps related to the
CITAM COVID-19 model.


.. note::
    To use local results instead of the result storage server,
    set the environment variable ``USE_LOCAL_RESULTS=True`` when running
    gunicorn

"""

__all__ = ["get_wsgi_app"]

import logging
from os.path import abspath, dirname, join, exists
from typing import Any

import falcon
from falcon.routing import StaticRoute

from citam.api import parser
from citam.conf import settings
import time

LOG = logging.getLogger(__name__)


# noinspection PyUnusedLocal
class ResultsResource:
    """Results file APIs"""

    def on_get_list(self, req: falcon.Request, resp: falcon.response):
        """Get the base map as an SVG"""
        resp.media = settings.storage_driver.list_runs()
        resp.status = falcon.HTTP_200

    def on_get_summary(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get simulation summary"""
        resp.media = settings.storage_driver.get_manifest(sim_id)
        resp.status = falcon.HTTP_200

    def on_get_trajectory(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get trajectory data"""
        floor = req.params.get("floor")  # Floor is allowed to be None here.
        offset = (
            int(req.params.get("offset")) if req.params.get("offset") else 0
        )
        first_timestep = int(req.params.get("first_timestep"))
        max_steps = int(req.params.get("max_steps"))
        start_time = time.time()
        resp.media = parser.get_trajectories(
            sim_id, floor, offset, first_timestep, max_steps
        )
        resp.status = falcon.HTTP_200
        print("Total time: ", time.time() - start_time)

    def on_get_trajectory_lines(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get trajectory data"""
        floor = req.params.get("floor")  # Floor is allowed to be None here.
        resp.media = parser.get_trajectories_lines(sim_id, floor)
        resp.status = falcon.HTTP_200

    def on_get_contact(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get contact data"""
        floor = req.params.get("floor")
        if not floor:
            # If floor is not specified, use the first listed floor in manifest
            manifest = settings.storage_driver.get_manifest(sim_id)
            floor = manifest["floors"][0]["name"]
        resp.media = parser.get_contacts(sim_id, floor)
        resp.status = falcon.HTTP_200

    def on_get_map(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get the base map as an SVG"""
        floor = req.params.get("floor")
        if not floor:
            # If floor is not specified, use the first listed floor in manifest
            manifest = settings.storage_driver.get_manifest(sim_id)
            floor = manifest["floors"][0]["name"]
        resp.body = settings.storage_driver.get_map_file(sim_id, floor).read()
        resp.content_type = "image/svg+xml"
        resp.status = falcon.HTTP_200

    def on_get_heatmap(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get the base map as an SVG"""
        floor = req.params.get("floor")
        if not floor:
            # If floor is not specified, use the first listed floor in manifest
            manifest = settings.storage_driver.get_manifest(sim_id)
            floor = manifest["floors"][0]["name"]
        resp.body = settings.storage_driver.get_heatmap_file(
            sim_id, floor
        ).read()
        resp.content_type = "image/svg+xml"
        resp.status = falcon.HTTP_200

    def on_get_coordinate_dist(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get the contact per coordinate distribution"""
        floor = req.params.get("floor")
        if not floor:
            # If floor is not specified, use the first listed floor in manifest
            manifest = settings.storage_driver.get_manifest(sim_id)
            floor = manifest["floors"][0]["name"]
        resp.media = parser.get_coordinate_distribution(sim_id, floor)
        resp.status = falcon.HTTP_200

    def on_get_pair_contact(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get pair contact data"""
        resp.media = parser.get_pair_contacts(sim_id)
        resp.status = falcon.HTTP_200

    def on_get_statistics(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get statistics.json data"""
        resp.media = parser.get_statistics_json(sim_id)
        resp.status = falcon.HTTP_200

    def on_get_policy(
        self, req: falcon.Request, resp: falcon.response, sim_id: str
    ):
        """Get statistics.json data"""
        resp.media = parser.get_policy_json(sim_id)
        resp.status = falcon.HTTP_200


# noinspection PyUnusedLocal
class RedocResource:
    """API Documentation Page"""

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.status = falcon.HTTP_200
        resp.content_type = "text/html"

        filename = join(dirname(abspath(__file__)), "static", "redoc.html")
        with open(filename) as f:
            resp.body = f.read()


# noinspection PyUnusedLocal
class DashIndexResource:
    """API Documentation Page"""

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.status = falcon.HTTP_200
        resp.content_type = "text/html"
        file = join(dirname(abspath(__file__)), "static", "dash", "index.html")
        if not exists(file):
            LOG.warning("CITAM Dash is not included with this build")
            file = join(dirname(dirname(file)), "dash404.html")
        with open(file) as f:
            resp.body = f.read()


# noinspection PyUnusedLocal
class OpenAPIResource:
    """API Endpoint to download the OpenAPI specification"""

    YAML_SPEC = join(dirname(abspath(__file__)), "static", "openapi.yaml")

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.content_type = "application/x-yaml"
        with open(self.YAML_SPEC, "rb") as f:
            resp.body = f.read()
        resp.status = falcon.HTTP_200


# noinspection PyUnusedLocal
class CORSMiddleware:
    """Middleware to enable CORS requests"""

    def process_response(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        resource: Any,
        req_succeeded: bool,
    ):
        resp.set_header("Access-Control-Allow-Origin", "*")

        if (
            req.get_header("Access-Control-Request-Method")
            and req.method == "OPTIONS"
        ):  # pragma: no cover
            # CORS preflight request
            # Note, we don't have any resources that would trigger a
            # preflight request, so this should never be called, but it was
            # included just in case

            allow = resp.get_header("Allow")
            resp.delete_header("Allow")

            allow_headers = req.get_header(
                "Access-Control-Request-Headers", default="*"
            )

            resp.set_headers(
                [
                    ("Access-Control-Allow-Methods", allow),
                    ("Access-Control-Allow-Headers", allow_headers),
                    ("Access-Control-Max-Age", "86400"),
                ]
            )


def _get_sink():
    """Generate the API sink method given a static resolver.

    The current version of falcon (as of 2020-09-14) always allows sinks to
    supersede static routes (https://github.com/falconry/falcon/issues/1372).

    This method injects a built-in :class:falcon.routing.StaticRoute` object
    into the sink method, and the method checks the static route and only
    executes the sink logic if no static file was found.
    """

    static_route = StaticRoute(
        "/",
        join(dirname(abspath(__file__)), "static", "dash"),
    )

    def _sink(req, resp):
        """This handles all 404s and converts them to index.html

        We need this so ``citam dash`` can handle links to specific subpages
        :param falcon.Request req: incoming request
        :param falcon.Response resp: outgoing response
        """

        if static_route.match(req.path):
            try:  # Try static route
                static_route(req, resp)
                LOG.debug("%s refers to a static file", req.path)
                return
            except falcon.HTTPNotFound:  # Abort static file resolution
                LOG.debug(
                    "%s does not match a resource. returning index.html",
                    req.path,
                )

        file = join(dirname(abspath(__file__)), "static", "dash", "index.html")
        if not exists(file):
            LOG.warning("CITAM Dash is not included with this build")
            file = join(dirname(dirname(file)), "dash404.html")

        with open(file) as f:
            LOG.debug("Returning file")
            resp.status = falcon.HTTP_200
            resp.body = f.read()

    return _sink


def get_wsgi_app():
    """
    Return the WSGI application for this API.
    This should be used with a WSGI server like Gunicorn
    """
    app = falcon.API(middleware=[CORSMiddleware()])
    results = ResultsResource()

    app.add_route("/", DashIndexResource())
    app.add_route("/v1", RedocResource())
    app.add_route("/v1/openapi.yaml", OpenAPIResource())

    app.add_route("/v1/list", results, suffix="list")
    app.add_route("/v1/{sim_id}", results, suffix="summary")
    app.add_route("/v1/{sim_id}/trajectory", results, suffix="trajectory")
    app.add_route(
        "/v1/{sim_id}/trajectory_lines", results, suffix="trajectory_lines"
    )
    app.add_route("/v1/{sim_id}/contact", results, suffix="contact")
    app.add_route("/v1/{sim_id}/map", results, suffix="map")
    app.add_route(
        "/v1/{sim_id}/distribution/coordinate",
        results,
        suffix="coordinate_dist",
    )
    app.add_route("/v1/{sim_id}/pair", results, suffix="pair_contact")
    app.add_route("/v1/{sim_id}/statistics", results, suffix="statistics")
    app.add_route("/v1/{sim_id}/heatmap", results, suffix="heatmap")
    app.add_route("/v1/{sim_id}/policy", results, suffix="policy")
    app.add_sink(_get_sink())
    return app
