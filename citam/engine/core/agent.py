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

from typing import Optional

from citam.engine.schedulers.schedule import Schedule


class Agent:
    """The agent in Agent-based modeling. An agent represents a user of the
    facility (employee or otherwise). An agent has a schedule (and associated
    itinerary) that they follow throughout the day. This also keeps track of
    the number of contacts that this agent has had so far.
    """

    def __init__(
        self,
        unique_id: int,
        schedule: Schedule,
        name: Optional[str] = None,
        office_id: Optional[int] = None,
        job_function: Optional[str] = None,
    ):
        """
        Initialize an agent object.

        Create a new agent object to represent a facility user.

        :param unique_id: The unique identifier of this agent.
        :type unique_id: int
        :param schedule: The schedule of this agent.
        :type schedule: Schedule
        :param name: The name of this agent, defaults to None
        :type name: str, optional
        :param office_id: ID of the office space assigned to this agent,
            defaults to None
        :type office_id: int, optional
        :param job_function: job function of this agent, defaults to None
        :type job_function: str, optional
        """
        self.unique_id = unique_id
        self.schedule = schedule

        self.name = name
        self.office_id = office_id
        self.job_function = job_function

        self.cumulative_contact_duration = 0
        self.pos = None
        self.current_location = None
        self.current_floor = None

    def step(self):
        """
        Move this agent one step forward in its itinerary.

        This updates the agent's current position only if the agent's itinerary
        indicates a different location.

        :return: whether the agent has moved from its current location or not.
        :rtype: bool
        """
        xy_position, floor_number = self.schedule.get_next_position()
        has_moved = False

        if xy_position != self.pos or floor_number != self.current_floor:
            has_moved = True

        if xy_position is not None:

            if self.pos is None:
                self.schedule.navigation.floorplans[floor_number].place_agent(
                    self, xy_position
                )
            else:  # TODO: Handle when changing floors
                if self.current_floor == floor_number:
                    self.schedule.navigation.floorplans[
                        floor_number
                    ].move_agent(self, xy_position)
                else:
                    self.schedule.navigation.floorplans[
                        self.current_floor
                    ].remove_agent(self)
                    self.schedule.navigation.floorplans[
                        floor_number
                    ].place_agent(self, xy_position)

            self.current_location = self.schedule.navigation.floorplans[
                floor_number
            ].identify_this_location(
                xy_position[0], xy_position[1], include_boundaries=True
            )
            self.current_floor = floor_number

        return has_moved
