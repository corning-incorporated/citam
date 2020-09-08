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

"""
=================
CITAM Results API
=================
Python backend for retrieving CITAM model results

--------
Commands
--------
* Start the API server locally::

      python -m citam.api

* Start the API server for production use::

      gunicorn citam.api:app

"""
__all__ = ['app', 'run_server']

import logging
import os
from wsgiref import simple_server
from citam.api.server import get_wsgi_app
from citam.conf import settings

LOG = logging.getLogger(__name__)

#: The exposed WSGI application.  Start the server with the command
app = get_wsgi_app()


def run_server(port=8000, host='127.0.0.1', results=None, *args, **kwargs):
    if os.path.isdir(os.path.abspath(results)):
        LOG.debug("Result path '%s' specified to CLI. Updating settings.")
        settings.result_path = os.path.abspath(results)
    LOG.info("Attempting to start server on %s:%s", host, port)
    httpd = simple_server.make_server(host, port, app)
    print(f"Running CITAM Server on http://{host}:{port}", flush=True)
    httpd.serve_forever()
