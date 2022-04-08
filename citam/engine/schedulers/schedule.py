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
from __future__ import annotations
from abc import ABC, abstractmethod


class ScheduleItem:
    def __init__(self, purpose, location, floor_number, duration):
        self.purpose = purpose
        self.location = location
        self.floor_number = floor_number
        self.duration = duration


class Schedule(ABC):
    def __init__(
        self,
        timestep: int,
        start_time: int,
        end_time: int,
    ) -> None:
        super().__init__()
        self.timestep = timestep
        self.start_time = start_time
        self.end_time = end_time

    @abstractmethod
    def build(self):
        pass
