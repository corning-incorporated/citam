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

__all__ = ["api", "cli", "engine", "settings"]

import os
import logging

from citam import api, cli, engine, conf
import citam.engine.io.storage_utils as su

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True, show_path=False, show_time=False)
    ],
)

settings = conf.settings

# Alias key methods to make them available at the citam level
list_facilities = engine.main.list_facilities
load_floorplans = engine.main.load_floorplans
ingest_floorplan = engine.main.ingest_floorplan
show_navigation_network = engine.main.export_navigation_graph_to_svg
show_floorplan = engine.main.show_floorplan
update_floorplan_from_svg = engine.main.update_floorplan_from_svg_file
build_navigation_network = engine.main.build_navigation_network
run_simulation = engine.main.run_simulation


def show_facility_summary(facility_name):
    # get floors
    facility_dir = su.get_facility_datadir(facility_name)
    if not os.path.isdir(facility_dir):
        raise ValueError("Facility not found.")
    floor_dirs = [
        f
        for f in os.listdir(facility_dir)
        if os.path.isdir(os.path.join(facility_dir, f))
    ]
    if len(floor_dirs) == 0:
        raise ValueError("No floors found in this facility")

    # load floorplan for each floor
    floorplans = load_floorplans(
        facility_name,
        [floor_dir.replace("floor_", "") for floor_dir in floor_dirs],
    )
    # Show summary stats
    for floorplan in floorplans:
        floorplan.show_summary()
