"""
Adapter Layer — 模型无关接口
设计原则：任何模型（Transformers / Custom）都可以通过 Adapter 接入 Nooht
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field

try:
    import torch
except ImportError:
    torch = None


@dataclass
class ModelOutput:
    """标准化模型输出"""
    logits: Optional[Any] = None
    hidden_states: Optional[List[Any]] = None
    attention: Optional[List[Any]] = None
    loss: Optional[Any] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class ModelAdapter(ABC):
    """模型适配器 — 统一接口"""
    
    @abstractmethod
    def get_hidden_states(
        self,
        input_ids: Any,
        attention_mask: Optional[Any] = None,
        layer_idx: Optional[int] = -1,
        **kwargs
    ) -> Any:
        """获取指定层的隐藏状态"""
        pass
    
    @abstractmethod
    def inject_memory(
        self,
        hidden_states: Any,
        memory_embeddings: Any,
        **kwargs
    ) -> Any:
        """注入记忆到隐藏状态"""
        pass
    
    @abstractmethod
    def generate(
        self,
        input_ids: Any,
        memory_embeddings: Optional[Any] = None,
        max_new_tokens: int = 256,
        **kwargs
    ) -> Any:
        """生成输出"""
        pass
    
    @abstractmethod
    def encode(self, text: str, **kwargs) -> Any:
        """编码文本（用于检索）"""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        pass
    
    @abstractmethod
    def get_tokenizer(self) -> Any:
        """获取 tokenizer"""
        pass


class TransformersAdapter(ModelAdapter):
    """
    HuggingFace Transformers 适配器
    支持所有 HF 模型
    """
    
    def __init__(
        self,
        model_name: str,
        device: str = "cuda",
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
        **kwargs
    ):
        if torch is None:
            raise ImportError("PyTorch is required for TransformersAdapter")
        
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        self.model_name = model_name
        self.device = device
        
        load_kwargs = {"device_map": device}
        if load_in_8bit:
            load_kwargs["load_in_8bit"] = True
        if load_in_4bit:
            load_kwargs["load_in_4bit"] = True
        
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.config = self.model.config
        self.hidden_size = self.config.hidden_size
        
        self._fusion_layer = None
    
    def get_hidden_states(
        self,
        input_ids: Any,
        attention_mask: Optional[Any] = None,
        layer_idx: Optional[int] = -1,
        **kwargs
    ) -> Any:
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
            return_dict=True,
            **kwargs
        )
        if layer_idx == -1:
            return outputs.hidden_states[-1]
        return outputs.hidden_states[layer_idx]
    
    def inject_memory(
        self,
        hidden_states: Any,
        memory_embeddings: Any,
        fusion_layer: Optional[Any] = None,
        **kwargs
    ) -> Any:
        if fusion_layer is None:
            if hasattr(memory_embeddings, "unsqueeze"):
                return hidden_states + memory_embeddings.unsqueeze(1)
            return hidden_states + memory_embeddings
        return fusion_layer(hidden_states, memory_embeddings)
    
    def generate(
        self,
        input_ids: Any,
        memory_embeddings: Optional[Any] = None,
        max_new_tokens: int = 256,
        **kwargs
    ) -> Any:
        return self.model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            **kwargs
        )
    
    def encode(self, text: str, **kwargs) -> Any:
        inputs = self.tokenizer(text, return_tensors="pt", **kwargs)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            hidden = outputs.hidden_states[-1]
            embedding = hidden.mean(dim=1)
        
        return embedding
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "hidden_size": self.hidden_size,
            "vocab_size": self.config.vocab_size,
            "num_layers": getattr(self.config, "num_hidden_layers", None),
            "num_heads": getattr(self.config, "num_attention_heads", None),
            "adapter_type": "transformers",
        }
    
    def get_tokenizer(self) -> Any:
        return self.tokenizer


class AdapterFactory:
    """适配器工厂"""
    
    @staticmethod
    def create(adapter_type: str, **kwargs) -> ModelAdapter:
        if adapter_type == "transformers":
            return TransformersAdapter(**kwargs)
        elif adapter_type == "transformers_8bit":
            return TransformersAdapter(load_in_8bit=True, **kwargs)
        elif adapter_type == "transformers_4bit":
            return TransformersAdapter(load_in_4bit=True, **kwargs)
        else:
            raise ValueError(f"Unsupported adapter type: {adapter_type}")
