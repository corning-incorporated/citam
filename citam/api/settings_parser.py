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
__all__ = [
    'get_storage_driver',
    'get_access_key',
    'get_secret_key',
    'get_storage_bucket',
    'get_region_name',
    'get_storage_url',
    'get_local_result_path',
    'get_log_level',
]

import logging
import os
from importlib import import_module


def _import_string(dotted_path):
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


def get_storage_driver():
    """Get configured storage driver

    This is defined by the environment variable ``CITAM_STORAGE_DRIVER``

    :rtype: citam.storage.BaseStorageDriver
    """
    if get_local_result_path():
        driver_path = 'citam.api.storage.local.LocalStorageDriver'
    else:
        driver_path = os.environ.get(
            'CITAM_STORAGE_DRIVER',
            'citam.api.storage.s3.S3StorageDriver',
        )
    driver_class = _import_string(driver_path)
    return driver_class(**_get_storage_driver_kwargs())


def get_access_key():
    """Get access key for object storage backend.

    This is only used if using the S3Storage driver

    This can be set in the environment variable ``CITAM_STORAGE_KEY``
    """
    return os.environ.get('CITAM_STORAGE_KEY')


def get_secret_key():
    """Get secret key for object storage backend.

    This is only used if using the S3Storage driver

    This can be set in the environment variable ``CITAM_STORAGE_SECRET``
    """
    return os.environ.get('CITAM_STORAGE_SECRET')


def get_storage_bucket():
    """Get bucket to use for object storage backend.

    This is only used if using the S3Storage driver

    This can be set in the environment variable ``CITAM_STORAGE_BUCKET``
    """
    return os.environ.get('CITAM_STORAGE_BUCKET')


def get_region_name():
    """Get region name for the object storage backend.

    This is only used if using the S3Storage driver

    This can be set in the environment variable ``CITAM_STORAGE_REGION``
    """
    return os.environ.get('CITAM_STORAGE_REGION')


def get_storage_url():
    """Get url for the object storage backend.

    This is only used if using the S3Storage driver

    This can be set in the environment variable ``CITAM_STORAGE_URL``
    """
    return os.environ.get('CITAM_STORAGE_URL', )


def get_local_result_path():
    """Get filesystem path where results are stored

    This is only used if using the LocalStorage driver

    This can be set in the environment variable ``CITAM_RESULT_PATH``
    """
    return os.environ.get('CITAM_RESULT_PATH')


def get_log_level():
    """Get application log level/verbosity.

    This can be set in the environment variable ``CITAM_LOG_LEVEL``.

    Default: WARNING

    Options are: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    configured_level = os.environ.get('CITAM_LOG_LEVEL', 'WARNING').upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARN': logging.WARNING,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return level_map[configured_level]


def _get_storage_driver_kwargs():
    """Get keyword arguments to pass into the storage driver constructor"""
    return {
        'bucket': get_storage_bucket(),
        'secret_key': get_secret_key(),
        'region_name': get_region_name(),
        'storage_url': get_storage_url(),
        'access_key': get_access_key(),
        'search_path': get_local_result_path(),
    }
