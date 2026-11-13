"""
UrbanFlow AI - Base Agent Contract
Defines the standard lifecycle and event-emitting protocol for all specialized agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from shared.world_state import WorldState
from shared.schemas import AgentEvent


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, world_state: WorldState, **kwargs) -> AgentEvent:
        """
        Executes agent logic against the shared canonical WorldState snapshot
        and appends an AgentEvent to the traceable audit log.
        """
        pass

