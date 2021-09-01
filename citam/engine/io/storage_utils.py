# Copyright 2021. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================

import os
from typing import Union
import pathlib
from appdirs import user_data_dir


def get_user_cache() -> Union[str, pathlib.Path]:
    """
    Get the path to this user's OS cache directory. The cache directory is
    used to save facility and policy information.

    :return: path to the cache directory
    :rtype: Union[str, pathlib.Path]
    """
    citam_cache_directory = os.environ.get("CITAM_CACHE_DIRECTORY")
    if citam_cache_directory is None:
        citam_cache_directory = user_data_dir("CITAM")

    parent_dir = os.path.abspath(os.path.join(citam_cache_directory, ".."))
    if not os.path.isdir(parent_dir):
        os.mkdir(parent_dir)

    if not os.path.isdir(citam_cache_directory):
        os.mkdir(citam_cache_directory)

    return citam_cache_directory


def get_floorplans_directory() -> Union[str, pathlib.Path]:
    citam_cache_directory = get_user_cache()
    return os.path.join(citam_cache_directory, "floorplans_and_nav_data/")


def create_floor_datadir(
    facility_name: str, floor_name: str
) -> Union[str, pathlib.Path]:
    """
    Create a new directory in the user's cache to save data for a given
    facility and floor.

    :param facility_name: The name of the facility
    :type facility_name: str
    :param floor_name: The name of the floor.
    :type floor_name: str
    :return: The path of the newly created directory.
    :rtype: Union[str, pathlib.Path]
    """
    floorplan_directory = get_floorplans_directory()
    if not os.path.isdir(floorplan_directory):
        os.mkdir(floorplan_directory)

    facility_directory = os.path.join(floorplan_directory, facility_name + "/")
    if not os.path.isdir(facility_directory):
        os.mkdir(facility_directory)

    floor_directory = os.path.join(
        facility_directory, "floor_" + floor_name + "/"
    )
    if not os.path.isdir(floor_directory):
        os.mkdir(floor_directory)

    return floor_directory


def get_floor_datadir(
    facility_name: str, floor_name: str
) -> Union[str, pathlib.Path]:
    """
    Get the directory where data for a given facility and floor are saved.

    :param facility_name: The name of the facility.
    :type facility_name: str
    :param floor_name: The name of the floor.
    :type floor_name: str
    :return: path of the directory where data for this facility and floor are
            found.
    :rtype: Union[str, pathlib.Path]
    """
    """"""
    citam_cache_directory = get_user_cache()
    return os.path.join(
        citam_cache_directory,
        "floorplans_and_nav_data",
        facility_name,
        "floor_" + floor_name,
    )


def get_facility_datadir(facility_name: str) -> Union[str, pathlib.Path]:
    """
    Get the directory where data for a given facility are saved.

    :param facility_name: The name of the facility.
    :type facility_name: str
    :return: path of the directory where data for this facility and floor are
            found.
    :rtype: Union[str, pathlib.Path]
    """
    """"""
    citam_cache_directory = get_user_cache()
    return os.path.join(
        citam_cache_directory,
        "floorplans_and_nav_data",
        facility_name,
    )