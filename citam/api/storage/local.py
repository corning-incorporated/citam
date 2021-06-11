#  Copyright 2021. Corning Incorporated. All rights reserved.
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
                required_keys = [
                    "RunID",
                    "SimulationHash",
                    "RunName",
                    "SimulationName",
                    "FacilityName",
                    "NumberOfAgents",
                ]
                keys_not_found = []
                is_manifest_valid = True
                for r_key in required_keys:
                    try:
                        _ = manifest_data[r_key]
                    except KeyError:
                        keys_not_found.append(r_key)
                        is_manifest_valid = False
                if not is_manifest_valid:
                    LOG.warning(
                        f'"{manifest}" does not define "{keys_not_found}". '
                        "The results for this manifest will be ignored "
                    )
                    continue

                self.result_dirs[manifest_data["RunID"]] = os.path.dirname(
                    manifest
                )
                self.runs.append(
                    {
                        "RunID": manifest_data["RunID"],
                        "SimulationHash": manifest_data["SimulationHash"],
                        "RunName": manifest_data["RunName"],
                        "SimulationName": manifest_data["SimulationName"],
                        "FacilityName": manifest_data["FacilityName"],
                    }
                )

        if len(self.result_dirs.keys()) == 0:
            raise NoResultsFoundError(
                "LocalStorageDriver did not find any valid manifest.json"
                f"files in the directory '{search_path}'"
            )

    def list_runs(self):
        return self.runs

    def get_coordinate_distribution_file(self, run_id, floor):
        manifest = self.get_manifest(run_id)
        return open(
            os.path.join(
                self.result_dirs[run_id],
                f'{manifest["floor_dict"][floor]}contact_dist_per_coord.csv',
            ),
            "r",
        )

    def get_trajectory_file(self, run_id):
        manifest = self.get_manifest(run_id)
        return open(
            os.path.join(
                self.result_dirs[run_id],
                manifest.get("trajectory_file", "trajectory.txt"),
            ),
            "r",
        )

    def get_trajectory_file_location(self, run_id):
        manifest = self.get_manifest(run_id)
        return os.path.join(
            self.result_dirs[run_id],
            manifest.get("trajectory_file", "trajectory.txt"),
        )

    def get_contact_file(self, run_id, floor):
        manifest = self.get_manifest(run_id)
        return open(
            os.path.join(
                self.result_dirs[run_id],
                f'{manifest["floor_dict"][floor]}contacts.txt',
            ),
            "r",
        )

    def get_map_file(self, run_id, floor):
        manifest = self.get_manifest(run_id)
        return open(
            os.path.join(
                self.result_dirs[run_id],
                f'{manifest["floor_dict"][floor]}map.svg',
            ),
            "rb",
        )

    def get_heatmap_file(self, run_id, floor):
        manifest = self.get_manifest(run_id)
        return open(
            os.path.join(
                self.result_dirs[run_id],
                f'{manifest["floor_dict"][floor]}heatmap.svg',
            ),
            "rb",
        )

    def get_manifest_file(self, run_id):
        return open(
            os.path.join(self.result_dirs[run_id], "manifest.json"), "r"
        )

    def get_pair_contact_file(self, run_id):
        return open(
            os.path.join(self.result_dirs[run_id], "pair_contact.csv"), "r"
        )

    def get_statistics_file(self, run_id):
        return open(
            os.path.join(self.result_dirs[run_id], "statistics.json"), "r"
        )

    def get_policy_file(self, run_id):
        return open(os.path.join(self.result_dirs[run_id], "policy.json"), "r")
