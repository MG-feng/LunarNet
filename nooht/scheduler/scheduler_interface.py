from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
from enum import Enum
import time
import uuid

class Scheduler(ABC):
    @abstractmethod
    async def start(self):
        pass
    
    @abstractmethod
    async def stop(self):
        pass
    
    @abstractmethod
    async def submit(self, task: 'Task') -> bool:
        pass
    
    @abstractmethod
    async def execute(self, task_id: str) -> Any:
        pass

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class DeviceType(Enum):
    GPU = "gpu"
    TPU = "tpu"
    CPU = "cpu"

@dataclass
class ComputeRequirement:
    device: DeviceType = DeviceType.CPU
    compute_units: float = 1.0

@dataclass
class Task:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    compute_req: ComputeRequirement = field(default_factory=ComputeRequirement)
    payload: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    timeout: int = 300
