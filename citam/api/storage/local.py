#  Copyright 2020. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the licenses granted by
#  Corning Incorporated. All other uses as well as any copying, modification or
#  reverse engineering of the software is strictly prohibited.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
#  WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
#  ==============================================================================

__all__ = ["LocalStorageDriver"]

import json
import logging
import os
from glob import glob

from citam.api.storage import BaseStorageDriver, NoResultsFoundError

LOG = logging.getLogger(__name__)


class LocalStorageDriver(BaseStorageDriver):
    """Local storage driver for simulation results.

    This driver will scan the provided search_path for valid manifest.json
    files when initialized.

    :param str search_path:
        Search root for simulation results.
    """

    def __init__(self, search_path, **kwargs):  # noqa
        super().__init__()
        self.search_path = search_path
        self.result_dirs = {}
        self.runs = []

        if os.path.isdir(search_path):
            LOG.info(
                "Initializing LocalStorageDriver with root path %s",
                search_path,
            )

            search_path = os.path.join(
                os.path.abspath(search_path), "**", "manifest.json"
            )

            LOG.debug("search_path: %s", search_path)
            manifests = glob(search_path, recursive=True)

            LOG.info(
                "LocalStorageDriver found %d manifest.json files",
                len(manifests),
            )

        else:
            raise IOError(
                f"search_path '{search_path}' is invalid. search_path "
                f"must reference a directory"
            )

        for manifest in manifests:
            with open(manifest, "r") as manifest_file:
                manifest_data = json.load(manifest_file)
                try:
                    run_id = manifest_data["RunID"]
                except KeyError:
                    LOG.warning(
                        '"%s" does not define "RunID". '
                        "The results for this manifest will be ignored ",
                        manifest,
                    )
                    continue
                try:
                    sim_hash = manifest_data["SimulationHash"]
                except KeyError:
                    LOG.warning(
                        '"%s" does not define "SimulationHash". '
                        "The results for this manifest will be ignored ",
                        manifest,
                    )
                    continue
                # try:
                #     manifest_data["TotalTimesteps"]
                # except KeyError:
                #     LOG.warning(
                #         '"%s" does not define "TotalTimesteps". '
                #         "The results for this manifest will be ignored ",
                #         manifest,
                #     )
                #     continue

                if "FacilityName" in manifest_data:
                    facility_name = manifest_data["FacilityName"]
                elif "Campus" in manifest_data:
                    facility_name = manifest_data["Campus"]
                else:
                    LOG.warning(
                        '"%s" does not define "FacilityName" or "Campus". '
                        "The results for this manifest will be ignored ",
                        manifest,
                    )
                    continue

                self.result_dirs[run_id] = os.path.dirname(manifest)
                self.runs.append(
                    {
                        "run_id": run_id,
                        "sim_hash": sim_hash,
                        "facility_name": facility_name,
                    }
                )

        if len(self.result_dirs.keys()) == 0:
            raise NoResultsFoundError(
                "LocalStorageDriver did not find any valid manifest.json"
                f"files in the directory '{search_path}'"
            )

    def list_runs(self):
        return self.runs

    def get_coordinate_distribution_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        return open(
            os.path.join(
                self.result_dirs[sim_id],
                f'{manifest["floor_dict"][floor]}contact_dist_per_coord.csv',
            ),
            "r",
        )

    def get_trajectory_file(self, sim_id):
        manifest = self.get_manifest(sim_id)
        return open(
            os.path.join(
                self.result_dirs[sim_id],
                manifest.get("trajectory_file", "trajectory.txt"),
            ),
            "r",
        )

    def get_trajectory_file_location(self, sim_id):
        manifest = self.get_manifest(sim_id)
        return os.path.join(
            self.result_dirs[sim_id],
            manifest.get("trajectory_file", "trajectory.txt"),
        )

    def get_contact_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        return open(
            os.path.join(
                self.result_dirs[sim_id],
                f'{manifest["floor_dict"][floor]}contacts.txt',
            ),
            "r",
        )

    def get_map_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        return open(
            os.path.join(
                self.result_dirs[sim_id],
                f'{manifest["floor_dict"][floor]}map.svg',
            ),
            "rb",
        )

    def get_heatmap_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        return open(
            os.path.join(
                self.result_dirs[sim_id],
                f'{manifest["floor_dict"][floor]}heatmap.svg',
            ),
            "rb",
        )

    def get_manifest_file(self, sim_id):
        return open(
            os.path.join(self.result_dirs[sim_id], "manifest.json"), "r"
        )

    def get_pair_contact_file(self, sim_id):
        return open(
            os.path.join(self.result_dirs[sim_id], "pair_contact.csv"), "r"
        )

    def get_statistics_file(self, sim_id):
        return open(
            os.path.join(self.result_dirs[sim_id], "statistics.json"), "r"
        )

    def get_policy_file(self, sim_id):
        return open(os.path.join(self.result_dirs[sim_id], "policy.json"), "r")
