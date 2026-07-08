"""Adapters Module — 模型无关接口"""

from .base import ModelAdapter, TransformersAdapter, AdapterFactory, ModelOutput

__all__ = [
    "ModelAdapter",
    "TransformersAdapter",
    "AdapterFactory",
    "ModelOutput",
]
