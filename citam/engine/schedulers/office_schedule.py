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


import logging
from typing import Tuple, List, Dict, Any, Optional
import numpy as np

from citam.engine.constants import (
    CAFETERIA_VISIT,
    LAB_WORK,
    OFFICE_WORK,
    RESTROOM_VISIT,
    MEETING,
    MEETING_BUFFER,
)
from citam.engine.map.door import Door
from citam.engine.schedulers.schedule import Schedule, ScheduleItem
from citam.engine.schedulers.meetings import Meeting
from citam.engine.facility.navigation import Navigation


LOG = logging.getLogger(__name__)


class OfficeSchedule(Schedule):
    """
    Create and manage a schedule associated with one agent. Schedules
    are created based on rules encoded in a scheduling policy and include a
    full itinerary.
    """

    def __init__(
        self,
        timestep: int,
        start_time: int,
        exit_time: int,
        entrance_door: Door,
        entrance_floor: int,
        exit_door: Door,
        exit_floor: int,
        office_location: int,
        office_floor: int,
        navigation: Navigation,
        scheduling_rules: Dict[str, Any],
        meetings: List[Meeting] = None,
    ):
        """
        Initialize a new schedule object.

        :param timestep: The timestep determining the time resolution of the
                schedule.
        :type timestep: int
        :param start_time: The start time of this schedule.
        :type start_time: int
        :param exit_time: When this agent exits the facility
        :type exit_time: int
        :param entrance_door: The door to use as entrance.
        :type entrance_door: Door
        :param entrance_floor: index of the entrance floor.
        :type entrance_floor: int
        :param exit_door: The door to use as exit.
        :type exit_door: Door
        :param exit_floor: Index of the exit floor.
        :type exit_floor: int
        :param office_location: Index of this agent's office space.
        :type office_location: int
        :param office_floor: Index of this agent's office floor.
        :type office_floor: int
        :param navigation: The navigation object for this facility.
        :type navigation: Navigation
        :param scheduling_rules: The rules to use to create schedule items.
        :type scheduling_rules: Dict[str, Any]
        :param meetings: List of in-person meetings this agent has to attend,
             defaults to None
        :type meetings: List[Meeting], optional
        """
        super().__init__(timestep, start_time, exit_time)

        self.exit_time = exit_time
        self.entrance_door = entrance_door
        self.entrance_floor = entrance_floor
        self.exit_door = exit_door
        self.exit_floor = exit_floor
        self.daylength = exit_time - start_time
        self.meetings = meetings if meetings else []
        self.next_meeting_index = 0

        self.meetings.sort(key=lambda meeting: meeting.start_time)

        self.scheduling_rules = scheduling_rules

        self.office_location = office_location
        self.office_floor = office_floor
        self.navigation = navigation

        self.current_standing = 0

        self.itinerary: List[Tuple[Any, ...]] = [
            (None, None) for _ in range(start_time - 2)
        ]
        self.schedule_items: List[ScheduleItem] = []

        (
            self.meeting_rooms,
            self.labs,
            self.cafes,
            self.restrooms,
            self.offices,
        ) = (
            [],
            [],
            [],
            [],
            [],
        )  # List of lists of space indices

        for fp in self.navigation.floorplans:
            (
                floor_offices,
                floor_labs,
                floor_cafes,
                floor_restrooms,
                floor_meeting_rooms,
            ) = ([], [], [], [], [])

            for index, space in enumerate(fp.spaces):

                if space.is_space_an_office():
                    floor_offices.append(index)

                elif space.is_space_a_lab():
                    floor_labs.append(index)

                elif space.is_space_a_cafeteria():
                    floor_cafes.append(index)

                elif space.is_space_a_restroom():
                    floor_restrooms.append(index)

                elif space.is_space_a_meeting_room():
                    floor_meeting_rooms.append(index)

            self.offices.append(floor_offices)
            self.labs.append(floor_labs)
            self.cafes.append(floor_cafes)
            self.restrooms.append(floor_restrooms)
            self.meeting_rooms.append(floor_meeting_rooms)

        self.possible_purposes = self.find_possible_purposes()
        self.shortest_purpose_duration = min(
            [
                self.scheduling_rules[purp]["min_duration"]
                for purp in self.possible_purposes
                if purp != RESTROOM_VISIT
            ]
        )

    def build_schedule_item(
        self, purpose: str, next_meeting_start_time: Optional[int]
    ) -> ScheduleItem:
        """
        Given a purpose and additional properties such as meeting duration,
        build a schedule item for this agent.

        :param purpose: The purpose for this schedule item.
        :type purpose: str
        :param next_meeting_start_time: Start of any upcoming meeting. None if
            there is no upcoming meeting.
        :type next_meeting_start_time: int
        :raises ValueError: If no suitable location is found for this purpose.
        :return: The newly created schedule item.
        :rtype: ScheduleItem
        """

        # Choose a duration
        max_duration = self.get_max_duration_for_purpose(
            purpose, next_meeting_start_time
        )

        if max_duration < self.scheduling_rules[purpose]["min_duration"]:
            raise ValueError("Not enough time is available for this meeting.")

        duration = np.random.randint(
            self.scheduling_rules[purpose]["min_duration"], max_duration
        )

        # Choose a location
        if purpose == OFFICE_WORK:
            location = self.office_location
            floor_number = self.office_floor
        else:
            possible_locations = []
            if purpose == RESTROOM_VISIT:
                # TODO: Choose closest restroom
                possible_locations = self.restrooms
            elif purpose == LAB_WORK:
                possible_locations = self.labs
            elif purpose == CAFETERIA_VISIT:
                possible_locations = self.cafes

            total_locations = sum([len(pl) for pl in possible_locations])
            if total_locations == 0:
                raise ValueError("total locations must be > 0")

            floor_number = np.random.randint(len(self.navigation.floorplans))
            location = np.random.choice(possible_locations[floor_number])

        # Setup schedule item
        schedule_item = ScheduleItem(
            purpose=purpose,
            location=location,
            floor_number=floor_number,
            duration=duration,
        )
        return schedule_item

    def find_next_schedule_item(self) -> ScheduleItem:
        """
        Check if a meeting is happening within MEETING_BUFFER time. If so,
        return the meeting as the next schedule item, otherwise, build a new
        item that must ned before the next meeting time for this agent.

        ..Note:: MEETING BUFFER is a constant specified in settings.

        :return: The next schedule item.
        :rtype: ScheduleItem
        """

        next_meeting_start_time = None
        # Handle meetings first
        if len(self.meetings) > 0:
            next_meeting = self.meetings[self.next_meeting_index]
            next_meeting_start_time = next_meeting.start_time
            # Check if meeting is happening within 15 timestep of now, if so
            if next_meeting.start_time - len(self.itinerary) <= MEETING_BUFFER:
                schedule_item = ScheduleItem(
                    purpose=MEETING,
                    duration=next_meeting.end_time - next_meeting.start_time,
                    location=next_meeting.location,
                    floor_number=next_meeting.floor_number,
                )
                self.next_meeting_index += 1
                return schedule_item

        if len(self.schedule_items) == 0:  # First item for the day

            schedule_item = self.build_schedule_item(
                OFFICE_WORK,
                next_meeting_start_time,
            )
            return schedule_item

        # If no upcoming meeting and agent is already in facility, let's pick
        # a purpose using the scheduling policy
        purpose = self.choose_valid_scheduling_purpose(next_meeting_start_time)
        schedule_item = self.build_schedule_item(
            purpose, next_meeting_start_time
        )

        return schedule_item

    def find_possible_purposes(self) -> List[str]:
        """
        Feturn list of possible purposes for this agent in this facility.

        Iterate over purposes defined in scheduling rules and compare with
        purposes specified for the different locations in this facility. The
        possible purposes are the ones for which at least one location is
        available.

        ..Note:: Possible purposes are not checked for validity based on
        scheduling rules.

        :return: list of possible purposes.
        :rtype: List[str]
        """

        # TODO: add more complex rules based on employee details
        # (e.g. no office work or no lab work).

        # Only keep purposes that have corresponding rooms in this facility
        possible_purposes = [OFFICE_WORK]

        # TODO: Associate each purpose with a room type at the model level
        locations_for_purpose = {
            RESTROOM_VISIT: self.restrooms,
            LAB_WORK: self.labs,
            CAFETERIA_VISIT: self.cafes,
        }

        for purpose in self.scheduling_rules:
            if purpose in locations_for_purpose:
                possible_locations = locations_for_purpose[purpose]
                total_locations = sum(len(pl) for pl in possible_locations)
                if total_locations > 0:
                    possible_purposes.append(purpose)

        return possible_purposes

    def get_max_duration_for_purpose(
        self, purpose: str, next_meeting_start_time: Optional[int]
    ) -> int:
        """
        Calculate the maximum duration possible for a given scheduling purpose
        while taking into account any upcoming meeting after this schedule
        item.

        :param purpose: The purpose of the next meeting.
        :type purpose: str
        :param next_meeting_start_time: Start time of the next meeting.
        :type next_meeting_start_time: int
        :return: The maximum duration.
        :rtype: int
        """
        remaining_daylength = self.daylength - len(self.itinerary)
        details = self.scheduling_rules[purpose]
        max_duration = min([details["max_duration"], remaining_daylength])
        if next_meeting_start_time is not None:
            max_end_time = next_meeting_start_time - MEETING_BUFFER
            if len(self.itinerary) + max_duration > max_end_time:
                max_duration = max_end_time - len(self.itinerary)

        return max_duration

    def count_purpose_occurence_in_schedule_items(self) -> List[int]:
        """
        Iterate over schedule items and count how many items each scheduling
        purpose exists.

        :return: List of counts, one per possible purpose.
        :rtype: int
        """
        n_items = [0 for _ in self.possible_purposes]
        for employee_item in self.schedule_items:
            # Current items already in this employee's schedule
            for i, purpose in enumerate(self.possible_purposes):
                if purpose == employee_item.purpose:
                    n_items[i] += 1
                    break
        return n_items

    def get_valid_purposes_from_possible_purposes(
        self, next_meeting_start_time: Optional[int]
    ) -> List[str]:
        """
        Iterate through list of purposes under consideration, remove any that
        doesn't satisfy exisiting scheduling rules.

        :param next_meeting_start_time: Start time of any upcoming meeting.
        :type next_meeting_start_time: int
        :return: List of valid purposes
        :rtype: List[str]
        """
        valid_purposes = []

        # TODO: refactor this function to add to valid purpose only after all
        # the tests have passed
        # Count how many items of each type is already in the schedule
        n_items = self.count_purpose_occurence_in_schedule_items()
        # Don't consider schedule item that already reached their max instances
        for i, purpose in enumerate(self.possible_purposes):
            item_details = self.scheduling_rules[purpose]
            if n_items[i] < item_details["max_instances"]:
                # Check if we have enough time left for this purpose
                max_duration = self.get_max_duration_for_purpose(
                    purpose, next_meeting_start_time
                )
                if max_duration >= item_details["min_duration"]:
                    valid_purposes.append(purpose)

        # No consecutive restroom visits #TODO: Add this to scheduling rules
        if (
            RESTROOM_VISIT in valid_purposes
            and self.schedule_items
            and self.schedule_items[-1].purpose == RESTROOM_VISIT
        ):
            valid_purposes.remove(RESTROOM_VISIT)

        # Cafeteria visits only happen around the middle of the work day
        # TODO: Add this to scheduling rules
        if CAFETERIA_VISIT in valid_purposes and (
            len(self.itinerary) < round(self.daylength / 3.0)
            or len(self.itinerary) > round(2 * self.daylength / 3.0)
        ):
            valid_purposes.remove(CAFETERIA_VISIT)
        return valid_purposes

    def choose_valid_scheduling_purpose(
        self, next_meeting_start_time: Optional[int]
    ) -> str:
        """
        Find a valid scheduling purpose using rules defined in the
        scheduling policy for this facility. Common purposes include:
        restroom visits, lab work, office work and cafeteria visit.

        :param next_meeting_start_time: Start time of the next meeting
        :type next_meeting_start_time: Optional[int]
        :raises ValueError: If not valid purpose is found.
        :return: A randomly chosen purpose from list of valid purposes.
        :rtype: str
        """

        valid_purposes = self.get_valid_purposes_from_possible_purposes(
            next_meeting_start_time
        )

        # Randomly choose a purpose from list of valid purposes
        if valid_purposes:
            return np.random.choice(valid_purposes)
        else:
            raise ValueError("At least one valid purpose needed.")

    def get_pace(self, scale: float) -> float:
        """
        Randomly pick a walking pace for this agent by sampling from a
        gaussian distribution around a pace of 4 ft/sec. The acceptable
        range is set between 2 and 6 ft/sec.

        :param scale: the scale of the floorplan in [ft]/[drawing unit].
        :type scale: float
        :return: the agent's pace in [drawing unit]/[timestep]
        :rtype: float
        """
        # typical walking pace: 4 ft/sec; Range : 2 to 6 ft/sec
        pace = 0.0
        while pace < 2.0 or pace > 6.0:
            pace = np.random.normal(loc=4)
        pace *= self.timestep
        pace /= scale

        return pace

    def update_schedule_items(self, new_item: ScheduleItem) -> None:
        """
        Update list of schedule items by adding this new item. If previous item
        is the same location and purpose as this new one, merge them.

        :param new_item: The new schedule item to add to the list.
        :type new_item: ScheduleItem
        """
        # update list of schedule items
        if len(self.schedule_items) > 0:
            last_item = self.schedule_items[-1]
            if (
                last_item.purpose == new_item.purpose
                and last_item.location == new_item.location
                and last_item.floor_number == new_item.floor_number
            ):
                # If this purpose and location are the same as the last
                # one, just update the last one
                self.schedule_items[-1].duration += new_item.duration
            else:
                self.schedule_items.append(new_item)
        else:
            self.schedule_items.append(new_item)

    def update_itinerary(
        self, route: List[Tuple[Any, ...]], schedule_item: ScheduleItem
    ) -> None:
        """
        Given a route and a next schedule item, update this agent's itinerary
        accordingly
        """
        next_location = schedule_item.location
        next_floor_number = schedule_item.floor_number

        if not route:
            raise ValueError("Route cannot be 'None'")

        self.itinerary += route

        # Choose random point inside destination as last coords
        internal_point = (
            self.navigation.floorplans[next_floor_number]
            .spaces[next_location]
            .get_random_internal_point()
        )

        next_coords = (internal_point.x, internal_point.y)
        self.itinerary.append((next_coords, next_floor_number))

        # Stay in this location for the given duration
        for _ in range(schedule_item.duration):
            self.itinerary.append((next_coords, next_floor_number))

        # update schedule items
        self.update_schedule_items(schedule_item)

    def build(self) -> None:
        """
        Build this agent's schedule and corresponding itinerary.
        """
        prev_coords = (
            int(round(self.entrance_door.path.point(0.5).real)),
            int(round(self.entrance_door.path.point(0.5).imag)),
        )

        prev_location = prev_coords
        prev_floor_number = self.entrance_floor

        self.itinerary.append((prev_coords, self.entrance_floor))

        while len(self.itinerary) < self.exit_time:

            schedule_item = self.find_next_schedule_item()

            next_location = schedule_item.location
            next_floor_number = schedule_item.floor_number
            floor_scale = self.navigation.floorplans[next_floor_number].scale
            agent_pace = self.get_pace(floor_scale)
            route = self.navigation.get_route(
                prev_location,
                prev_floor_number,
                next_location,
                next_floor_number,
                agent_pace,
            )

            if not route:
                if len(self.schedule_items) == 0:
                    raise ValueError("No route to primary office")
                else:
                    current_loc = self.navigation.floorplans[
                        prev_floor_number
                    ].spaces[prev_location]
                    dest = self.navigation.floorplans[
                        next_floor_number
                    ].spaces[next_location]

                    LOG.info(f"Doors in current loc: {current_loc.doors}")
                    LOG.info(f"Doors in destination: {dest.doors}")
                    msg = (
                        "No route found between these 2 locations: "
                        + f"{current_loc.unique_name} ({current_loc.id}) "
                        + f" and {dest.unique_name} ({dest.id})."
                    )
                    raise ValueError(msg)

            self.update_itinerary(route, schedule_item)
            prev_location = schedule_item.location
            prev_floor_number = schedule_item.floor_number

            remaining_daylength = self.daylength - len(self.itinerary)
            if remaining_daylength <= self.shortest_purpose_duration:
                break

        coords = (
            int(round(self.exit_door.path.point(0.5).real)),
            int(round(self.exit_door.path.point(0.5).imag)),
        )
        next_location = coords
        next_floor_number = self.exit_floor
        floor_scale = self.navigation.floorplans[next_floor_number].scale
        agent_pace = self.get_pace(floor_scale)
        route = self.navigation.get_route(
            prev_location,
            prev_floor_number,
            next_location,
            next_floor_number,
            agent_pace,
        )
        if route is None:
            myfloorplan = self.navigation.floorplans[prev_floor_number]
            myspace = myfloorplan.spaces[prev_location].unique_name
            LOG.info(
                "Last location: %s | specified exit: %s",
                myspace,
                next_location,
            )
            raise ValueError("Route to leave facility must not be None")

        self.itinerary += route
        self.itinerary.append((coords, self.exit_floor))
        self.itinerary.append((None, None))

        self.schedule_items.append(
            ScheduleItem(
                location=None,
                duration=0,
                floor_number=self.exit_floor,
                purpose="Leave for the day",
            )
        )

    def __str__(self) -> str:
        """
        Convert current schedule to a str for output purposes
        """
        day_length = sum(item.duration for item in self.schedule_items)

        string_repr = (
            "\nSchedule\n-----------------------\n"
            + "Day length: "
            + str(day_length)
            + " Number of items: "
            + str(len(self.schedule_items))
            + "\n\nSchedule details\n"
        )

        for i, item in enumerate(self.schedule_items):
            if item.location is None:
                location_id = "None"
            else:
                location_id = (
                    self.navigation.floorplans[item.floor_number]
                    .spaces[item.location]
                    .unique_name
                )
            string_repr += (
                str(i)
                + ". "
                + location_id
                + ": "
                + str(round(item.duration / 60.0, 2))
                + " min\t"
                + item.purpose
                + "\n"
            )

        return string_repr

    def get_next_position(self) -> Tuple[Optional[int], ...]:
        """Return the next position of this agent from its itinerary"""
        position = self.itinerary[self.current_standing]
        if self.current_standing < len(self.itinerary) - 1:
            self.current_standing += 1

        return position