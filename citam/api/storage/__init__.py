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

__all__ = ['s3', 'local', 'BaseStorageDriver']

import abc
import json


class BaseStorageDriver(abc.ABC):
    """Base class for CITAM storage engines"""

    @abc.abstractmethod
    def list_runs(self):
        """List all simulations"""

    @abc.abstractmethod
    def get_coordinate_distribution_file(self, sim_id, floor):
        """
        Return the Coordinate Distribution file for a simulation

        :param str sim_id: simulation identifier
        :param str floor: Floor number
        :return: Coordinate Distribution file
        :rtype: StringIO
        """

    @abc.abstractmethod
    def get_trajectory_file(self, sim_id):
        """
        Return the trajectory file for a simulation

        :param str sim_id: simulation identifier
        :return: Trajectory file
        :rtype: StringIO
        """

    @abc.abstractmethod
    def get_contact_file(self, sim_id, floor):
        """
        Return the contact file for a simulation

        :param str sim_id: simulation identifier
        :param str floor: Floor number
        :return: Contacts file
        :rtype: io.StringIO
        """

    @abc.abstractmethod
    def get_map_file(self, sim_id, floor):
        """
        Return the map image for given simulation

        :param str sim_id: simulation identifier
        :param str floor: Floor number
        :return: Map file
        :rtype: io.BytesIO
        """

    @abc.abstractmethod
    def get_manifest_file(self, sim_id):
        """
        Return the manifest file for a simulation

        :param str sim_id: simulation identifier
        :return: Simulation Manifest file
        :rtype: io.StringIO
        """

    def get_manifest(self, sim_id):
        """
        Return the parsed manifest for a simulation

        :param str sim_id: simulation identifier
        :return: Simulation Manifest
        :rtype: dict
        """
        manifest = json.loads(self.get_manifest_file(sim_id).read())

        manifest['sim_id'] = sim_id
        manifest['floor_dict'] = {
            floor['name']: floor['directory']
            for floor in manifest['floors']
        }
        return manifest
