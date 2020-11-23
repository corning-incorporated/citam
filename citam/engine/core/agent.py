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


class Agent:
    def __init__(self, name, schedule):

        self.name = name
        self.unique_id = name

        self.status = "S"
        self.office = None
        self.job_function = None

        self.n_contacts = 0

        self.pos = None
        self.current_location = None
        self.current_floor = None

        self.schedule = schedule

        return

    def step(self):

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
            # self.pos = new_position
            self.current_location = self.schedule.navigation.floorplans[
                floor_number
            ].identify_this_location(
                xy_position[0], xy_position[1], include_boundaries=True
            )
            self.current_floor = floor_number

        return has_moved