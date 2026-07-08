
# ============================================================
# 9. api-document/ADAPTER_GUIDE.md
# ============================================================

adapter_guide_md = r'''# Nooht Framework — Adapter Integration Guide

**Version:** 0.1.0-alpha  
**Scope:** Integrating custom LLMs with Nooht through the Adapter Layer

---

## Design Philosophy

The Adapter Layer is Nooht's **model-agnostic bridge**. It ensures that:

1. **Nooht core modules** (`memory/`, `compression/`, `semantic/`, `retrieval/`, `context/`) never import model-specific code
2. **Any LLM** can be integrated by implementing the `ModelAdapter` interface
3. **Future models** (Nightglow, custom transformers, agent systems) require zero changes to core modules

```
┌─────────────────────────────────────────────┐
│           Your LLM (any model)              │
│  ┌─────────────────────────────────────┐   │
│  │  CustomAdapter(ModelAdapter)        │   │
│  │  ├── get_hidden_states()            │   │
│  │  ├── inject_memory()                │   │
│  │  ├── generate()                     │   │
│  │  └── encode()                       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           Nooht Core (unchanged)            │
│  SymbolMemory │ HMC │ SCM │ Retrieval │ ...│
└─────────────────────────────────────────────┘
```

---

## The ModelAdapter Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import torch

class ModelAdapter(ABC):
    """
    Abstract interface for connecting any LLM to Nooht.
    
    All methods must be implemented. No training code belongs here.
    """
    
    @abstractmethod
    def get_hidden_states(
        self,
        input_ids: Any,
        attention_mask: Optional[Any] = None,
        layer_idx: Optional[int] = -1,
        **kwargs
    ) -> torch.Tensor:
        """
        Extract hidden states from a specific layer.
        
        Args:
            input_ids: Tokenized input (model-specific format)
            attention_mask: Attention mask (optional)
            layer_idx: Layer index (-1 = last layer)
        
        Returns:
            torch.Tensor: Hidden states [batch, seq_len, hidden_dim]
        """
        pass
    
    @abstractmethod
    def inject_memory(
        self,
        hidden_states: torch.Tensor,
        memory_embeddings: torch.Tensor,
        **kwargs
    ) -> torch.Tensor:
        """
        Fuse memory embeddings into hidden states.
        
        This is a placeholder for future gated fusion mechanisms.
        Current default: simple addition.
        
        Args:
            hidden_states: Model hidden states
            memory_embeddings: Retrieved memory vectors
        
        Returns:
            torch.Tensor: Fused hidden states
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        input_ids: Any,
        memory_embeddings: Optional[torch.Tensor] = None,
        max_new_tokens: int = 256,
        **kwargs
    ) -> Any:
        """
        Generate text with optional memory injection.
        
        Args:
            input_ids: Tokenized prompt
            memory_embeddings: Optional memory to inject
            max_new_tokens: Generation limit
        
        Returns:
            Model-specific output (token IDs, strings, etc.)
        """
        pass
    
    @abstractmethod
    def encode(self, text: str, **kwargs) -> torch.Tensor:
        """
        Encode text into an embedding vector for retrieval.
        
        Args:
            text: Raw text to encode
        
        Returns:
            torch.Tensor: Embedding vector [1, hidden_dim] or [hidden_dim]
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Return model configuration dict."""
        pass
    
    @abstractmethod
    def get_tokenizer(self) -> Any:
        """Return the tokenizer instance."""
        pass
```

---

## Implementing a Custom Adapter

### Step 1: Inherit from ModelAdapter

```python
from nooht.adapters.base import ModelAdapter
import torch

class MyCustomAdapter(ModelAdapter):
    def __init__(self, model_path: str, device: str = "cuda"):
        self.device = device
        # Load your model here
        self.model = load_my_model(model_path)
        self.tokenizer = load_my_tokenizer(model_path)
        self.hidden_size = self.model.config.hidden_size
    
    def get_hidden_states(self, input_ids, attention_mask=None, layer_idx=-1, **kwargs):
        # Your model's hidden state extraction
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
        )
        return outputs.hidden_states[layer_idx]
    
    def inject_memory(self, hidden_states, memory_embeddings, **kwargs):
        # Simple addition (placeholder for future gated fusion)
        return hidden_states + memory_embeddings.unsqueeze(1)
    
    def generate(self, input_ids, memory_embeddings=None, max_new_tokens=256, **kwargs):
        if memory_embeddings is not None:
            # Your memory injection logic
            pass
        return self.model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            **kwargs
        )
    
    def encode(self, text: str, **kwargs) -> torch.Tensor:
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            hidden = outputs.hidden_states[-1]
            return hidden.mean(dim=1)  # Mean pooling
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "model_path": self.model_path,
            "hidden_size": self.hidden_size,
            "device": self.device,
        }
    
    def get_tokenizer(self):
        return self.tokenizer
```

### Step 2: Register in AdapterFactory

```python
from nooht.adapters.base import AdapterFactory

# Register your adapter
AdapterFactory._registry["my_custom"] = MyCustomAdapter

# Use it
adapter = AdapterFactory.create("my_custom", model_path="/path/to/model")
```

---

## Existing Adapters

### TransformersAdapter

**Module:** `nooht.adapters.base`  
**Supports:** All HuggingFace Transformers models

```python
from nooht.adapters.base import TransformersAdapter

adapter = TransformersAdapter(
    model_name="Qwen/Qwen2.5-Coder-3B",
    device="cuda",
    load_in_4bit=True,  # For T4 GPU compatibility
)

# Encode for retrieval
embedding = adapter.encode("def authenticate_user(credentials):")

# Get config
config = adapter.get_config()
# {
#   'model_name': 'Qwen/Qwen2.5-Coder-3B',
#   'hidden_size': 2048,
#   'vocab_size': 151936,
#   'num_layers': 36,
#   'num_heads': 16
# }
```

### NightglowAdapter (Future)

```python
from nooht.adapters.base import AdapterFactory

# Planned for v1.0
adapter = AdapterFactory.create("nightglow", model_path="nightglow-3b")
```

---

## Integration Patterns

### Pattern 1: Retrieval-Augmented Generation

```python
from nooht import SymbolMemory
from nooht.memory.vector_store import FAISSVectorStore
from nooht.adapters.base import TransformersAdapter

# Initialize
memory = SymbolMemory()
vector_store = FAISSVectorStore(dimension=768)
adapter = TransformersAdapter("Qwen/Qwen2.5-Coder-3B")

# User query
query = "How do I implement JWT authentication?"

# Encode query
query_embedding = adapter.encode(query)

# Retrieve relevant symbols
results = vector_store.search(query_embedding.numpy(), top_k=5)

# Build context
context = "\n".join([
    f"Function: {meta['name']}\nSummary: {meta.get('summary', 'N/A')}"
    for _, meta in results
])

# Generate with context
prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
inputs = adapter.get_tokenizer()(prompt, return_tensors="pt")
output = adapter.generate(inputs.input_ids, max_new_tokens=256)
```

### Pattern 2: Memory-Injected Generation

```python
# Retrieve memory embeddings
memory_embeddings = retrieve_relevant_embeddings(query)

# Inject into generation
output = adapter.generate(
    input_ids=inputs.input_ids,
    memory_embeddings=memory_embeddings,
    max_new_tokens=256,
)
```

### Pattern 3: Context-Aware Completion

```python
from nooht.context.manager import ContextManager, ContextItem, ContextPriority

ctx = ContextManager(max_tokens=4096)

# Add current code
ctx.add(ContextItem(
    id="current_file",
    content=current_source_code,
    priority=ContextPriority.CRITICAL,
    token_count=estimate_tokens(current_source_code),
    source="current",
))

# Add retrieved symbols
for symbol in retrieved:
    ctx.add(ContextItem(
        id=symbol.id,
        content=symbol.summary,
        priority=ContextPriority.HIGH,
        token_count=20,
        source="retrieved",
    ))

# Compress if needed
ctx.compress_if_needed(threshold_ratio=0.9)

# Build prompt from allocated context
context_text = "\n".join(item.content for item in ctx.context)
prompt = f"{context_text}\n\n# Complete the following code:\n{partial_code}"
```

---

## Adapter Requirements Checklist

Before submitting a new adapter, ensure:

- [ ] Implements all `ModelAdapter` abstract methods
- [ ] `encode()` returns a 1D or 2D tensor (mean-pooled)
- [ ] `get_hidden_states()` supports `layer_idx` parameter
- [ ] `generate()` accepts `max_new_tokens` and optional `memory_embeddings`
- [ ] No training code (LoRA, Trainer, etc.) in the adapter
- [ ] No hard-coded model paths (use constructor parameters)
- [ ] Type hints on all public methods
- [ ] Docstrings for all public methods
- [ ] Unit tests for `encode()` and `get_hidden_states()`

---

## Common Pitfalls

### ❌ Importing torch in Core Modules

```python
# WRONG — core modules must remain model-agnostic
# nooht/memory/symbol_memory.py
import torch  # ❌ NEVER do this
```

### ❌ Hard-Coding Model Names

```python
# WRONG
class BadAdapter(ModelAdapter):
    def __init__(self):
        self.model = AutoModel.from_pretrained("Qwen/Qwen2.5-Coder-3B")  # ❌ Hard-coded
```

### ❌ Training Code in Adapter

```python
# WRONG — adapters are inference-only
class BadAdapter(ModelAdapter):
    def train(self, dataset):  # ❌ Out of scope
        ...
    def fine_tune(self):  # ❌ Out of scope
        ...
```

### ✅ Correct Implementation

```python
# CORRECT
class GoodAdapter(ModelAdapter):
    def __init__(self, model_name: str, device: str = "cuda"):
        self.model = AutoModel.from_pretrained(model_name)  # ✅ Parameterized
        self.device = device
```

---

## Testing Your Adapter

```python
import pytest
from nooht.adapters.base import ModelAdapter

class TestMyAdapter:
    def test_encode_returns_tensor(self):
        adapter = MyAdapter("test-model")
        embedding = adapter.encode("def test(): pass")
        assert isinstance(embedding, torch.Tensor)
        assert embedding.dim() in [1, 2]
    
    def test_get_hidden_states_shape(self):
        adapter = MyAdapter("test-model")
        inputs = adapter.get_tokenizer()("test", return_tensors="pt")
        hidden = adapter.get_hidden_states(inputs.input_ids)
        assert hidden.dim() == 3  # [batch, seq, hidden]
    
    def test_generate_output(self):
        adapter = MyAdapter("test-model")
        inputs = adapter.get_tokenizer()("def ", return_tensors="pt")
        output = adapter.generate(inputs.input_ids, max_new_tokens=10)
        assert output is not None
```

---

<p align="center"><i>For core architecture questions, see <a href="ARCHITECTURE.md">Architecture Overview</a></i></p>
'''
