#!/usr/bin/env python3
"""
Nooht Framework v0.2.1 - Automated Repository Setup Script
Generates complete Phase 0 (Frozen) and Phase 1 (Scaffold) code structure.
"""
import os

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"  Created: {filepath}")

# ==========================================
# 1. Root & Config
# ==========================================
write_file("nooht/__init__.py", '''"""
Nooht Framework v0.2.1 (Phase 1 Ready)
"""
__version__ = "0.2.1"
''')

write_file("nooht/config/__init__.py", '''from .config_manager import ConfigManager, NoohtConfig, FrozenConfigError
from .config_schema import ConfigSchema, ModuleConfig, KTUConfig, MemoryConfig, SchedulerConfig, RuntimeConfig, DeviceType, ComputePrecision
''')

write_file("nooht/config/config_schema.py", '''from dataclasses import dataclass, field
from typing import Dict, List, Any
from enum import Enum

class DeviceType(Enum):
    GPU = "gpu"
    TPU = "tpu"
    CPU = "cpu"

class ComputePrecision(Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"

@dataclass
class ModuleConfig:
    name: str
    enabled: bool = True

@dataclass
class KTUConfig(ModuleConfig):
    char_dim: int = 128
    token_dim: int = 512
    structure_dim: int = 256
    ktu_dim: int = 768
    name: str = "ktu"

@dataclass
class MemoryConfig(ModuleConfig):
    l0_max_bytes: int = 16 * (1024**3)
    l1_max_size: int = 1000
    l2_max_size: int = 100
    name: str = "memory"

@dataclass
class SchedulerConfig(ModuleConfig):
    max_concurrent_tasks: int = 100
    task_history_limit: int = 10000
    name: str = "scheduler"

@dataclass
class RuntimeConfig(ModuleConfig):
    devices: List[DeviceType] = field(default_factory=lambda: [DeviceType.CPU])
    precision: ComputePrecision = ComputePrecision.FP32
    num_workers: int = 4
    name: str = "runtime"

@dataclass
class ConfigSchema:
    project_name: str = "Nooht"
    version: str = "0.2.1"
    ktu: KTUConfig = field(default_factory=KTUConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
''')

write_file("nooht/config/config_manager.py", '''import os
import json
import yaml
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from copy import deepcopy
from .config_schema import ConfigSchema, KTUConfig, MemoryConfig, SchedulerConfig, RuntimeConfig, DeviceType, ComputePrecision

class FrozenConfigError(Exception):
    pass

class NoohtConfig:
    def __init__(self, schema: ConfigSchema):
        self._schema = schema
        self._frozen = False
        self._overrides: Dict[str, Any] = {}

    def freeze(self):
        self._frozen = True

    def get(self, path: str, default: Any = None) -> Any:
        if path in self._overrides:
            return self._overrides[path]
        parts = path.split(".")
        current = self._schema
        try:
            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict):
                    current = current[part]
                else:
                    return default
            return current
        except (KeyError, AttributeError):
            return default

    def set(self, path: str, value: Any):
        if self._frozen:
            raise FrozenConfigError(f"Cannot modify frozen config. Attempted to set '{path}'.")
        self._overrides[path] = value

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config: Optional[NoohtConfig] = None

    @classmethod
    def from_yaml(cls, path: str, freeze: bool = True) -> NoohtConfig:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        schema = cls._dict_to_schema(data)
        config = NoohtConfig(schema)
        if freeze:
            config.freeze()
        return config

    @staticmethod
    def _dict_to_schema(data: Dict) -> ConfigSchema:
        schema = ConfigSchema()
        if 'ktu' in data:
            schema.ktu = KTUConfig(**data['ktu'])
        if 'memory' in data:
            schema.memory = MemoryConfig(**data['memory'])
        if 'scheduler' in data:
            schema.scheduler = SchedulerConfig(**data['scheduler'])
        if 'runtime' in data:
            runtime_data = data['runtime'].copy()
            if 'devices' in runtime_data:
                runtime_data['devices'] = [DeviceType(d) for d in runtime_data['devices']]
            if 'precision' in runtime_data:
                runtime_data['precision'] = ComputePrecision(runtime_data['precision'])
            schema.runtime = RuntimeConfig(**runtime_data)
        return schema
''')

write_file("nooht/config/default.yaml", '''project_name: "Nooht"
version: "0.2.1"

ktu:
  char_dim: 128
  token_dim: 512
  structure_dim: 256
  ktu_dim: 768

memory:
  l0_max_bytes: 17179869184
  l1_max_size: 1000
  l2_max_size: 100

scheduler:
  max_concurrent_tasks: 100
  task_history_limit: 10000

runtime:
  devices:
    - cpu
  precision: fp32
  num_workers: 4
''')

# ==========================================
# 2. Engine Core
# ==========================================
write_file("nooht/engine/__init__.py", '''from .module_interface import NoohtModule, ModuleStatus
from .module_registry import ModuleRegistry
from .pipeline import Pipeline, PipelineStage, PipelineExecutor
from .pipeline_registry import PipelineRegistry
from .engine_core import NoohtEngine
''')

write_file("nooht/engine/module_interface.py", '''from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum
import uuid

class ModuleStatus(Enum):
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"

class NoohtModule(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.module_id = str(uuid.uuid4())[:8]
        self.config = config
        self.status = ModuleStatus.UNINITIALIZED

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        pass
''')

write_file("nooht/engine/module_registry.py", '''import asyncio
from typing import Dict, Type, Optional
from .module_interface import NoohtModule
import logging

logger = logging.getLogger(__name__)

class ModuleRegistry:
    def __init__(self):
        self._modules: Dict[str, NoohtModule] = {}
        self._module_types: Dict[str, Type[NoohtModule]] = {}
        self._lock = None

    def _get_lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def create_instance(self, module_type: str, instance_name: str, config: Dict = None) -> Optional[NoohtModule]:
        async with self._get_lock():
            if module_type not in self._module_types:
                return None
            if instance_name in self._modules:
                return self._modules[instance_name]
            
            module_class = self._module_types[module_type]
            instance = module_class(name=instance_name, config=config or {})
            await instance.initialize()
            self._modules[instance_name] = instance
            return instance

    async def shutdown_all(self):
        async with self._get_lock():
            for name, module in list(self._modules.items()):
                await module.cleanup()
            self._modules.clear()
''')

write_file("nooht/engine/pipeline.py", '''from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StageType(Enum):
    SEQUENTIAL = "sequential"

class PipelineStage:
    def __init__(self, name: str, module_name: str, stage_type: StageType = StageType.SEQUENTIAL):
        self.name = name
        self.module_name = module_name

class Pipeline:
    def __init__(self, name: str):
        self.name = name
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> 'Pipeline':
        self.stages.append(stage)
        return self

class PipelineExecutor:
    def __init__(self, registry):
        self.registry = registry

    async def execute(self, pipeline: Pipeline, inputs: Dict[str, Any]) -> Dict[str, Any]:
        current_data = dict(inputs)
        for stage in pipeline.stages:
            module = self.registry._modules.get(stage.module_name)
            if not module:
                raise RuntimeError(f"Module not found: {stage.module_name}")
            current_data = await module.execute(current_data)
        return current_data
''')

write_file("nooht/engine/pipeline_registry.py", '''from typing import Dict, Optional, List
from .pipeline import Pipeline
import logging

logger = logging.getLogger(__name__)

class PipelineRegistry:
    def __init__(self):
        self._pipelines: Dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline) -> bool:
        self._pipelines[pipeline.name] = pipeline
        return True

    def get(self, name: str) -> Optional[Pipeline]:
        return self._pipelines.get(name)

    def clear(self):
        self._pipelines.clear()
''')

write_file("nooht/engine/engine_core.py", '''import asyncio
from typing import Dict, Any
from .module_registry import ModuleRegistry
from .pipeline_registry import PipelineRegistry
from .pipeline import PipelineExecutor, Pipeline
import logging

logger = logging.getLogger(__name__)

class NoohtEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.module_registry = ModuleRegistry()
        self.pipeline_registry = PipelineRegistry()
        self.pipeline_executor = PipelineExecutor(self.module_registry)
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start(self) -> bool:
        self._running = True
        self._tasks['monitor'] = asyncio.create_task(self._monitor_loop())
        return True

    async def stop(self) -> bool:
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        await self.module_registry.shutdown_all()
        self.pipeline_registry.clear()
        return True

    def register_pipeline(self, pipeline: Pipeline) -> bool:
        return self.pipeline_registry.register(pipeline)

    async def execute_pipeline(self, pipeline_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._running:
            raise RuntimeError("Engine is not running")
        pipeline = self.pipeline_registry.get(pipeline_name)
        if pipeline is None:
            raise ValueError(f"Pipeline not found: {pipeline_name}")
        return await self.pipeline_executor.execute(pipeline, inputs)

    async def _monitor_loop(self):
        while self._running:
            await asyncio.sleep(10)
''')

# ==========================================
# 3. Scheduler (Phase 0 Frozen V2.1)
# ==========================================
write_file("nooht/scheduler/__init__.py", '''from .scheduler_interface import Scheduler, Task, TaskPriority, TaskStatus, DeviceType
from .hybrid_scheduler import HybridScheduler
''')

write_file("nooht/scheduler/scheduler_interface.py", '''from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
from enum import Enum
import time
import uuid

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
''')

write_file("nooht/scheduler/hybrid_scheduler.py", '''import asyncio
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
''')

# ==========================================
# 4. Distributed (Phase 0 Frozen V2.1)
# ==========================================
write_file("nooht/distributed/__init__.py", '''from .parameter_server import HybridParameterServer
''')

write_file("nooht/distributed/parameter_server.py", '''import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging
import torch

logger = logging.getLogger(__name__)

@dataclass
class GradientUpdate:
    worker_id: str
    gradients: Dict[str, torch.Tensor]
    step: int

class HybridParameterServer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.learning_rate = config.get('learning_rate', 1e-4)
        self.parameters: Dict[str, torch.Tensor] = {}
        self._gradient_queue: asyncio.Queue = asyncio.Queue()
        self._velocity: Dict[str, torch.Tensor] = {}

    async def push_gradients(self, update: GradientUpdate):
        await self._gradient_queue.put(update)

    async def update_loop(self):
        while True:
            updates = []
            while not self._gradient_queue.empty():
                updates.append(await self._gradient_queue.get())
            
            if not updates:
                await asyncio.sleep(0.01)
                continue

            for param_name in self.parameters.keys():
                sum_grad = None
                count = 0
                for update in updates:
                    if param_name in update.gradients:
                        grad = update.gradients[param_name]
                        if sum_grad is None:
                            sum_grad = grad.clone()
                        else:
                            sum_grad = torch.add(sum_grad, grad)
                        count += 1
                
                if count > 0 and param_name in self.parameters:
                    avg_grad = torch.div(sum_grad, count)
                    if param_name not in self._velocity:
                        self._velocity[param_name] = torch.zeros_like(self.parameters[param_name])
                    
                    self._velocity[param_name] = 0.9 * self._velocity[param_name] - self.learning_rate * avg_grad
                    self.parameters[param_name] = torch.add(self.parameters[param_name], self._velocity[param_name])
''')

# ==========================================
# 5. Phase 1 Scaffold - Memory
# ==========================================
write_file("nooht/memory/__init__.py", '''from .memory_interface import MemoryEntry, MemoryQuery
from .memory_tracker import MemoryFootprintTracker
from .hmc_compressor import HMCCompressor
from .scm_graph import SemanticCodeMemory
from .memory_broker import MemoryBroker
''')

write_file("nooht/memory/memory_interface.py", '''from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import time
import uuid

class MemoryLevel(Enum):
    L0_RAM = "l0_ram"
    L1_SHARED = "l1_shared"
    L2_DISK = "l2_disk"

@dataclass
class MemoryEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: MemoryLevel = MemoryLevel.L0_RAM
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    
    def estimate_bytes(self) -> int:
        from .memory_tracker import MemoryFootprintTracker
        return MemoryFootprintTracker.estimate_bytes(self.data)

@dataclass
class MemoryQuery:
    query_vector: Any = None
    top_k: int = 5
''')

write_file("nooht/memory/memory_tracker.py", '''import torch
from typing import Any

class MemoryFootprintTracker:
    @staticmethod
    def estimate_bytes(data: Any) -> int:
        if isinstance(data, torch.Tensor):
            return data.numel() * data.element_size()
        elif isinstance(data, str):
            return len(data.encode('utf-8'))
        elif isinstance(data, dict):
            return sum(MemoryFootprintTracker.estimate_bytes(v) for v in data.values())
        elif isinstance(data, list):
            return sum(MemoryFootprintTracker.estimate_bytes(v) for v in data)
        return 0
''')

write_file("nooht/memory/hmc_compressor.py", '''import asyncio
import torch
from typing import List
from .memory_interface import MemoryEntry
from ..engine.module_interface import NoohtModule

class HMCCompressor(NoohtModule):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._compression_semaphore = asyncio.Semaphore(4)
        self._device = "cpu"

    async def initialize(self) -> bool:
        return True

    async def execute(self, inputs: dict) -> dict:
        return inputs

    async def cleanup(self) -> bool:
        return True

    async def compress_l0_to_l1(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        async with self._compression_semaphore:
            pass

    async def compress_l1_to_l2(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        async with self._compression_semaphore:
            pass
''')

write_file("nooht/memory/scm_graph.py", '''from typing import Dict, List, Any
from ..engine.module_interface import NoohtModule
import asyncio

class SemanticCodeMemory(NoohtModule):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._graph = {}

    async def initialize(self) -> bool:
        return True

    async def execute(self, inputs: dict) -> dict:
        return inputs

    async def cleanup(self) -> bool:
        return True

    async def query_impact_analysis(self, function_name: str, max_depth: int = 5, timeout_ms: int = 500) -> Dict:
        visited_set = set()
        pass
''')

write_file("nooht/memory/memory_broker.py", '''import asyncio
from collections import OrderedDict
from typing import Dict, Any, List, Optional
from .memory_interface import MemoryEntry, MemoryLevel, MemoryQuery
from .hmc_compressor import HMCCompressor
from ..engine.module_interface import NoohtModule
import logging

logger = logging.getLogger(__name__)

class MemoryBroker(NoohtModule):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._l0_memory: OrderedDict = OrderedDict()
        self._l0_max_bytes = config.get("l0_max_bytes", 16 * (1024**3))
        self._current_l0_bytes = 0
        self._hmc_compressor = HMCCompressor("hmc_compressor", config)
        self._lock = None

    def _get_lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def initialize(self) -> bool:
        await self._hmc_compressor.initialize()
        return True

    async def execute(self, inputs: dict) -> dict:
        return inputs

    async def cleanup(self) -> bool:
        return True

    async def store(self, entry: MemoryEntry) -> str:
        async with self._get_lock():
            entry_size = entry.estimate_bytes()
            
            while self._current_l0_bytes + entry_size > self._l0_max_bytes:
                if not self._l0_memory:
                    break
                old_id, old_entry = self._l0_memory.popitem(last=False)
                self._current_l0_bytes -= old_entry.estimate_bytes()
                asyncio.create_task(self._hmc_compressor.compress_l0_to_l1([old_entry]))
            
            self._l0_memory[entry.entry_id] = entry
            self._current_l0_bytes += entry_size
            return entry.entry_id
''')

# ==========================================
# 6. Phase 1 Scaffold - KTU
# ==========================================
write_file("nooht/ktu/__init__.py", '''from .ktu_encoder import KTUEncoder, KTUVector
''')

write_file("nooht/ktu/ktu_encoder.py", '''import torch
import torch.nn as nn
from typing import Dict, Any
from dataclasses import dataclass
from ..engine.module_interface import NoohtModule

@dataclass
class KTUVector:
    vector: torch.Tensor
    metadata: Dict[str, Any]

class KTUEncoder(NoohtModule):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._device = "cpu"
        self.dim = config.get("ktu_dim", 768)
        
        self.char_norm = nn.RMSNorm(self.dim)
        self.semantic_norm = nn.RMSNorm(self.dim)
        self.structure_norm = nn.RMSNorm(self.dim)
        self.gate = nn.Linear(self.dim * 3, 3)
        self.fusion_proj = nn.Linear(self.dim * 3, self.dim)

    async def initialize(self) -> bool:
        return True

    async def execute(self, inputs: dict) -> dict:
        return inputs

    async def cleanup(self) -> bool:
        return True

    async def encode(self, raw_input: Dict[str, Any]) -> KTUVector:
        char_feat = torch.randn(1, self.dim).to(self._device)
        semantic_feat = torch.randn(1, self.dim).to(self._device)
        structure_feat = torch.randn(1, self.dim).to(self._device)

        char_normed = self.char_norm(char_feat)
        sem_normed = self.semantic_norm(semantic_feat)
        struct_normed = self.structure_norm(structure_feat)

        combined = torch.cat([char_normed, sem_normed, struct_normed], dim=-1)
        weights = torch.softmax(self.gate(combined), dim=-1)
        
        weighted = torch.cat([
            char_normed * weights[:, 0:1],
            sem_normed * weights[:, 1:2],
            struct_normed * weights[:, 2:3]
        ], dim=-1)
        
        vector = self.fusion_proj(weighted)
        return KTUVector(vector=vector, metadata=raw_input)
''')

# ==========================================
# 7. Requirements & README
# ==========================================
write_file("requirements.txt", '''torch>=1.9.0
numpy>=1.19.0
pyyaml>=5.4.0
''')

write_file("README.md", '''# Nooht Architecture v0.2.1

Nooht 不仅是模型架构，而是：
- 独立 AI 架构 + 分布式训练/推理系统
- 不是 Transformer 插件

## Phase 0 (Frozen)
- Engine, Runtime, Scheduler, Memory, Config

## Phase 1 (Scaffold Ready)
- KTU (Knowledge Token Unit)
- HMC (Hierarchical Memory Compression)
- SCM (Semantic Code Memory)

## Run
```bash
python setup_nooht_repo.py
```
''')

print("\n✅ Nooht 项目完整架构已成功生成！")
print("   包含 Phase 0 冻结代码与 Phase 1 接口脚手架。")

# Fix for root-level files
def write_root_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"  Created: {filepath}")

write_root_file("requirements.txt", '''torch>=1.9.0
numpy>=1.19.0
pyyaml>=5.4.0
''')

write_root_file("README.md", '''# Nooht Architecture v0.2.1

Nooht 不仅是模型架构，而是：
- 独立 AI 架构 + 分布式训练/推理系统
- 不是 Transformer 插件

## Phase 0 (Frozen)
- Engine, Runtime, Scheduler, Memory, Config

## Phase 1 (Scaffold Ready)
- KTU (Knowledge Token Unit)
- HMC (Hierarchical Memory Compression)
- SCM (Semantic Code Memory)

## Run
```bash
python setup_nooht_repo.py
```
''')

print("\n✅ Nooht 项目完整架构已成功生成！")
print("   包含 Phase 0 冻结代码与 Phase 1 接口脚手架。")
