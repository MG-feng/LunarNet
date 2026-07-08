
# ============================================================
# 4. ARCHITECTURE.md
# ============================================================

architecture_md = r'''# Nooht Framework — Architecture Overview

**Version:** 0.1.0-alpha  
**Last Updated:** 2026-07-08  
**Status:** Architecture Approved

---

## 1. Design Philosophy

### 1.1 Core Principle: Model-Agnostic Infrastructure

Nooht is **not** a language model. It is a **cognitive infrastructure layer** that sits between any LLM and the code it needs to understand.

```
Traditional Approach:          Nooht Approach:

    LLM                         LLM (any model)
     |                              |
     |                              |
  More Params                  Nooht Adapter
     |                              |
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

### 1.2 Memory Preservation Principle

> **Compression is always preferred over deletion.**

```
Raw Memory
    ↓
Compress L1 (Summary)
    ↓
Compress L2 (Semantic)
    ↓
Compress L3 (Archive)
    ↓
Delete (last resort only)
```

This principle is **non-negotiable** and enforced at the architecture level.

### 1.3 Separation of Concerns

| Layer | Responsibility | Must NOT Do |
|-------|---------------|-------------|
| **Memory** | Store and retrieve symbols | Model inference |
| **Compression** | Compress memories hierarchically | Delete without compression attempt |
| **Semantic** | Extract code semantics | Execute code |
| **Retrieval** | Find relevant symbols | Modify stored data |
| **Context** | Manage token budgets | Generate text |
| **Adapter** | Bridge to any LLM | Store business logic |

---

## 2. Module Architecture

### 2.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Application Layer                           │
│    (IDE Plugin, Agent, CLI Tool, Nightglow Model, etc.)           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Adapter Layer                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ModelAdapter (ABC)                                         │   │
│  │  ├── TransformersAdapter (HuggingFace)                      │   │
│  │  ├── CustomAdapter (Nightglow future)                      │   │
│  │  └── ... (extensible)                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Orchestration Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │   Context   │  │  Retrieval  │  │    Semantic Code        │   │
│  │   Manager   │──│   Engine    │──│    Memory (SCM)         │   │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘   │
│         │                │                    │                     │
│         ▼                ▼                    ▼                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │           Hierarchical Memory Compression (HMC)             │   │
│  │  L0_RAW → L1_SUMMARY → L2_SEMANTIC → L3_ARCHIVE           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Storage Layer                                │
│  ┌─────────────────────────┐  ┌───────────────────────────────┐   │
│  │    Symbol Memory        │  │      Vector Store             │   │
│  │  ┌─────────────────┐   │  │  ┌─────────────────────────┐  │   │
│  │  │ MemoryBackend   │   │  │  │ VectorStore (ABC)       │  │   │
│  │  │ ├── InMemory    │   │  │  │ ├── FAISSVectorStore    │  │   │
│  │  │ └── DuckDB      │   │  │  │ └── ... (extensible)    │  │   │
│  │  └─────────────────┘   │  │  └─────────────────────────┘  │   │
│  └─────────────────────────┘  └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
1. INGESTION
   Code Repository
        │
        ▼
   Tree-sitter / AST Parser
        │
        ▼
   SymbolEntity (structured)
        │
        ├──→ SymbolMemory (DuckDB/InMemory)
        └──→ FAISSVectorStore (embeddings)

2. RETRIEVAL
   Query (code snippet or natural language)
        │
        ├──→ KeywordRetriever (name matching)
        ├──→ EmbeddingRetriever (FAISS similarity)
        └──→ GraphRetriever (dependency traversal)
        │
        ▼
   Hybrid fusion → Top-K results
        │
        ▼
   ContextManager (token budget allocation)
        │
        ▼
   Adapter.inject_memory() → LLM

3. COMPRESSION (background)
   SymbolMemory.iter_all()
        │
        ▼
   HMCController (age-based trigger)
        │
        ├──→ L0→L1 (signature + summary)
        ├──→ L1→L2 (embedding + key metadata)
        └──→ L2→L3 (hash + name only)
        │
        ▼
   vacuum() (physical delete tombstones)
```

---

## 3. Core Modules

### 3.1 Symbol Memory (`nooht/memory/`)

**Purpose:** Atomic storage for code entities.

**Key Classes:**

| Class | Role |
|-------|------|
| `SymbolEntity` | Data model — the atomic unit of memory |
| `SymbolMemory` | Business logic — CRUD + query facade |
| `MemoryBackend` | Storage abstraction |
| `InMemoryBackend` | Small-scale, fast, non-persistent |
| `DuckDBBackend` | Large-scale, persistent, SQL-powered |
| `VectorStore` | Embedding storage abstraction |
| `FAISSVectorStore` | CPU-optimized similarity search |

**Entity Lifecycle:**

```
Create → Active → [Compressed L1/L2/L3] → Archived → Tombstone → Deleted
```

### 3.2 Hierarchical Memory Compression (`nooht/compression/`)

**Purpose:** Preserve memory through progressive compression.

**Compression Levels:**

| Level | Name | Content | Size Ratio |
|-------|------|---------|------------|
| L0 | Raw | Full source, docstring, metadata | 1.0x |
| L1 | Summary | Signature, summary, file location | ~0.3x |
| L2 | Semantic | Embedding, key deps, name | ~0.1x |
| L3 | Archive | Hash, name, timestamp | ~0.01x |

**Trigger Policy:**

```python
if len(raw_memories) > max_raw_count:
    compress_oldest_20_percent_to_next_level()
```

### 3.3 Semantic Code Memory (`nooht/semantic/`)

**Purpose:** Convert code into semantic structures.

**Rule-Based Analysis:**

```python
def login(user, password):
    """Authenticate user and return JWT."""
    ...

# → CodeSemantic:
{
    "name": "login",
    "type": "function",
    "inputs": ["user", "password"],
    "outputs": ["JWT token"],
    "purpose": "user authentication",
    "dependencies": ["bcrypt", "database"],
    "complexity": "moderate"
}
```

**No model training required.** All analysis is AST-based with heuristic rules.

### 3.4 Context Manager (`nooht/context/`)

**Purpose:** Dynamic token budget management.

**Priority Tiers:**

| Priority | Content | Eviction Order |
|----------|---------|----------------|
| CRITICAL | Current user prompt | Never |
| HIGH | Retrieved relevant symbols | Last |
| MEDIUM | Working memory history | Third |
| LOW | Compressed summaries | Second |
| ARCHIVE | Archived fingerprints | First |

**Allocation Algorithm:**

```
1. Reserve tokens for CRITICAL items
2. Fill HIGH priority until budget exhausted
3. If overflow, trigger compression of lowest active tier
4. If still overflow, archive oldest items
5. Delete only if all compression exhausted
```

### 3.5 Retrieval (`nooht/retrieval/`)

**Purpose:** Multi-strategy symbol retrieval.

**Strategies:**

| Strategy | Use Case | Backend |
|----------|----------|---------|
| `Embedding` | Semantic similarity | FAISS |
| `Keyword` | Exact name matching | Inverted index |
| `Graph` | Dependency traversal | SymbolMemory relations |
| `Hybrid` | Combined ranking | All above |

**Fusion Formula:**

```
score_hybrid = w_embed * score_embed + w_keyword * score_keyword + w_graph * score_graph
```

Default weights: `[0.5, 0.3, 0.2]`

### 3.6 Adapter Layer (`nooht/adapters/`)

**Purpose:** Model-agnostic bridge.

**Interface:**

```python
class ModelAdapter(ABC):
    def get_hidden_states(...) -> Tensor
    def inject_memory(...) -> Tensor        # Gated fusion placeholder
    def generate(...) -> Tensor
    def encode(...) -> Tensor               # For retrieval embedding
```

**Current Implementation:**

- `TransformersAdapter` — HuggingFace models (no training code)

**Future:**

- `NightglowAdapter` — Custom transformer
- `AgentAdapter` — Multi-agent systems

---

## 4. Design Decisions

### 4.1 Why DuckDB over SQLite?

| Factor | DuckDB | SQLite |
|--------|--------|--------|
| Columnar storage | ✅ | ❌ |
| Vectorized scan | ✅ | ❌ |
| LIST type support | ✅ | ❌ (JSON only) |
| Analytical queries | ✅ | ⚠️ |
| Embedded | ✅ | ✅ |
| Thread safety | ⚠️ (handled) | ✅ |

DuckDB's columnar architecture is optimal for batch analytics (compression, statistics, export).

### 4.2 Why FAISS over Vector DBs?

| Factor | FAISS | Milvus/Qdrant |
|--------|-------|---------------|
| Zero dependencies | ✅ (pip install) | ❌ (server) |
| Embedding in same process | ✅ | ❌ (RPC) |
| T4 GPU compatible | ✅ | ❌ |
| Index rebuild cost | Low | High |
| Production scale | < 10M vectors | Unlimited |

For Nooht's target (repo-level, ~100K symbols), FAISS is sufficient and simpler.

### 4.3 Why Rule-Based SCM?

- **Speed:** No model loading, instant analysis
- **Determinism:** Same code → same semantic structure
- **Portability:** No GPU required
- **Extensibility:** Easy to add new language rules

Future versions may add optional neural SCM as a plugin.

---

## 5. Extension Points

### 5.1 Adding a New Backend

```python
class RedisBackend(MemoryBackend):
    def insert(self, entity: SymbolEntity) -> str: ...
    def get(self, entity_id: str) -> Optional[SymbolEntity]: ...
    # ... implement all abstract methods

# Register
SymbolMemory(backend=RedisBackend(...))
```

### 5.2 Adding a New Retriever

```python
class ASTRetriever(Retriever):
    def retrieve(self, query, top_k=5): ...

# Use in hybrid
hybrid = HybridRetriever(
    retrievers=[EmbeddingRetriever(), ASTRetriever()],
    weights=[0.6, 0.4]
)
```

### 5.3 Adding a New Adapter

```python
class ONNXAdapter(ModelAdapter):
    def get_hidden_states(self, ...): ...
    # ... implement all abstract methods

AdapterFactory.create("onnx", model_path="...")
```

---

## 6. Performance Characteristics

### 6.1 DuckDB Backend (1M Entities)

| Operation | Latency | Notes |
|-----------|---------|-------|
| `insert()` | ~2ms | Single row |
| `get()` | ~1ms | Primary key lookup |
| `query(tag=...)` | ~5ms | list_contains + SIMD |
| `get_callers()` | ~8ms | list_contains on callers |
| `search_by_source()` | ~50-200ms | LIKE full scan (expected) |
| `count()` | ~1ms | Index-optimized |
| `iter_all(1000)` | ~20ms/batch | Sequential scan |

### 6.2 FAISS Vector Store (100K vectors, 768-dim)

| Operation | Latency | Notes |
|-----------|---------|-------|
| `add(1000 vectors)` | ~50ms | Batch add |
| `search(top_k=5)` | ~2ms | Brute-force (FlatIP) |
| `save()` | ~100ms | Disk write |
| `load()` | ~200ms | Disk read |

### 6.3 Memory Footprint

| Component | 100K Entities | 1M Entities |
|-----------|---------------|-------------|
| DuckDB (disk) | ~50MB | ~500MB |
| DuckDB (RAM) | ~30MB | ~100MB |
| FAISS index | ~300MB | ~3GB |
| InMemoryBackend | ~500MB | N/A (not recommended) |

---

## 7. Future Roadmap

### v0.2 (Beta)

- [ ] Online Symbol Memory (incremental updates)
- [ ] Memory rewrite / consolidation
- [ ] IDE integration (LSP-like protocol)
- [ ] Multi-repo support

### v0.3 (Future)

- [ ] Continuous learning
- [ ] Dynamic memory graph
- [ ] Tool calling integration
- [ ] Distributed memory

### v1.0 (Nightglow Integration)

- [ ] Nightglow-3B native adapter
- [ ] End-to-end training pipeline
- [ ] Production deployment guides

---

## 8. Glossary

| Term | Definition |
|------|------------|
| **Symbol** | A named code entity (function, class, variable, etc.) |
| **Entity** | A `SymbolEntity` instance — the atomic memory unit |
| **HMC** | Hierarchical Memory Compression |
| **SCM** | Semantic Code Memory |
| **Tombstone** | Soft-delete marker — entity logically deleted but physically present |
| **Vacuum** | Physical deletion of tombstoned records |
| **Adapter** | Bridge between Nooht and any LLM |
| **Retriever** | Strategy for finding relevant symbols |

---

