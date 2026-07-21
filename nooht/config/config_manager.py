import os
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
