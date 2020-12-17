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

__all__ = ["S3StorageDriver"]

import logging
import boto3
from datetime import datetime
from io import BytesIO, StringIO
from citam.api.storage import BaseStorageDriver

LOG = logging.getLogger(__name__)


class S3StorageDriver(BaseStorageDriver):
    def __init__(self, bucket, **kwargs):
        super().__init__()
        self.bucket = bucket
        self.client = self._get_s3_client(**kwargs)

    def _get_s3_client(self, **kwargs):
        """
        Return a S3 client for fetching result files

        :param verify ssl:
            Whether to verify SSL Certificates.
        :param bool ssl:
            Whether to use SSL for the S3 Connection.
        :param str access_key:
            S3 Access Key.
        :param str secret_key:
            S3 Secret Key.
        :param str region_name:
            S3 region name.
        :param str storage_url:
            S3 storage url.
        """

        session = boto3.session.Session()
        return session.client(
            service_name="s3",
            use_ssl=kwargs.get("ssl", False),
            verify=kwargs.get("verify", False),
            region_name=kwargs.get("storage_region"),
            endpoint_url=kwargs.get("storage_url"),
            aws_access_key_id=kwargs.get("access_key"),
            aws_secret_access_key=kwargs.get("secret_key"),
        )

    def _get_text_file(self, sim_id, filename):
        """
        Load a text file from S3

        :param str sim_id: simulation identifier
        :param str filename: Result filename
        :rtype: StringIO
        """

        start_time = datetime.now()
        LOG.info("Downloading file: '%s'", filename)

        response = self.client.get_object(
            Bucket=self.bucket,
            Key=f"{sim_id}/{filename}",
        )
        output = StringIO()
        output.write(response["Body"].read().decode("UTF-8"))
        output.seek(0)

        elapsed = datetime.now() - start_time
        LOG.info(
            "Completed download, time: %d seconds", elapsed.total_seconds()
        )
        return output

    def list_runs(self):
        prefixes = self.client.list_objects_v2(
            Bucket=self.bucket,
            Delimiter="/",
        )["CommonPrefixes"]

        return list(map(lambda x: x["Prefix"].strip("/"), prefixes))

    def get_coordinate_distribution_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        return self._get_text_file(
            sim_id,
            f'{manifest["floor_dict"][floor]}contact_dist_per_coord.csv',
        )

    def get_trajectory_file(self, sim_id):
        manifest = self.get_manifest(sim_id)
        return self._get_text_file(
            sim_id, manifest.get("trajectory_file", "trajectory.txt")
        )

    def get_contact_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        return self._get_text_file(
            sim_id,
            f'{manifest["floor_dict"][floor]}contacts.txt',
        )

    def get_map_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=f'{sim_id}/{manifest["floor_dict"][floor]}map.svg',
        )

        output = BytesIO()
        output.write(response["Body"].read())
        output.seek(0)

        return output

    def get_heatmap_file(self, sim_id, floor):
        manifest = self.get_manifest(sim_id)
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=f'{sim_id}/{manifest["floor_dict"][floor]}heatmap.svg',
        )

        output = BytesIO()
        output.write(response["Body"].read())
        output.seek(0)

        return output

    def get_manifest_file(self, sim_id):
        # TODO: This could be cached.
        #  This may be called more than once per request
        return self._get_text_file(sim_id, "manifest.json")

    def get_pair_contact_file(self, sim_id):
        return self._get_text_file(sim_id, "pair_contact.csv")

    def get_statistics_file(self, sim_id):
        return self._get_text_file(sim_id, "statistics.json")
