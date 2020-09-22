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
"""CITAM Global Test Fixtures

.. warning::
       This module is reserved for global auto-use fixtures. Only add fixtures
       to this file if they impact code or functionality affecting the
       majority of the codebase,

"""
import pytest

import citam


@pytest.fixture(autouse=True)
def reinitialize_settings(monkeypatch):
    """Before each command is run, reinitialize the citam settings"""
    monkeypatch.delenv('CITAM_RESULT_PATH', raising=False)
    monkeypatch.delenv('CITAM_STORAGE_KEY', raising=False)
    monkeypatch.delenv('CITAM_STORAGE_SECRET', raising=False)
    monkeypatch.delenv('CITAM_STORAGE_REGION', raising=False)
    monkeypatch.delenv('CITAM_RESULT_PATH', raising=False)
    monkeypatch.delenv('CITAM_STORAGE_DRIVER', raising=False)
    monkeypatch.delenv('CITAM_LOG_LEVEL', raising=False)
    citam.conf.settings.reset()
