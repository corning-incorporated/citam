#  Copyright 2021. Corning Incorporated. All rights reserved.
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

import os
import pytest
from citam.conf import settings


@pytest.fixture()
def use_local_storage():
    """Configure CITAM dash to use the test sample_results directory"""
    search_root = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sample_results",
    )
    settings.storage_driver_path = "citam.api.storage.local.LocalStorageDriver"
    settings.result_path = search_root
