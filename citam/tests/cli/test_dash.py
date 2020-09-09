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


"""Test cases for the ``citam dash`` CLI subcommand"""

import os
import wsgiref.simple_server
from tempfile import TemporaryDirectory

import pytest

from citam import cli
from citam.conf import settings


@pytest.fixture(autouse=True)
def disable_blocking_run_forever_call(monkeypatch):
    """This prevents the ``citam dash`` command from starting the server"""
    monkeypatch.setattr(
        wsgiref.simple_server.WSGIServer,
        'serve_forever',
        lambda *args, **kwargs: None
    )


def test_valid_results_option():
    # Set a starting results path
    settings.result_path = os.path.dirname(__file__)

    # Create temporary directory
    with TemporaryDirectory() as td:
        results_dir = os.path.abspath(td)

        # Pass temp directory to CLI with --results
        parser = cli.get_parser()
        parsed = parser.parse_args(['dash', '--results', results_dir])
        parsed.func(**vars(parsed))

        # Assert results_dir is being set properly
        assert settings.result_path == results_dir


def test_invalid_dir_results_option():
    """
    This is to test that when an invalid or non-existent directory is
    specified via the CLI, the correct exception is raised.

    This test was difficult to write, because we need to guarantee that the
    directory specified is valid in the OS running the test, but also doesn't
    exist.  The approach taken here was to create a temporary directory to
    get a valid directory name, and then delete it to ensure the directory
    does not exist.
    """
    # Set a starting results path
    settings.result_path = os.path.dirname(__file__)

    # Create temporary directory
    td = TemporaryDirectory()
    results_dir = os.path.abspath(td.name)
    # delete temporary directory we just created
    td.cleanup()
    # ensure the directory does not exist
    assert not os.path.exists(results_dir)

    with pytest.raises(IOError):
        # Pass temp directory to CLI with --results
        parser = cli.get_parser()
        parsed = parser.parse_args(['dash', '--results', results_dir])
        parsed.func(**vars(parsed))