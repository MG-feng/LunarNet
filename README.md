
import os

base_dir = "/mnt/agents/output/nooht"

# ============================================================
 README.md
# ============================================================

readme_md = r'''# 🌙 Nooht Framework

**A model-agnostic, extensible cognitive infrastructure for long-term code intelligence.**

[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)](https://github.com/MG-feng/Nooht-by-MG)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-purple)](https://python.org)

> **Nooht does not make models remember more tokens — it gives models a compressible, retrievable, and long-term maintainable code cognition system.**

---

## What is Nooht?

Nooht is a **cognitive infrastructure layer** that sits between any language model and the code it needs to understand. Unlike traditional approaches that rely on ever-larger context windows or parameter counts, Nooht builds an external, structured memory system specifically designed for code comprehension.

### The Problem

Traditional LLMs face fundamental limitations when dealing with code:

- **Context Window Limits** — Large codebases exceed even 128K token windows
- **KV Cache Pressure** — Long contexts consume massive GPU memory
- **Hallucination** — Models forget or misremember code structure across sessions
- **No Persistence** — Context is lost when the conversation ends
- **Relational Blindness** — Models struggle to track function-to-function dependencies across files

### Nooht's Solution

Nooht introduces a **Hierarchical Memory System** that operates independently of any model:

```
Traditional:                    Nooht:

    LLM                            LLM (any model)
     |                                |
     |                                |
  More Params                   Nooht Adapter
     |                                |
  More Context              ┌──────────────────┐
     |                      │ Symbol Memory    │
  Better Performance        │ HMC              │
                            │ SCM              │
                            │ Retrieval        │
                            │ Context Manager  │
                            └──────────────────┘
                                   |
                            DuckDB + FAISS
```

**Key Insight:** Instead of making the model bigger, make its memory smarter.

---

## What Nooht Contains

### 1. Symbol Memory — Structured Code Entity Storage

The atomic unit of Nooht's memory system. Every function, class, variable, and API is stored as a structured `SymbolEntity` with:

- **Identity** — Name, type, signature, file location
- **Relationships** — Dependencies, callers, parent symbols
- **Semantics** — Summary, docstring, parameter types
- **Vectors** — Optional embeddings for similarity search
- **Lifecycle** — Status tracking (active, archived, deprecated)

```python
from nooht import SymbolEntity, SymbolType

entity = SymbolEntity(
    name="authenticate_user",
    type=SymbolType.FUNCTION,
    source="def authenticate_user(creds): ...",
    signature="authenticate_user(credentials: Credentials) -> Token",
    dependencies=["db", "bcrypt", "jwt"],
    summary="Validates credentials and returns JWT token",
    tags=["auth", "security"],
    file_path="src/auth.py",
)
```

### 2. Hierarchical Memory Compression (HMC) — Compression > Deletion

Nooht's core innovation. When memory reaches capacity, it **compresses** before considering deletion:

```
Raw Memory (L0) — Full source, all metadata
    ↓
Summary Memory (L1) — Signature + summary, ~30% size
    ↓
Semantic Memory (L2) — Embedding + key metadata, ~10% size
    ↓
Archive Memory (L3) — Hash + name only, ~1% size
    ↓
Delete — only when all compression exhausted
```

**The Memory Preservation Principle:** Information is degraded gradually, never discarded abruptly.

### 3. Semantic Code Memory (SCM) — Code as Meaning

Converts raw code into semantic structures using rule-based AST analysis:

```python
# Input:
def authenticate(credentials):
    """Validate user credentials and return JWT token."""
    user = db.query(User).filter_by(email=credentials.email).first()
    if not user or not bcrypt.check(credentials.password, user.hash):
        raise AuthError("Invalid credentials")
    return jwt.encode({"sub": user.id}, SECRET)

# Output (CodeSemantic):
{
    "name": "authenticate",
    "type": "function",
    "inputs": ["credentials"],
    "outputs": ["JWT token"],
    "dependencies": ["db", "bcrypt", "jwt"],
    "purpose": "user authentication",
    "complexity": "moderate"
}
```

**No model training required.** All analysis is deterministic and instant.

### 4. Context Manager — Token Budget Intelligence

Dynamic context allocation that respects token limits while maximizing relevance:

| Priority | Content | Eviction Order |
|----------|---------|----------------|
| **CRITICAL** | Current user prompt | Never |
| **HIGH** | Retrieved relevant symbols | Last |
| **MEDIUM** | Working memory history | Third |
| **LOW** | Compressed summaries | Second |
| **ARCHIVE** | Archived fingerprints | First |

```python
from nooht.context.manager import ContextManager, ContextItem, ContextPriority

ctx = ContextManager(max_tokens=4096)
ctx.add(ContextItem(
    id="prompt",
    content="Refactor the auth module...",
    priority=ContextPriority.CRITICAL,
    token_count=20,
    source="current",
))
ctx.compress_if_needed(threshold_ratio=0.9)  # Auto-compress if over budget
```

### 5. Retrieval Engine — Multi-Strategy Search

Unified retrieval supporting multiple strategies:

| Strategy | Method | Best For |
|----------|--------|----------|
| **Embedding** | FAISS vector similarity | Semantic search ("find auth functions") |
| **Keyword** | Inverted index | Exact name matching ("find `login`") |
| **Graph** | Dependency traversal | Relationship queries ("what calls `authenticate`?") |
| **Hybrid** | Weighted fusion | General-purpose retrieval |

### 6. Adapter Layer — Model-Agnostic Bridge

Zero binding to any specific LLM. Current support:

- **TransformersAdapter** — All HuggingFace models (Qwen, DeepSeek, Llama, etc.)
- **CustomAdapter** — Any model implementing the `ModelAdapter` interface
- **Future:** Nightglow-3B native adapter

```python
from nooht.adapters.base import TransformersAdapter

adapter = TransformersAdapter(
    model_name="Qwen/Qwen2.5-Coder-3B",
    device="cuda",
    load_in_4bit=True,  # T4 GPU compatible
)
```

### 7. Pluggable Storage Backends

| Backend | Scale | Persistence | Use Case |
|---------|-------|-------------|----------|
| **InMemory** | < 100K entities | No | Development, testing |
| **DuckDB** | Unlimited | Yes | Production, large repositories |
| **FAISS** | < 10M vectors | Yes | Vector similarity search |

---

## Nooht vs Other Architectures

### vs Traditional LLM Scaling

| Dimension | Traditional LLM | Nooht + Small LLM |
|-----------|-----------------|-------------------|
| **Approach** | Increase parameters | External structured memory |
| **Context** | 128K tokens (max) | Unlimited (hierarchical compression) |
| **GPU Memory** | 80GB+ (A100) | 16GB (T4) |
| **Code Relations** | Implicit in weights | Explicit dependency graph |
| **Persistence** | None across sessions | Persistent DuckDB storage |
| **Hallucination** | High for large repos | Low (retrieval-grounded) |

### vs RAG (Retrieval-Augmented Generation)

| Dimension | RAG | Nooht |
|-----------|-----|-------|
| **Data Unit** | Text chunks | Structured symbols (function/class level) |
| **Understanding** | Shallow (text similarity) | Deep (AST-based semantic analysis) |
| **Compression** | None | Hierarchical (L0→L1→L2→L3) |
| **Relationships** | None | Dependency & caller graphs |
| **Long-term Memory** | Re-index from source | Persistent with intelligent compression |
| **Noise** | High (irrelevant chunks) | Low (structured, tagged, filtered) |

### vs KV Cache Extension

| Dimension | KV Cache | Nooht |
|-----------|----------|-------|
| **Storage** | GPU RAM (volatile) | Disk + RAM (persistent) |
| **Content** | Token activations | Semantic structures |
| **Lifetime** | Single session | Permanent (with compression) |
| **Model Dependency** | Tied to specific model | Model-agnostic |
| **Compression** | Difficult (lossy quantization) | Native (semantic degradation) |
| **Retrieval** | Sequential only | Multi-strategy (embedding, keyword, graph) |

### vs Agent Memory

| Dimension | Agent Memory | Nooht |
|-----------|--------------|-------|
| **Structure** | Unstructured chat logs | Structured code entities |
| **Domain** | General conversation | Code-specific |
| **Compression** | Simple truncation | Hierarchical semantic compression |
| **Retrieval** | Recency-based | Multi-strategy (relevance + recency) |
| **Scope** | Session-level | Repository-level |

---

## ⚡ Quick Start

```bash
pip install nooht
```

```python
from nooht import SymbolMemory, SymbolEntity, SymbolType

# Create a memory instance
memory = SymbolMemory()

# Add a code symbol
entity = SymbolEntity(
    name="authenticate_user",
    type=SymbolType.FUNCTION,
    source="def authenticate_user(creds): ...",
    summary="Validates credentials and returns JWT token",
    tags=["auth", "security"]
)
memory.add(entity)

# Query by tag
results = memory.query(tag="auth", limit=5)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Nightglow / Any LLM               │
├─────────────────────────────────────────────┤
│           Adapter Layer                     │
├─────────────────────────────────────────────┤
│  Context  │  Retrieval  │  Semantic  │ HMC │
├─────────────────────────────────────────────┤
│           Symbol Memory + Store             │
│     (DuckDB / InMemory / FAISS)           │
└─────────────────────────────────────────────┘
```

---

## 📦 Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `Symbol Memory` | Structured code entity storage | ✅ Frozen |
| `Memory Backend` | Pluggable storage (DuckDB / InMemory) | ✅ Frozen |
| `HMC` | Hierarchical Memory Compression | ✅ Frozen |
| `SCM` | Semantic Code Memory | ✅ Frozen |
| `Context Manager` | Token budget & context scheduling | ✅ Frozen |
| `Adapter Layer` | Model-agnostic interface | ✅ Frozen |

---

## 📚 Documentation

- <a href="api-document/ARCHITECTURE.md">Architecture Overview</a> — Core design principles & module relationships
- <a href="api-document/API_REFERENCE.md">API Reference</a> — Complete module API documentation
- <a href="api-document/QUICKSTART.md">Quick Start Guide</a> — Step-by-step tutorial
- <a href="api-document/BACKEND_GUIDE.md">Backend Guide</a> — DuckDB vs InMemory configuration
- <a href="api-document/HMC_GUIDE.md">HMC Guide</a> — Compression levels & policies
- <a href="api-document/ADAPTER_GUIDE.md">Adapter Guide</a> — Integrating custom LLMs
- <a href="api-document/CHANGELOG.md">Changelog</a> — Version history

---

## 🤝 Contributing

Please read our [Contributing Guidelines](.github/CONTRIBUTING.md) and [Security Policy](.github/SECURITY.md) before submitting any pull requests.

---

## 🛡️ Security

For vulnerability reports, see [SECURITY.md](.github/SECURITY.md).

---

## 📄 License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Repository:** https://github.com/MG-feng/Nooht-by-MG
- **Issues:** https://github.com/MG-feng/Nooht-by-MG/issues
- **Discussions:** https://github.com/MG-feng/Nooht-by-MG/discussions

---

<p align="center"><i>Built for Nightglow. Open to all.</i></p>
'''
