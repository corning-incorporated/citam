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

"""Methods to load overridable user-defined settings"""
__all__ = ['settings']

import logging
import os
from importlib import import_module
from typing import Any, Union

from citam.api.storage import BaseStorageDriver


def _import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.

    .. note::
        This is based on the ``django.utils.module_loading.import_string``
        method from the Django project.

    :param str dotted_path: Class as dot-delimited import path
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError(
            "%s doesn't look like a module path" % dotted_path) from err
    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class' % (
                module_path, class_name)
        ) from err


class CitamSettings:
    _storage_driver = None
    _result_path = None
    _active_storage_driver_path = None
    _active_storage_driver_options = None

    def __init__(self):
        #: Access Key for s3 backend.
        self.access_key = os.environ.get('CITAM_STORAGE_KEY', '')
        #: Secret Key for s3 backend.
        self.secret_key = os.environ.get('CITAM_STORAGE_SECRET', '')
        #: Storage bucket for S3 backend
        self.storage_bucket = os.environ.get(
            'CITAM_STORAGE_BUCKET',
            'example',
        )
        #: Region Name for S3 backend
        self.region_name = os.environ.get('CITAM_STORAGE_REGION', '')
        #: Storage URL for S3 backend
        self.storage_url = os.environ.get(
            'CITAM_STORAGE_URL',
            'http://example.com',
        )
        #: Filesystem path for result files to use with LocalStorage backend
        self._result_path = os.environ.get('CITAM_RESULT_PATH', '')

        #: Path to storage driver class
        self.storage_driver_path = os.environ.get('CITAM_STORAGE_DRIVER')
        if not self.storage_driver_path:
            if self.result_path:
                self.storage_driver_path = 'citam.api.storage.local.LocalStorageDriver'  # noqa
            else:
                self.storage_driver_path = 'citam.api.storage.s3.S3StorageDriver'  # noqa

        #: Verbosity. Valid options: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        self.log_level = self._get_default_log_level()

        #: Storage driver instance
        self._storage_driver = self._initialize_storage_driver()

    @property
    def result_path(self) -> str:
        return self._result_path

    @result_path.setter
    def result_path(self, value: Union[str, None]):
        self._result_path = value
        # Update the storage driver if this changes
        if self._result_path:
            self.storage_driver_path = 'citam.api.storage.local.LocalStorageDriver'  # noqa
        else:
            self.storage_driver_path = 'citam.api.storage.s3.S3StorageDriver'  # noqa

    @property
    def storage_driver(self) -> BaseStorageDriver:
        cached_driver_conditions = (
            self._storage_driver,
            self._active_storage_driver_path == self.storage_driver_path,
            self._active_storage_driver_options == self._storage_kwargs,
        )

        if not all(cached_driver_conditions):
            self._storage_driver = self._initialize_storage_driver()

        return self._storage_driver

    def _initialize_storage_driver(self) -> BaseStorageDriver:
        """Get configured storage driver"""
        driver_class = _import_string(self.storage_driver_path)
        self._active_storage_driver_path = str(self.storage_driver_path)
        self._active_storage_driver_options = self._storage_kwargs

        assert issubclass(driver_class, BaseStorageDriver), (
            f"You are using a custom storage driver, but "
            f"{self._active_storage_driver_path} does not extend "
            f"BaseStorageDriver.  Extend BaseStorageDriver in your custom "
            f"storage driver."
        )

        return driver_class(**self._storage_kwargs)

    @staticmethod
    def _get_default_log_level() -> int:
        """Get application log level/verbosity.

        This can be set in the environment variable ``CITAM_LOG_LEVEL``.

        Default: WARNING
        """
        configured_level = os.environ.get('CITAM_LOG_LEVEL', 'WARNING').upper()
        configured_level.strip("'").strip('"')  # remove quotes from env
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARN': logging.WARNING,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        return level_map[configured_level]

    @property
    def _storage_kwargs(self):
        """Get keyword arguments to pass into the storage driver constructor"""
        return {
            'bucket': str(self.storage_bucket),
            'secret_key': str(self.secret_key),
            'region_name': str(self.region_name),
            'storage_url': str(self.storage_url),
            'access_key': str(self.access_key),
            'search_path': str(self.result_path),
        }


settings = CitamSettings()
