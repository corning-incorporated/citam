from typing import Tuple, List
import numpy as np
import logging
import os
import progressbar as pb
from citam.engine.schedulers.office_schedule import OfficeSchedule
from citam.engine.schedulers.meetings import MeetingSchedule
from citam.engine.schedulers.schedule import Schedule
from citam.engine.schedulers.scheduler import Scheduler
from citam.engine.constants import DEFAULT_SCHEDULING_RULES

LOG = logging.getLogger(__name__)


class OfficeScheduler(Scheduler):
    """Scheduler class used to create a typical schedules for an office
    building. This assumes each agent has an office space, go to meetings
    throughout the day and spend time in special spaces called labs.
    Supports the use of restrooms and dining areas by agents.
    """

    def __init__(
        self,
        facility,
        total_timesteps,
        timestep=1,
        scheduling_rules=None,
        meeting_policy=None,
        entry_exit_window=300,
        preassigned_offices=None,
        shifts=None,
    ) -> None:

        super().__init__(facility, timestep, total_timesteps)
        self.entry_exit_window = entry_exit_window
        self.preassigned_offices = preassigned_offices
        if scheduling_rules is None:
            self.scheduling_rules = DEFAULT_SCHEDULING_RULES
        else:
            self.scheduling_rules = scheduling_rules

        self.meeting_policy = meeting_policy
        if self.meeting_policy is None:
            LOG.info(
                "No meeting policy provided. No meetings will be created."
            )

        self.schedules = []
        if shifts is None:
            self.shifts = [
                {"name": "1", "start_time": 0, "percent_agents": 1.0}
            ]
        else:
            self.shifts = shifts

    def generate_meetings(self, n_agents: int) -> None:
        """
        Create meetings based on meeting policy.
        """
        # Get all meeting rooms
        meeting_room_objects = []
        for fn, floor_rooms in enumerate(self.facility.meeting_rooms):
            floor_room_objs = []
            for room_id in floor_rooms:
                room_obj = self.facility.floorplans[fn].spaces[room_id]
                floor_room_objs.append(room_obj)
            meeting_room_objects.append(floor_room_objs)

        # Create meeting schedule object
        agent_ids = list(range(n_agents))
        self.meeting_schedule = MeetingSchedule(
            meeting_room_objects,
            agent_ids,
            daylength=self.total_timesteps,
            policy_params=self.meeting_policy,
        )

        if self.meeting_policy is None:
            LOG.info(
                "No meeting policy provided. Meetings will not be generated."
            )
            return

        # Generate meetings
        n_meeting_rooms = sum(len(rooms) for rooms in meeting_room_objects)
        if n_meeting_rooms > 0:
            self.meeting_schedule.build()
        else:
            LOG.info("No meeting rooms found. Meetings will not be generated")

    def assign_office(self) -> Tuple[int, int]:
        """
        Assign an office to the current agent. If office spaces are not
        pre-assigned, select one randomly and remove it from list of available
        offices. Otherwise, return the next office from the queue.

        :return: office id and floor
        :rtype: Tuple[int, int]
        """

        if self.preassigned_offices is not None:
            office_id, office_floor = self.preassigned_offices.pop(0)
            if (
                office_id >= len(self.facility.floorplans[office_floor].spaces)
                or office_id < 0
            ):
                raise ValueError(
                    "Invalid preassigned office ID. Please double check."
                )
        else:
            floors_with_offices = [
                i
                for i in range(len(self.facility.all_office_spaces))
                if len(self.facility.all_office_spaces[i]) > 0
            ]
            if len(floors_with_offices) == 0:
                raise ValueError("No office space found throughout facility.")

            office_floor = np.random.choice(floors_with_offices)
            rint = np.random.randint(
                len(self.facility.all_office_spaces[office_floor])
            )
            office_id = self.facility.all_office_spaces[office_floor].pop(rint)

        return office_id, office_floor

    def run(self, n_agents: int) -> List[Schedule]:
        """Run this scheduler and return one schedule per agent.

        :param n_agents: Number of agents to create schedules for
        :type n_agents: int
        :param shifts: Dictionary describing a shift (group of agents with
                    the same start time)
        :type shifts: dict
        :raises ValueError: If unable to find an appropriate entrance for an
                    assigned office space.
        :return: list of schedule objects, one per agent
        :rtype: List[Schedule]
        """
        # Start by generating meetings
        self.generate_meetings(n_agents)

        # Now generate individual schedules
        self.schedules = []
        agent_pool = list(range(n_agents))
        for shift in self.shifts:
            if (
                "start_time" not in shift.keys()
                or "percent_agents" not in shift.keys()
                or "name" not in shift.keys()
            ):
                raise ValueError(
                    "Invalid shift info: name, start_time and "
                    "percent_agents required."
                )

            shift_start_time = shift["start_time"] + self.entry_exit_window
            n_shift_agents = round(shift["percent_agents"] * n_agents)
            shift_agents = np.random.choice(agent_pool, n_shift_agents)
            agent_pool = [a for a in agent_pool if a not in shift_agents]

            LOG.info("Working with shift: " + shift["name"])
            LOG.info("\tNumber of agents: " + str(n_shift_agents))
            LOG.info("\tAverage starting step: " + str(shift_start_time))

            for _ in pb.progressbar(shift_agents):

                # Find office space
                office_id, office_floor = self.assign_office()

                # Choose the closest entrance to office
                (
                    entrance_door,
                    entrance_floor,
                ) = self.facility.choose_best_entrance(office_floor, office_id)

                if entrance_door is None:
                    office = self.facility.floorplans[office_floor].spaces[
                        office_id
                    ]
                    raise ValueError(
                        f"Unable to assign this office: {office.unique_name}"
                    )

                # Sample start time and exit time from a poisson distribution
                start_time = -1
                while start_time < 0 or start_time > 2 * shift_start_time:
                    start_time = round(np.random.poisson(shift_start_time))

                exit_time = 0
                while (
                    exit_time == 0
                    or exit_time > self.total_timesteps
                    or exit_time
                    < self.total_timesteps - 2 * self.entry_exit_window
                ):

                    exit_time = round(
                        np.random.poisson(
                            self.total_timesteps - self.entry_exit_window
                        )
                    )

                # Exit through the same door
                exit_door = entrance_door
                exit_floor = entrance_floor

                schedule = OfficeSchedule(
                    timestep=self.timestep,
                    start_time=start_time,
                    exit_time=exit_time,
                    entrance_door=entrance_door,
                    entrance_floor=entrance_floor,
                    exit_door=exit_door,
                    exit_floor=exit_floor,
                    office_location=office_id,
                    office_floor=office_floor,
                    navigation=self.facility.navigation,
                    scheduling_rules=self.scheduling_rules,
                    meetings=self.meeting_schedule.meetings,
                )
                schedule.build()
                self.schedules.append(schedule)

        return self.schedules

    def save_to_files(self, work_directory) -> None:
        """Write key scheduling info to file.

        Two files are created with respectively the following contents:
        1. meetings.txt with all the meetings
        3. agent_ids.csv with each agent's assigned office

        :param work_directory: [description]
        :type work_directory: [type]
        """
        filename = os.path.join(work_directory, "agents.csv")
        try:
            with open(filename, "w") as outfile:
                outfile.write("AgentID,OfficeID,FloorID\n")
                for i, schedule in enumerate(self.schedules):
                    outfile.write(
                        str(i)
                        + ","
                        + str(schedule.office_location)
                        + ","
                        + str(schedule.office_floor)
                        + "\n"
                    )
        except Exception as e:
            LOG.error(f"An eception occured while writing agents.csv. {e}")

        # Meetings
        filename = os.path.join(work_directory, "meetings.txt")
        try:
            with open(filename, "w") as outfile:
                outfile.write(
                    "Total number of meetings: "
                    + str(len(self.meeting_schedule.meetings))
                    + "\n\n"
                )
                for meeting in self.meeting_schedule.meetings:
                    outfile.write(str(meeting) + "\n")
        except Exception as e:
            LOG.error(f"An eception occured while writing meetings.csv. {e}")
