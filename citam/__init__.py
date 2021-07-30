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

from citam import api, cli, engine, conf

settings = conf.settings

# Alias key methods to make them available at the citam level
list_facilities = engine.main.list_facilities
load_floorplans = engine.main.load_floorplans
ingest_floorplan = engine.main.ingest_floorplan
show_navigation_network = engine.main.export_navigation_graph_to_svg
