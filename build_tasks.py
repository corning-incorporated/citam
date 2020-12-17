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

import logging
import os
import shutil
import subprocess
import sys
import warnings
from distutils.core import Command

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
NODE_ROOT = os.path.join(BASE_DIR, "citamjs")
NODE_OUTPUT_DIR = os.path.join(NODE_ROOT, "dist")
CITAM_STATIC_DIR = os.path.join(BASE_DIR, "citam", "api", "static", "dash")
LOG = logging.getLogger(__name__)


class NodeJSBuild(Command):
    """distutils/setuptools command for building NodeJS modules

    example::

        # setup.py
        import setuptools
        from build_tasks import NodeJSBuild

        setuptools.setup(
            # ...
            cmdclass={'build_js': NodeJSBuild}
        )

    """

    user_options = []

    def initialize_options(self):
        """There are currently no options for this command"""

    def finalize_options(self):
        """There are currently no options for this command"""

    def run(self):
        """Perform a nodejs build for the given path"""
        env = os.environ.copy()

        # shell=True is required for subprocess in windows
        shell = True if sys.platform == "win32" else False

        try:
            subprocess.check_call(["npm", "-v"], env=env, shell=shell)
        except (subprocess.SubprocessError, FileNotFoundError):
            warnings.warn(
                "Unable to detect NodeJS installation. Skipping "
                "NodeJS build step"
            )
            return

        try:
            LOG.info("Building NodeJS artifacts")
            original_dir = os.getcwd()
            os.chdir(NODE_ROOT)

            # NODE_ENV=development is set to install dev_dependencies
            env["NODE_ENV"] = "development"
            subprocess.run(
                ["npm", "install", "--progress=false"],
                check=True,
                env=env,
                shell=shell,
            )

            # NODE_ENV=production triggers build-time optimizations
            env["NODE_ENV"] = "production"
            subprocess.run(
                ["npm", "run", "build"], check=True, env=env, shell=shell
            )

            # TODO: Make JS compile directly to CITAM_STATIC_DIR
            LOG.info("Cleaning previously generated NodeJS artifacts")
            if os.path.exists(CITAM_STATIC_DIR):
                shutil.rmtree(CITAM_STATIC_DIR, ignore_errors=True)

            LOG.info("Copying NodeJS artifacts into package")
            shutil.copytree(NODE_OUTPUT_DIR, CITAM_STATIC_DIR)
            os.chdir(original_dir)
        except (subprocess.SubprocessError, FileNotFoundError):
            warnings.warn(
                "NodeJS build Failed. "
                "The CITAM dashboard will not be available"
            )
            return
