from citam.engine.core.agent import Agent
from citam.engine.facility.indoor_facility import Facility

from abc import ABC, abstractmethod
from typing import List, Union
import os


class Calculator(ABC):
    def __init__(self, facility: Facility, **kwargs) -> None:
        super().__init__()
        self.facility = facility
        self.kwargs = kwargs

    @abstractmethod
    def run(self, current_step: int, agents: List[Agent]):
        pass

    @abstractmethod
    def save_to_files(
        self,
        agents: List[Agent],
        work_directory: Union[str, bytes, os.PathLike],
    ):
        pass
