from citam.engine.core.agent import Agent
from citam.engine.facility.indoor_facility import Facility

from abc import ABC, abstractmethod
from typing import List, Optional, OrderedDict, Union
import os


class Calculator(ABC):
    def __init__(self, facility: Facility, **kwargs) -> None:
        super().__init__()
        self.facility = facility
        self.kwargs = kwargs

    @abstractmethod
    def initialize(
        self,
        agents: OrderedDict[int, Agent],
        work_directory: Optional[Union[str, bytes, os.PathLike]] = None,
    ):
        pass

    @abstractmethod
    def run(self, current_step: int, agents: List[Agent], **kwargs):
        pass

    @abstractmethod
    def finalize(
        self,
        agents: List[Agent],
        work_directory: Optional[Union[str, bytes, os.PathLike]] = None,
    ):
        pass
