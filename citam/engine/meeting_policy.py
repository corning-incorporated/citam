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


import numpy as np
import logging
import progressbar as pb
from typing import List

from citam.engine.constants import DEFAULT_MEETINGS_POLICY

LOG = logging.getLogger(__name__)


class Meeting:
    def __init__(self, location, start_time, end_time):
        super().__init__()
        self.location = location
        self.attendees = []  # ID of all the participants
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        str_repr = "Meeting Details: \n"
        str_repr += ">>>>>> attendees :" + str(self.attendees) + "\n"
        str_repr += ">>>>>> start time :" + str(self.start_time) + "\n"
        str_repr += ">>>>>> end time :" + str(self.end_time) + "\n"
        str_repr += ">>>>>> location :" + str(self.location) + "\n"

        return str_repr


class MeetingPolicy:
    def __init__(
        self,
        meeting_rooms: List[List[int]],
        agent_ids: List[int],
        policy_params=None,
    ):
        super().__init__()

        self.meeting_rooms = meeting_rooms
        self.agent_ids = agent_ids
        self.meetings = []

        # Attendee pool
        self.attendee_pool = {}
        for agent_id in self.agent_ids:
            self.attendee_pool[agent_id] = 0

        if policy_params is None:
            policy_params = DEFAULT_MEETINGS_POLICY

        # Meetings duration
        self.min_meeting_duration = policy_params["min_meeting_duration"]
        self.max_meeting_length = policy_params["max_meeting_length"]
        self.meeting_duration_increment = policy_params[
            "meeting_duration_increment"
        ]

        # Meetings frequency
        self.avg_meetings_per_room = policy_params["avg_meetings_per_room"]
        self.avg_percent_meeting_rooms_used = policy_params[
            "avg_percent_meeting_rooms_used"
        ]

        # Meetings participants
        self.avg_meetings_per_person = policy_params["avg_meetings_per_person"]
        self.min_attendees_per_meeting = policy_params[
            "min_attendees_per_meeting"
        ]

        # Timing between meetings
        self.min_buffer_between_meetings = \
            policy_params["min_buffer_between_meetings"]
        self.max_buffer_between_meetings = \
            policy_params["max_buffer_between_meetings"]

        n_meeting_rooms = sum(len(rooms) for rooms in self.meeting_rooms)
        LOG.info("Meeting rooms in policy: " + str(n_meeting_rooms))

        return

    def create_meetings(self):
        """Create meetings with no conflicts (room nor agent)"""

        tot_blocks = int(
            self.max_meeting_length / self.meeting_duration_increment
        )

        # Create the meetings
        print("Creating meetings...")
        for floor_rooms in self.meeting_rooms:
            if len(self.attendee_pool) == 0:
                break
            for meeting_room in pb.progressbar(floor_rooms):

                # Maybe sample from a gaussian distribution instead ???
                random_number = np.random.rand()
                if random_number > self.avg_percent_meeting_rooms_used:
                    continue

                n_meetings = np.random.normal(self.avg_meetings_per_room)
                n_meetings = int(round(n_meetings))

                # TODO: Create first and last meeting then add extra meetings
                # to avoid all meetings happening in the morning

                last_meeting_end_time = 0
                for i in range(n_meetings):
                    # Start next meeting within buffer time of last meeting ending
                    start_time = last_meeting_end_time + np.random.randint(
                                    self.min_buffer_between_meetings,
                                    self.max_buffer_between_meetings
                                )
                    # Randomly set the duration
                    n_blocks = np.random.randint(tot_blocks)
                    duration = self.min_meeting_duration
                    duration += n_blocks * self.meeting_duration_increment
                    # Set end time
                    end_time = start_time + duration
                    # Create new meeting
                    new_meeting = Meeting(
                        location=meeting_room,
                        start_time=start_time,
                        end_time=end_time,
                    )

                    # Add participants,
                    # TODO: get capacity from meeting room obj
                    capacity = 25
                    n_attendees = np.random.randint(
                        self.min_attendees_per_meeting, capacity
                    )

                    pot_attendees = self._find_potential_attendees(
                                        start_time,
                                        end_time
                                    )
                    print("Pot attendees: ", pot_attendees, n_attendees)
                    if pot_attendees:

                        if n_attendees >= len(pot_attendees):
                            attendees = pot_attendees
                        else:
                            attendees = np.random.choice(
                                pot_attendees, n_attendees, replace=False
                            )

                        for attendee in attendees:
                            self.attendee_pool[attendee] += 1

                        new_meeting.attendees = attendees
                        self.meetings.append(new_meeting)
                        last_meeting_end_time = end_time
                        self._update_attendee_pool()

                    if len(self.attendee_pool) == 0:
                        break
        return

    def _find_potential_attendees(
        self,
        start_time: int,
        end_time: int
    ) -> List[int]:
        """
        Find all individuals in attendee pool who are free between start and
        end time.
        """

        # Find if there is another meeting at that same time
        pot_attendees = [k for k in self.attendee_pool]   # copy of the list
        for meeting in self.meetings:
            if start_time < meeting.end_time and end_time > meeting.start_time:
                # this is an overlap, attendees are not available
                for a in meeting.attendees:
                    if a in pot_attendees:
                        pot_attendees.remove(a)

        return pot_attendees

    def _update_attendee_pool(self):
        """Update the attendee pool to ensure the average
        number of meetings per agent is not exceeded
        """
        # if the avg is greater than desired, remove the attendee with the most
        # meetings from the attendee pool

        current_avg = np.average([int(v) for v in self.attendee_pool.values()])

        while current_avg > self.avg_meetings_per_person:
            max_meetings = max(self.attendee_pool.values())
            self.attendee_pool = {
                key: val
                for key, val in self.attendee_pool.items()
                if val < max_meetings
            }

            if not self.attendee_pool:
                break

            values = [int(v) for v in self.attendee_pool.values()]
            current_avg = np.average(values)
        return

    def get_daily_meetings(self, agent_id: int):
        """Returns list of meetings for this agent"""

        return [
            meeting
            for meeting in self.meetings
            if agent_id in meeting.attendees
        ]
