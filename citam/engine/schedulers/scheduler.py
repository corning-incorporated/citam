from abc import ABC, abstractmethod
from citam.engine.facility.indoor_facility import Facility


class Scheduler(ABC):
    def __init__(
        self, facility: Facility, timestep: int, total_timesteps: int,
    ) -> None:
        super().__init__()
        self.facility = facility
        self.timestep = timestep
        self.total_timesteps = total_timesteps

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def save_to_files(self, work_directory):
        pass
