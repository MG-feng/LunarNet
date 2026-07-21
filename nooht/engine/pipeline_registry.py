from typing import Dict, Optional, List
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
