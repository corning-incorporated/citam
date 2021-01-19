# Copyright 2020. Corning Incorporated. All rights reserved.
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


import numpy as np
import logging
import progressbar as pb
from typing import List, Dict, Any

from citam.engine.constants import DEFAULT_MEETINGS_POLICY
from citam.engine.map.space import Space

LOG = logging.getLogger(__name__)


class Meeting:
    """
    Class to manage meeting instances.
    """

    def __init__(
        self,
        location: Space,
        floor_number: int,
        start_time: int,
        end_time: int,
        attendees: List[int] = None,
    ) -> None:
        """
        Initialize a new meeting object.

        :param location: The location of the meeting
        :type location: Space
        :param floor_number: index of the floor where this meeting takes place.
        :type floor_number: int
        :param start_time: Start time of the meeting.
        :type start_time: int
        :param end_time: End time of the meeting.
        :type end_time: int
        :param attendees: List of agents attending this meeting,
            defaults to None
        :type attendees: List[int], optional
        """
        self.location = location
        self.floor_number = floor_number
        if attendees is None:
            self.attendees = []  # ID of all the participants
        else:
            self.attendees = attendees
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self) -> str:
        """
        Generate a string representation of this meeting.

        :return: The string representing this meeting
        :rtype: str
        """
        str_repr = "Meeting Details: \n"
        str_repr += ">>>>>> attendees :" + str(self.attendees) + "\n"
        str_repr += ">>>>>> start time :" + str(self.start_time) + "\n"
        str_repr += ">>>>>> end time :" + str(self.end_time) + "\n"
        str_repr += ">>>>>> location :" + str(self.location.unique_name) + "\n"
        str_repr += ">>>>>> floor_number :" + str(self.floor_number) + "\n"

        return str_repr

    def __eq__(self, other) -> bool:
        return (
            self.location == other.location
            and self.floor_number == other.floor_number
            and self.attendees == other.attendees
            and self.start_time == other.start_time
            and self.end_time == other.end_time
        )


class MeetingPolicy:
    """
    Class to implement a meeting policy defining all the meetings that take
    place in a facility based on predefined parameters.
    """

    def __init__(
        self,
        meeting_rooms: List[List[Space]],
        agent_ids: List[int],
        daylength: int,
        policy_params: Dict[str, Any] = None,
    ) -> None:
        """
        Initialize a new meeting policy object.

        :param meeting_rooms: The list of meeting rooms available.
        :type meeting_rooms: List[List[Space]]
        :param agent_ids: List of agent ids to create meetings for.
        :type agent_ids: List[int]
        :param daylength: The total time window within which meetings are to be
            created.
        :type daylength: int
        :param policy_params: Parameters used to decide how to create the
            meetings, defaults to None
        :type policy_params: Dict[str, Any], optional
        """
        self.meetings: List[Meeting] = []
        self.daylength = daylength

        # Attendee pool
        self.attendee_pool = {agent_id: 0 for agent_id in agent_ids}

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
        self.percent_meeting_rooms_used = policy_params[
            "percent_meeting_rooms_used"
        ]

        # Meetings participants
        self.avg_meetings_per_person = policy_params["avg_meetings_per_person"]
        self.min_attendees_per_meeting = policy_params[
            "min_attendees_per_meeting"
        ]

        # Timing between meetings
        self.min_buffer_between_meetings = policy_params[
            "min_buffer_between_meetings"
        ]
        self.max_buffer_between_meetings = policy_params[
            "max_buffer_between_meetings"
        ]

        self.total_time_blocks = int(
            self.max_meeting_length / self.meeting_duration_increment
        )

        self.meeting_rooms: List[List[Space]] = []
        for floor in meeting_rooms:
            self.meeting_rooms.append([])
            for room in floor:
                if (
                    room.capacity
                    and room.capacity >= self.min_attendees_per_meeting
                ):
                    self.meeting_rooms[-1].append(room)

        n_meeting_rooms = sum(len(rooms) for rooms in self.meeting_rooms)
        LOG.info(
            "Valid meeting rooms for this policy: " + str(n_meeting_rooms)
        )

    def _create_meetings_for_room(
        self, meeting_room: Space, floor_number: int
    ) -> None:
        """
        Create all meetings to take place in this specific room.

        :param meeting_room: The meeting room of interest.
        :type meeting_room: Space
        :param floor_number: Index of the floor of this meeting room.
        :type floor_number: int
        """

        n_meetings = round(np.random.normal(self.avg_meetings_per_room))

        # TODO: Create first and last meeting then add extra meetings
        # to avoid all meetings happening in the morning

        last_meeting_end_time = 0
        for i in range(n_meetings):

            if last_meeting_end_time >= self.daylength:
                break

            # Start next meeting within min and max buffer time
            start_time = last_meeting_end_time + np.random.randint(
                self.min_buffer_between_meetings,
                self.max_buffer_between_meetings,
            )
            # Randomly set the duration
            n_blocks = np.random.randint(self.total_time_blocks)
            duration = self.min_meeting_duration
            duration += n_blocks * self.meeting_duration_increment

            # Set end time
            end_time = start_time + duration
            if end_time > self.daylength:
                end_time = self.daylength

            attendees = self._generate_meeting_attendee_list(
                meeting_room, start_time, end_time
            )

            if len(attendees) > 1:
                for attendee in attendees:
                    self.attendee_pool[attendee] += 1

                # Create new meeting
                self.meetings.append(
                    Meeting(
                        location=meeting_room,
                        floor_number=floor_number,
                        start_time=start_time,
                        end_time=end_time,
                        attendees=attendees,
                    )
                )

                last_meeting_end_time = end_time
                self._update_attendee_pool()

            if len(self.attendee_pool) == 0:
                break

    def _generate_meeting_attendee_list(
        self, meeting_room: Space, start_time: int, end_time: int
    ) -> List[int]:
        """
        Randomly add attendees to a meeting time slot based on agents'
        availability.

        :param meeting_room: The meeting room
        :type meeting_room: Space
        :param start_time: When the meeting starts
        :type start_time: int
        :param end_time: When the meeting ends.
        :type end_time: int
        :return: The list of selected agents (given by their ids).
        :rtype: List[int]
        """
        pot_attendees = self._find_potential_attendees(start_time, end_time)
        if not pot_attendees:
            return []

        attendees = []
        n_attendees = meeting_room.capacity
        if self.min_attendees_per_meeting < meeting_room.capacity:
            n_attendees = np.random.randint(
                self.min_attendees_per_meeting, meeting_room.capacity
            )

        if n_attendees >= len(pot_attendees):
            # We need more attendees than currently available
            attendees = pot_attendees
        elif n_attendees > 1:
            attendees = list(
                np.random.choice(pot_attendees, n_attendees, replace=False)
            )

        return attendees

    def create_all_meetings(self) -> None:
        """
        Create meetings for this facility with no conflicts (room nor agent)
        """

        n_meeting_rooms = sum(len(rooms) for rooms in self.meeting_rooms)
        if n_meeting_rooms == 0:
            LOG.warning("No valid meeting room found")
            return

        # Randomly select rooms
        available_rooms = [
            f"{floor_number}-{i}"
            for floor_number, floor_rooms in enumerate(self.meeting_rooms)
            for i in range(len(floor_rooms))
        ]

        n_rooms = int(self.percent_meeting_rooms_used * len(available_rooms))
        rooms = np.random.choice(available_rooms, n_rooms, replace=False)

        print("Creating meetings...")
        for roomkey in pb.progressbar(rooms):
            fn, i = roomkey.split("-")
            room = self.meeting_rooms[int(fn)][int(i)]
            self._create_meetings_for_room(room, int(fn))

    def _find_potential_attendees(
        self, start_time: int, end_time: int
    ) -> List[int]:
        """
        Find all individuals in attendee pool who are free between start and
        end time to be later added to a meeting within that time period.

        :param start_time: Start time of the meeting.
        :type start_time: int
        :param end_time: End time of the meeting.
        :type end_time: int
        :return: List of potential attendees
        :rtype: List[int]
        """
        # Find if there is another meeting at that same time
        pot_attendees = [k for k in self.attendee_pool]  # copy of the list
        for meeting in self.meetings:
            if start_time < meeting.end_time and end_time > meeting.start_time:
                # this is an overlap, attendees are not available
                for a in meeting.attendees:
                    if a in pot_attendees:
                        pot_attendees.remove(a)

        return pot_attendees

    def _update_attendee_pool(self) -> None:
        """
        Update the attendee pool to ensure the average
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

    def get_daily_meetings(self, agent_id: int) -> List[Meeting]:
        """
        Returns the list of meetings for a given agent.

        :param agent_id: Id of the agent of interest.
        :type agent_id: int
        :return: The list of meetings for this agent.
        :rtype: List[Meeting]
        """
        return [
            meeting
            for meeting in self.meetings
            if agent_id in meeting.attendees
        ]
