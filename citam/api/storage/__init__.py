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

__all__ = ["s3", "local", "BaseStorageDriver", "NoResultsFoundError"]

import abc
import json
import io
from typing import List, Dict, TextIO


class NoResultsFoundError(IOError):
    """Error raised when no results were found by the driver"""


class BaseStorageDriver(abc.ABC):
    """Base class for CITAM storage engines"""

    def __init__(self, **kwargs):  # noqa
        pass

    @abc.abstractmethod
    def list_runs(self) -> List[str]:
        """List all simulations

        :return: A list of completed simulations
        """

    @abc.abstractmethod
    def get_coordinate_distribution_file(
        self, sim_id: str, floor: str
    ) -> TextIO:
        """Return the Coordinate Distribution file for a simulation

        :param sim_id: simulation identifier
        :param floor: Floor number
        :return: Coordinate Distribution file
        """

    @abc.abstractmethod
    def get_trajectory_file(self, sim_id: str) -> TextIO:
        """Return the trajectory file for a simulation

        :param sim_id: simulation identifier
        :return: Trajectory file
        """

    @abc.abstractmethod
    def get_contact_file(self, sim_id: str, floor: str) -> TextIO:
        """Return the contact file for a simulation

        :param sim_id: simulation identifier
        :param floor: Floor number
        :return: Contacts file
        """

    @abc.abstractmethod
    def get_map_file(self, sim_id: str, floor: str) -> io.BytesIO:
        """Return the map image for given simulation

        :param sim_id: simulation identifier
        :param floor: Floor number
        :return: Map file
        """

    @abc.abstractmethod
    def get_manifest_file(self, sim_id: str) -> TextIO:
        """Return the manifest file for a simulation

        :param sim_id: simulation identifier
        :return: Simulation manifest file
        """

    @abc.abstractmethod
    def get_heatmap_file(self, sim_id: str, floor: str) -> io.BytesIO:
        """Return a heatmap file for a simulation and floor

        :param sim_id: simulation identifier
        :param floor: Floor number
        :return: Heatmap File
        """

    @abc.abstractmethod
    def get_pair_contact_file(self, sim_id: str) -> TextIO:
        """Return the pair contact file for a simulation

        :param sim_id: simulation identifier
        :return: Pair contact file
        """

    @abc.abstractmethod
    def get_statistics_file(self, sim_id: str) -> TextIO:
        """Get the statistics file for a simulation

        :param sim_id: simulation identifier
        """

    @abc.abstractmethod
    def get_policy_file(self, sim_id: str) -> TextIO:
        """Get the statistics file for a simulation

        :param sim_id: simulation identifier
        """

    def get_manifest(self, sim_id: str) -> Dict:
        """
        Return the parsed manifest for a simulation

        :param sim_id: simulation identifier
        :return: Simulation Manifest
        """
        manifest = json.loads(self.get_manifest_file(sim_id).read())

        manifest["sim_id"] = sim_id
        manifest["floor_dict"] = {
            floor["name"]: floor["directory"] for floor in manifest["floors"]
        }
        return manifest
