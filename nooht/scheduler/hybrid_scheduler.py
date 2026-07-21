import asyncio
import itertools
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .scheduler_interface import Scheduler, Task, TaskPriority, TaskStatus, DeviceType
import logging

logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    device_id: str
    device_type: DeviceType
    compute_capacity: float
    current_load: float = 0.0
    is_available: bool = True

class HybridScheduler(Scheduler):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Task] = {}
        self._max_completed_tasks = config.get('task_history_limit', 10000)
        self._devices: Dict[str, DeviceInfo] = {}
        self._task_queue = None
        self._queue_counter = itertools.count()
        self._running = False
        self._workers: List[asyncio.Task] = []
        
        self._devices['cpu_0'] = DeviceInfo('cpu_0', DeviceType.CPU, 1.0)

    async def start(self):
        if self._task_queue is None:
            self._task_queue = asyncio.PriorityQueue()
        self._running = True
        num_workers = self.config.get('num_workers', 4)
        for i in range(num_workers):
            self._workers.append(asyncio.create_task(self._worker_loop(f"worker_{i}")))

    async def stop(self):
        self._running = False
        for worker in self._workers:
            worker.cancel()
        self._workers.clear()

    async def submit(self, task: Task) -> bool:
        if self._task_queue is None:
            self._task_queue = asyncio.PriorityQueue()
        count = next(self._queue_counter)
        await self._task_queue.put((task.priority.value, count, task.task_id, task))
        self._tasks[task.task_id] = task
        return True

    async def _worker_loop(self, worker_name: str):
        while self._running:
            try:
                priority, count, task_id, task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self.execute(task_id)
                self._task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def execute(self, task_id: str) -> Any:
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING
        
        device = min([d for d in self._devices.values() if d.is_available], key=lambda d: d.current_load)
        device.current_load += task.compute_req.compute_units
        
        try:
            result = await asyncio.wait_for(task.callback(task.payload), timeout=task.timeout)
            task.status = TaskStatus.COMPLETED
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            raise e
        finally:
            device.current_load = max(0, device.current_load - task.compute_req.compute_units)
            self._archive_task(task_id)

    def _archive_task(self, task_id: str):
        if task_id in self._tasks:
            task = self._tasks.pop(task_id)
            if len(self._completed_tasks) >= self._max_completed_tasks:
                del self._completed_tasks[next(iter(self._completed_tasks))]
            self._completed_tasks[task_id] = task
