# Copyright 2020. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================


import logging
import os

from citam.engine.io.input_parser import parse_input_file
from citam.engine.main import run_simulation

LOG = logging.getLogger(__name__)


def engine_run(**kwargs):
    """Run a simulation

    This method is executed with the CLI call ``citam engine run``
    """
    LOG.debug("Preparing to run simulation")
    work_directory = kwargs.get("work_dir", os.path.abspath(os.getcwd()))

    LOG.debug("Working directory: '%s'", work_directory)
    LOG.info("Loading input file: %s", kwargs["input_file"])

    input_dict = parse_input_file(kwargs["input_file"])
    LOG.info("Starting simulation")
    run_simulation(input_dict)
    LOG.info("Simulation has completed")
