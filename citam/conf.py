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
from copy import deepcopy
from importlib import import_module
from typing import Any, Union

from citam.api.storage import BaseStorageDriver

LOG = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """This error is raised when the running CITAM configuration is invalid"""

    def __init__(self, error_list):
        error_str = '\n'.join(error_list)
        super().__init__(error_str)


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
    #: Internal variable for the currently initialized storage driver object
    _storage_driver = None

    #: Internal variable for the result_path property
    _result_path = None

    #: Internal variable for the storage_driver path related to the currently
    #: initialized storage driver object
    _active_storage_driver_path = None

    #: Internal tracking for validation problems
    _active_storage_driver_options = None

    #: Internal tracking for validation problems
    _validation_errors = {}

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
            self.storage_driver_path = 'citam.api.storage.local.LocalStorageDriver'  # noqa

        #: Verbosity. Valid options: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        self.log_level = self._get_default_log_level()

        #: Storage driver instance
        self._storage_driver = self._initialize_storage_driver()

    @property
    def result_path(self) -> str:
        if not self._result_path:
            self._result_path = os.environ.get('CITAM_RESULT_PATH')
        return self._result_path

    @result_path.setter
    def result_path(self, value: Union[str, None]):
        if not value:
            return

        self._result_path = value
        self.storage_driver_path = 'citam.api.storage.local.LocalStorageDriver'

        if not os.path.exists(self._result_path):
            self._validation_errors['result_path'] = \
                f"{self._result_path} does not exist"

        elif not os.path.isdir(self._result_path):
            self._validation_errors['result_path'] = \
                f"{self._result_path} is not a valid directory"

        else:
            if self._validation_errors.get('result_path'):
                self._validation_errors['result_path'] = False

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

    def validate(self):
        """Validate the current configuration object

        :raise ConfigurationError: If the configuration is invalid
        """
        print("VALIDATING", flush=True)
        # Re-initialize the storage driver if needed
        assert self.storage_driver

        if any(self._validation_errors.values()):
            raise ConfigurationError(
                [x for x in self._validation_errors.values() if x]
            )

        LOG.debug("Using results directory: %s", self._result_path)

    def _initialize_storage_driver(self) -> Union[BaseStorageDriver, None]:
        """Get configured storage driver"""
        driver_class = _import_string(self.storage_driver_path)
        self._active_storage_driver_path = str(self.storage_driver_path)
        self._active_storage_driver_options = deepcopy(self._storage_kwargs)

        assert issubclass(driver_class, BaseStorageDriver), (
            f"You are using a custom storage driver, but "
            f"{self._active_storage_driver_path} does not extend "
            f"BaseStorageDriver.  Extend BaseStorageDriver in your custom "
            f"storage driver."
        )
        try:
            driver = driver_class(**self._storage_kwargs)
            # Remove any flags
            if self._validation_errors.get('storage_driver'):
                self._validation_errors['storage_driver'] = False
        except OSError as err:
            LOG.info(
                "Error initializing driver_class, this will happen in "
                "normal operation when settings are specified on the CLI",
                exc_info=err,
            )
            driver = None
            self._validation_errors['storage_driver'] = str(err)
        return driver

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
