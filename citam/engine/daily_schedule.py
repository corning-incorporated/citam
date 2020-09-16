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

from citam.engine.constants import (
        CAFETERIA_VISIT,
        LAB_WORK,
        OFFICE_WORK,
        RESTROOM_VISIT,
        MEETING,
        LAST_SCHEDULE_ITEM_CUTOFF
    )


class Schedule:
    """Create and manage agents schedule and itinerary
    """
    def __init__(self,
                 timestep,
                 start_time,
                 exit_time,
                 entrance_door,
                 entrance_floor,
                 exit_door,
                 exit_floor,
                 office_location,
                 office_floor,
                 navigation,
                 scheduling_rules,
                 meetings=None
                 ):
        super().__init__()

        self.start_time = start_time
        self.exit_time = exit_time
        self.entrance_door = entrance_door
        self.entrance_floor = entrance_floor
        self.exit_door = exit_door
        self.exit_floor = exit_floor
        self.daylength = exit_time - start_time
        self.timestep = timestep
        self.meetings = meetings
        if meetings is None:
            self.meetings = []

        self.scheduling_rules = scheduling_rules

        self.office_location = office_location
        self.office_floor = office_floor
        self.navigation = navigation

        self.curent_standing = 0

        self.itinerary = [[None, None] for i in range(start_time-2)]
        self.schedule_items = []

        self.meeting_rooms, self.labs, self.cafes, self.restrooms,\
            self.offices = [], [], [], [], []  # List of lists of space indices

        for fp in self.navigation.floorplans:
            floor_offices, floor_labs, floor_cafes, floor_restrooms,\
                floor_meeting_rooms = [], [], [], [], []

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

        return

    def build_schedule_item(self,
                            purpose,
                            details,
                            next_meeting_start_time,
                            meeting_buffer
                            ):
        """Given a purpose and additional properties such as meeting duration,
        build a schedule item for this agent.
        """
        # Choose a duration
        remaining_daylength = self.daylength - len(self.itinerary)
        max_duration = min([details['max_duration'], remaining_daylength])
        if next_meeting_start_time is not None:
            max_end_time = next_meeting_start_time - meeting_buffer
            if len(self.itinerary) + max_duration > max_end_time:
                max_duration = max_end_time - len(self.itinerary)

        if max_duration <= details['min_duration']:
            duration = max_duration
        else:
            duration = np.random.randint(details['min_duration'], max_duration)

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
                raise ValueError('total locations must be > 0')

            floor_number = np.random.randint(len(self.navigation.floorplans))
            location = np.random.choice(possible_locations[floor_number])

        # Setup schedule item
        schedule_item = {
            'purpose': purpose,
            'location': location,
            'floor_number': floor_number,
            'duration': duration
        }
        return schedule_item

    def find_next_schedule_item(self, current_location=None):
        """Create the next schedule item for this agent. This will correspond
        to the next meeting on this agent's calendar or to a randomly selected
        item from a list of valid purposes.
        """
        meeting_buffer = 60*15
        next_meeting_start_time = None
        # Handle meetings first
        if len(self.meetings) > 0:
            next_meeting = self.meetings[0]
            next_meeting_start_time = next_meeting.start_time
            # Check if meeting is happening within 15 timestep of now, if so
            if next_meeting.start_time - len(self.itinerary) <= meeting_buffer:
                schedule_item = {'purpose': MEETING,
                                 'duration': next_meeting.duration,
                                 'location': next_meeting.location,
                                 'floor_number': next_meeting.floor_number
                                 }
                return schedule_item

        if len(self.schedule_items) == 0:  # First item for the day

            item_details = self.scheduling_rules[OFFICE_WORK]
            schedule_item = self.build_schedule_item(OFFICE_WORK,
                                                     item_details,
                                                     next_meeting_start_time,
                                                     meeting_buffer
                                                     )
            return schedule_item

        # If no upcoming meeting and agent is already in facility, let's pick
        # a purpose using the scheduling policy
        purpose = self.choose_valid_scheduling_purpose()
        item_details = self.scheduling_rules[purpose]
        schedule_item = self.build_schedule_item(purpose,
                                                 item_details,
                                                 next_meeting_start_time,
                                                 meeting_buffer
                                                 )

        return schedule_item

    def choose_valid_scheduling_purpose(self):
        """Find a valid scheduling purpose using rules defined in the
        scheduling policy for this facility. Common purposes include:
        restroom visits, lab work, office work and cafeteria visit.

        """
        # TODO: add more complex rules based on employee details
        # (e.g. no office work or no lab work).

        # Only keep purposes that have corresponding rooms in this facility
        purposes_under_consideration = [OFFICE_WORK]

        # TODO: Associate each purpose with a room type at the model level
        locations_for_purpose = {
            RESTROOM_VISIT: self.restrooms,
            LAB_WORK: self.labs,
            CAFETERIA_VISIT: self.cafes,
        }

        for purpose in self.scheduling_rules:
            if purpose in locations_for_purpose.keys():
                possible_locations = locations_for_purpose[purpose]
                total_locations = sum([len(pl) for pl in possible_locations])
                if total_locations > 0:
                    purposes_under_consideration.append(purpose)

        # Count how many items of each type is already in the schedule
        n_items = [0 for i in purposes_under_consideration]
        for employee_item in self.schedule_items:
            # Current items already in this employee's schedule
            for i, purpose in enumerate(purposes_under_consideration):
                if purpose == employee_item['purpose']:
                    n_items[i] += 1
                    break

        valid_purposes = []

        # Don't consider schedule item that already reached their max instances
        for i, purpose in enumerate(purposes_under_consideration):
            item_details = self.scheduling_rules[purpose]
            if n_items[i] < item_details['max_instances']:
                valid_purposes.append(purpose)

        # No consecutive restroom visits
        if RESTROOM_VISIT in valid_purposes and \
                self.schedule_items[-1]['purpose'] == RESTROOM_VISIT:
            valid_purposes.remove(RESTROOM_VISIT)

        # Cafeteria visits only happen around the middle of the work day
        if CAFETERIA_VISIT in valid_purposes:
            if len(self.itinerary) < round(self.daylength/3.0) or \
                    len(self.itinerary) > round(2*self.daylength/3.0):
                valid_purposes.remove(CAFETERIA_VISIT)

        # Randomly choose a purpose from list of valid purposes
        if len(valid_purposes) > 0:
            chosen_purpose = np.random.choice(valid_purposes)
        else:
            raise ValueError('At least one valid purpose required.')

        return chosen_purpose

    def get_pace(self, scale):
        """Randomly pick a walking pace for this agent by sampling from a
        gaussian distribution around a pace of 4 ft/sec. The acceptable
        range is set between 2 and 6 ft/sec

        Parameters
        - Scale: the scale of the floorplan in [ft]/[drawing unit].

        Returns
        - Pace: the agent's pace in [drawing unit]/[timestep]
        """
        # typical walkging pace: 4 ft/sec; Range : 2 to 6 ft/sec
        pace = 0.0
        while pace < 2.0 or pace > 6.0:
            pace = np.random.normal(loc=4)
        pace *= self.timestep
        pace /= scale

        return pace

    def update_itinerary(self, route, schedule_item):
        """
        Given a route and a next schedule item, update this agent's itinerary
        accordingly
        """
        next_location = schedule_item['location']
        next_floor_number = schedule_item['floor_number']
        if route is not None:

            # Update itinerary
            self.itinerary += route

            # Choose random point inside destination as last coords
            internal_point = self.navigation.floorplans[next_floor_number]\
                .spaces[next_location].get_random_internal_point()

            prev_coords = (internal_point.x, internal_point.y)
            prev_location = next_location
            prev_floor_number = next_floor_number
            self.itinerary.append([prev_coords, prev_floor_number])

            # Stay in this location for the given duration
            for j in range(schedule_item['duration']):
                self.itinerary.append([prev_coords, prev_floor_number])

            # update list of schedule items
            if len(self.schedule_items) > 0:
                last_item = self.schedule_items[-1]
                if last_item['purpose'] == schedule_item['purpose'] and \
                        last_item['location'] == schedule_item['location']:
                    # If this purpose and location are the same as the last
                    # one, just update the last one
                    self.schedule_items[-1]['duration'] += \
                        schedule_item['duration']
                else:
                    self.schedule_items.append(schedule_item)
            else:
                self.schedule_items.append(schedule_item)

        elif len(self.schedule_items) == 0:
            raise ValueError('Cannot compute route to primary office')

        return prev_floor_number, prev_location

    def build(self):
        """Build this agent's schedule and corresponding itinerary.
        """
        prev_coords = (int(round(self.entrance_door.path.point(0.5).real)),
                       int(round(self.entrance_door.path.point(0.5).imag))
                       )

        prev_location = prev_coords
        prev_floor_number = self.entrance_floor

        self.itinerary.append([prev_coords, self.entrance_floor])

        while len(self.itinerary) < self.exit_time:

            schedule_item = self.find_next_schedule_item()

            next_location = schedule_item['location']
            next_floor_number = schedule_item['floor_number']
            floor_scale = self.navigation.floorplans[next_floor_number].scale
            agent_pace = self.get_pace(floor_scale)
            route = self.navigation.get_route(prev_location,
                                              prev_floor_number,
                                              next_location,
                                              next_floor_number,
                                              agent_pace
                                              )

            prev_floor_number, prev_location = \
                self.update_itinerary(route, schedule_item)

            remaining_daylength = self.daylength - len(self.itinerary)
            if remaining_daylength <= LAST_SCHEDULE_ITEM_CUTOFF:
                break

        coords = (int(round(self.exit_door.path.point(0.5).real)),
                  int(round(self.exit_door.path.point(0.5).imag))
                  )
        next_location = coords
        next_floor_number = self.exit_floor
        floor_scale = self.navigation.floorplans[next_floor_number].scale
        agent_pace = self.get_pace(floor_scale)
        route = self.navigation.get_route(prev_location,
                                          prev_floor_number,
                                          next_location,
                                          next_floor_number,
                                          agent_pace)
        if route is None:
            myfloorplan = self.navigation.floorplans[prev_floor_number]
            myspace = myfloorplan.spaces[prev_location].unique_name
            logging.info('Last location is: ' + myspace)
            logging.info('Specified exit is: ' + str(next_location))
            raise ValueError("Route to leave facility must not be None")

        self.itinerary += route
        self.itinerary.append([coords, self.exit_floor])
        self.itinerary.append([None, None])

        self.schedule_items.append({'location': None,
                                    'duration': 0,
                                    'floor_number': self.exit_floor,
                                    'purpose': 'Leave for the day'})

        return self

    def __str__(self):
        """Convert current schedule to a str for output purposes
        """
        day_length = sum([item['duration'] for item in self.schedule_items])

        string_repr = '\nSchedule\n-----------------------\n' + \
            'Day length: ' + str(day_length) + ' Number of items: ' + \
            str(len(self.schedule_items)) + '\n\nSchedule details\n'

        for i, item in enumerate(self.schedule_items):
            if item['location'] is None:
                location_id = 'None'
            else:
                location_id = self.navigation.floorplans[item['floor_number']]\
                                .spaces[item['location']].unique_name
            string_repr += str(i) + '. ' + location_id + ': ' + \
                str(round(item['duration']/60.0, 2)) + ' min\t' + \
                item['purpose'] + '\n'

        return string_repr

    def get_next_position(self):
        """Return the next position of this agent from its itinerary
        """
        position = self.itinerary[self.curent_standing]
        if self.curent_standing < len(self.itinerary) - 1:
            self.curent_standing += 1

        return position
