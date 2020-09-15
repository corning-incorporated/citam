# Copyright 2020. Corning Incorporated. All rights reserved.
#
# This software may only be used in accordance with the licenses granted by
# Corning Incorporated. All other uses as well as any copying, modification or
# reverse engineering of the software is strictly prohibited.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================

import os
from appdirs import *

def get_user_cache():
    """Returns the user cache directory for citam
    """
    citam_cache_directory = os.environ.get('CITAM_CACHE_DIRECTORY')
    if citam_cache_directory is None:
        citam_cache_directory = user_data_dir('CITAM')

    parent_dir = os.path.abspath(os.path.join(citam_cache_directory, '..'))
    if not os.path.isdir(parent_dir):
        os.mkdir(parent_dir)

    if not os.path.isdir(citam_cache_directory):
        os.mkdir(citam_cache_directory)

    return citam_cache_directory


def get_floorplans_directory():
    citam_cache_directory = get_user_cache()
    floorplan_directory = os.path.join(citam_cache_directory,
                                       'floorplans_and_nav_data/'
                                       )
    return floorplan_directory


def create_datadir(facility_name, floor_name):
    """Create directory to save data for a given facility and floor.
    """
    floorplan_directory = get_floorplans_directory()
    if not os.path.isdir(floorplan_directory):
        os.mkdir(floorplan_directory)

    facility_directory = os.path.join(floorplan_directory, facility_name + '/')
    if not os.path.isdir(facility_directory):
        os.mkdir(facility_directory)

    floor_directory = os.path.join(facility_directory,
                                   'floor_' + floor_name + '/'
                                   )
    if not os.path.isdir(floor_directory):
        os.mkdir(floor_directory)

    return floor_directory


def get_datadir(facility_name, floor_name):
    """Get the directory where data for a given facility and floor are saved.
    """
    citam_cache_directory = get_user_cache()
    floorplan_directory = os.path.join(citam_cache_directory,
                                       'floorplans_and_nav_data/'
                                       )
    facility_directory = os.path.join(floorplan_directory, facility_name + '/')
    floor_directory = os.path.join(facility_directory,
                                   'floor_' + floor_name + '/'
                                   )

    return floor_directory
