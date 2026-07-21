import torch
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
