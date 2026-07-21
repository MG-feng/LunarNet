import asyncio
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
