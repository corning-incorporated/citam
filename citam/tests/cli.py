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
import wsgiref.simple_server
from tempfile import TemporaryDirectory
from citam import cli
from citam.conf import settings


def test_dash_results(monkeypatch):
    # Prevent server from actually starting
    monkeypatch.setattr(
        wsgiref.simple_server.WSGIServer,
        'serve_forever',
        lambda *args, **kwargs: None
    )

    # Create temporary directory
    with TemporaryDirectory() as td:
        results_dir = os.path.abspath(td)

        # Pass temp directory to CLI with --results
        parser = cli.get_parser()
        parsed = parser.parse_args(['dash', '--results', results_dir])
        parsed.func(**vars(parsed))

        # Assert results_dir is being set properly
        assert settings.result_path == results_dir
