
import os
base_dir = "/mnt/agents/output/nooht"

# ============================================================
# 5. api-document/API_REFERENCE.md
# ============================================================

api_reference_md = r'''# Nooht Framework — API Reference

**Version:** 0.1.0-alpha  
**Last Updated:** 2026-07-08

---

## Table of Contents

- [SymbolEntity](#symbolentity)
- [SymbolMemory](#symbolmemory)
- [MemoryBackend](#memorybackend)
- [InMemoryBackend](#inmemorybackend)
- [DuckDBBackend](#duckdbbackend)
- [VectorStore](#vectorstore)
- [FAISSVectorStore](#faissvectorstore)
- [HMCController](#hmccontroller)
- [SemanticCodeMemory](#semanticcodememory)
- [ContextManager](#contextmanager)
- [ModelAdapter](#modeladapter)
- [TransformersAdapter](#transformersadapter)

---

## SymbolEntity

**Module:** `nooht.memory.symbol_entity`  
**Purpose:** The atomic data unit of the Nooht framework.

### Constructor

```python
SymbolEntity(
    id: str = uuid4(),
    name: str = "",
    type: SymbolType = SymbolType.FUNCTION,
    source: str = "",
    file_path: str = "",
    line_start: int = 0,
    line_end: int = 0,
    signature: str = "",
    docstring: str = "",
    parameters: List[str] = [],
    return_type: str = "",
    dependencies: List[str] = [],
    callers: List[str] = [],
    parent_id: Optional[str] = None,
    summary: str = "",
    embedding: Optional[List[float]] = None,
    semantic_hash: str = "",
    status: SymbolStatus = SymbolStatus.ACTIVE,
    created_at: str = iso_timestamp(),
    updated_at: str = iso_timestamp(),
    access_count: int = 0,
    last_accessed: Optional[str] = None,
    metadata: Dict[str, Any] = {},
    tags: List[str] = [],
)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `touch()` | `() -> None` | Increment `access_count` and update `last_accessed` |
| `to_dict()` | `() -> Dict[str, Any]` | Serialize to dictionary |
| `from_dict()` | `(data: Dict) -> SymbolEntity` | Class method — deserialize from dictionary |

### Example

```python
from nooht import SymbolEntity, SymbolType, SymbolStatus

entity = SymbolEntity(
    name="authenticate",
    type=SymbolType.FUNCTION,
    source="def authenticate(creds): ...",
    signature="authenticate(creds: Credentials) -> Token",
    parameters=["creds"],
    return_type="Token",
    dependencies=["bcrypt", "jwt"],
    summary="Validates credentials and returns JWT",
    tags=["auth", "security"],
)
```

---

## SymbolMemory

**Module:** `nooht.memory.symbol_memory`  
**Purpose:** Business logic facade for symbol CRUD and querying.

### Constructor

```python
SymbolMemory(backend: Optional[MemoryBackend] = None)
```

- `backend`: Storage backend. Defaults to `InMemoryBackend()`.

### Methods

#### CRUD

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `add()` | `(entity: SymbolEntity) -> str` | `str` (entity_id) | Insert entity |
| `get()` | `(entity_id: str) -> Optional[SymbolEntity]` | `SymbolEntity | None` | Retrieve by ID (auto-increments access_count) |
| `update()` | `(entity_id: str, updates: Dict[str, Any]) -> bool` | `bool` | Update fields |
| `remove()` | `(entity_id: str) -> bool` | `bool` | Soft-delete (tombstone) |
| `exists()` | `(entity_id: str) -> bool` | `bool` | Check existence |

#### Query

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `query()` | `(name, type, tag, parent_id, status, limit=100, offset=0) -> List[SymbolEntity]` | `List[SymbolEntity]` | Multi-condition query with pagination |
| `count()` | `(**filters) -> int` | `int` | Count matching entities |
| `search_by_source()` | `(pattern: str, limit=100) -> List[SymbolEntity]` | `List[SymbolEntity]` | Substring search in source code |
| `get_by_repo()` | `(repo_prefix: str, limit=1000) -> List[SymbolEntity]` | `List[SymbolEntity]` | Filter by file path prefix |
| `get_dependencies()` | `(entity_id: str, limit=50) -> List[SymbolEntity]` | `List[SymbolEntity]` | Resolve dependency IDs to entities |
| `get_callers()` | `(entity_id: str, limit=50) -> List[SymbolEntity]` | `List[SymbolEntity]` | Find entities that depend on this one |

#### Utility

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `update_access()` | `(entity_id: str) -> None` | `None` | Manually bump access counter |
| `stats()` | `() -> Dict[str, Any]` | `dict` | Storage statistics |
| `iter_all()` | `(batch_size=1000) -> Iterator[List[SymbolEntity]]` | `Iterator` | Batch iterate all entities |
| `close()` | `() -> None` | `None` | Release backend resources |

### Example

```python
from nooht import SymbolMemory, DuckDBBackend

# Use DuckDB for production
memory = SymbolMemory(backend=DuckDBBackend("nooht.db"))

# Add entity
eid = memory.add(entity)

# Query by tag
results = memory.query(tag="auth", limit=10)

# Get statistics
print(memory.stats())
# {'total_entities': 150000, 'by_type': {'function': 120000, ...}, ...}

memory.close()
```

---

## MemoryBackend

**Module:** `nooht.memory.backend`  
**Purpose:** Abstract interface for all storage backends.

### Abstract Methods

All backends must implement:

```python
insert(entity: SymbolEntity) -> str
get(entity_id: str) -> Optional[SymbolEntity]
update(entity_id: str, updates: Dict[str, Any]) -> bool
delete(entity_id: str) -> bool
query(name, type, tag, parent_id, status, limit, offset) -> List[SymbolEntity]
count(**filters) -> int
search_by_source(pattern: str, limit: int) -> List[SymbolEntity]
get_by_repo(repo_prefix: str, limit: int) -> List[SymbolEntity]
get_dependencies(entity_id: str, limit: int) -> List[SymbolEntity]
get_callers(entity_id: str, limit: int) -> List[SymbolEntity]
update_access(entity_id: str) -> None
stats() -> Dict[str, Any]
iter_all(batch_size: int) -> Iterator[List[SymbolEntity]]
close() -> None
```

---

## InMemoryBackend

**Module:** `nooht.memory.backend`  
**Purpose:** Fast, non-persistent backend for < 100K entities.

### Constructor

```python
InMemoryBackend()
```

### Characteristics

| Property | Value |
|----------|-------|
| Persistence | No (data lost on process exit) |
| Capacity | ~100,000 entities |
| Memory usage | ~500MB @ 100K entities |
| Thread safety | No (single-threaded only) |
| Query latency | < 1ms |

### Example

```python
from nooht.memory.backend import InMemoryBackend

backend = InMemoryBackend()
memory = SymbolMemory(backend=backend)
```

---

## DuckDBBackend

**Module:** `nooht.memory.backend`  
**Purpose:** Production-grade, persistent backend for unlimited entities.

### Constructor

```python
DuckDBBackend(db_path: str = ":memory:")
```

- `db_path`: Database file path. Use `:memory:` for ephemeral storage.

### Characteristics

| Property | Value |
|----------|-------|
| Persistence | Yes (file-based) |
| Capacity | Unlimited (columnar storage) |
| Memory usage | ~100MB @ 1M entities |
| Thread safety | Yes (thread-local connections) |
| Query latency | < 10ms @ 1M entities |

### Additional Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `vacuum()` | `() -> int` | Physically delete tombstoned records. Returns deletion count. |

### Example

```python
from nooht.memory.backend import DuckDBBackend

# Persistent storage
backend = DuckDBBackend("project_memory.db")

# Ephemeral (testing)
backend = DuckDBBackend(":memory:")
```

---

## VectorStore

**Module:** `nooht.memory.vector_store`  
**Purpose:** Abstract interface for vector similarity storage.

### Abstract Methods

```python
add(vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None
search(query: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]
remove(ids: List[str]) -> None
save(path: str) -> None
load(path: str) -> None
stats() -> Dict[str, Any]
```

---

## FAISSVectorStore

**Module:** `nooht.memory.vector_store`  
**Purpose:** CPU-optimized vector similarity search.

### Constructor

```python
FAISSVectorStore(dimension: int, metric: str = "cosine")
```

- `dimension`: Embedding vector dimension (e.g., 768 for UniXcoder)
- `metric`: Distance metric. `"cosine"` uses inner product with L2 normalization.

### Additional Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `mark_tombstone()` | `(entity_id: str) -> None` | Soft-delete filter for search results |
| `vacuum()` | `() -> int` | Rebuild index excluding tombstones |

### Example

```python
import numpy as np
from nooht.memory.vector_store import FAISSVectorStore

store = FAISSVectorStore(dimension=768)

# Add vectors
vectors = np.random.randn(100, 768).astype(np.float32)
metadata = [{"id": f"entity_{i}", "name": f"func_{i}"} for i in range(100)]
store.add(vectors, metadata)

# Search
query = np.random.randn(768).astype(np.float32)
results = store.search(query, top_k=5)
# [(0.95, {"id": "entity_42", "name": "func_42"}), ...]
```

---

## HMCController

**Module:** `nooht.compression.hmc`  
**Purpose:** Manage memory lifecycle through hierarchical compression.

### Constructor

```python
HMCController(
    compressor: Optional[CompressionStrategy] = None,
    max_raw_count: int = 10000,
    max_summary_count: int = 50000,
    max_semantic_count: int = 100000,
    archive_after_days: int = 90,
)
```

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `add_memory()` | `(symbol, initial_level=MemoryLevel.L0_RAW) -> str` | `str` (compressed_id) | Add symbol to compression pipeline |
| `get_memory()` | `(memory_id: str) -> Optional[CompressedMemory]` | `CompressedMemory | None` | Retrieve compressed memory |
| `stats()` | `() -> Dict[str, int]` | `dict` | Count per level |
| `force_archive_old()` | `(days_threshold: Optional[int]) -> int` | `int` | Archive memories older than threshold |

### Compression Levels

```python
class MemoryLevel(IntEnum):
    L0_RAW = 0       # Full source
    L1_SUMMARY = 1   # Signature + summary
    L2_SEMANTIC = 2  # Embedding + key metadata
    L3_ARCHIVE = 3   # Hash + name only
```

### Example

```python
from nooht.compression.hmc import HMCController, MemoryLevel
from nooht import SymbolEntity, SymbolType

hmc = HMCController(max_raw_count=1000)

entity = SymbolEntity(
    name="process_data",
    type=SymbolType.FUNCTION,
    source="def process_data(raw): ..." * 100,  # Long content
)

cid = hmc.add_memory(entity, MemoryLevel.L0_RAW)

# Check stats
print(hmc.stats())
# {'raw': 1, 'summary': 0, 'semantic': 0, 'archive': 0, 'total': 1}

# Trigger compression by adding many more...
```

---

## SemanticCodeMemory

**Module:** `nooht.semantic.scm`  
**Purpose:** Convert code into semantic structures (rule-based, no training).

### Constructor

```python
SemanticCodeMemory()
```

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `analyze_and_store()` | `(code: str, entity_id: str, entity_type="function") -> CodeSemantic` | `CodeSemantic` | Parse code and store semantic structure |
| `get()` | `(entity_id: str) -> Optional[CodeSemantic]` | `CodeSemantic | None` | Retrieve stored semantic |
| `find_by_name()` | `(name: str) -> List[CodeSemantic]` | `List[CodeSemantic]` | Find by symbol name |
| `find_by_purpose()` | `(purpose_keyword: str) -> List[CodeSemantic]` | `List[CodeSemantic]` | Search purpose descriptions |
| `to_dict()` | `() -> Dict[str, Dict]` | `dict` | Export all semantics |

### CodeSemantic Structure

```python
@dataclass
class CodeSemantic:
    name: str
    entity_type: str          # "function", "class", "method", "module"
    inputs: List[str]         # Parameter names / base classes
    outputs: List[str]        # Return types / method names
    dependencies: List[str]   # Imported modules
    purpose: str              # Inferred or extracted description
    key_operations: List[str] # Function calls within the code
    complexity_estimate: str  # "simple", "moderate", "complex"
    raw_code: str             # Truncated original source
```

### Example

```python
from nooht.semantic.scm import SemanticCodeMemory

scm = SemanticCodeMemory()

code = """
def authenticate(credentials):
    \"\"\"Validate user credentials and return JWT token.\"\"\"
    user = db.query(User).filter_by(email=credentials.email).first()
    if not user or not bcrypt.check(credentials.password, user.hash):
        raise AuthError("Invalid credentials")
    return jwt.encode({"sub": user.id}, SECRET)
"""

semantic = scm.analyze_and_store(code, entity_id="auth_001", entity_type="function")

print(semantic.to_dict())
# {
#   "name": "authenticate",
#   "type": "function",
#   "inputs": ["credentials"],
#   "outputs": ["jwt.encode(...)"],
#   "dependencies": ["db", "bcrypt", "jwt"],
#   "purpose": "user authentication",
#   "key_operations": ["query", "filter_by", "check", "encode"],
#   "complexity": "moderate"
# }
```

---

## ContextManager

**Module:** `nooht.context.manager`  
**Purpose:** Dynamic token budget management and context scheduling.

### Constructor

```python
ContextManager(max_tokens: int = 8192)
```

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `set_token_counter()` | `(counter_fn: Callable) -> None` | `None` | Inject custom tokenizer |
| `allocate_context()` | `(items: List[ContextItem]) -> Tuple[List[ContextItem], bool]` | `(items, overflow)` | Select best combination within budget |
| `compress_if_needed()` | `(threshold_ratio=0.9) -> List[ContextItem]` | `List[ContextItem]` | Compress when usage exceeds threshold |
| `retrieve_memory()` | `(query: str, top_k=3) -> List[ContextItem]` | `List[ContextItem]` | Keyword-based context retrieval |
| `remove_redundancy()` | `() -> List[ContextItem]` | `List[ContextItem]` | Remove duplicate content |
| `add()` | `(item: ContextItem) -> None` | `None` | Add item with auto-overflow check |
| `clear()` | `() -> None` | `None` | Clear all context |
| `stats()` | `() -> Dict[str, Any]` | `dict` | Usage statistics |

### ContextItem

```python
@dataclass
class ContextItem:
    id: str
    content: str
    priority: ContextPriority      # CRITICAL, HIGH, MEDIUM, LOW, ARCHIVE
    token_count: int
    source: str                    # "current", "memory", "retrieved"
    metadata: Dict[str, Any] = {}
```

### Example

```python
from nooht.context.manager import ContextManager, ContextItem, ContextPriority

ctx = ContextManager(max_tokens=4096)

# Add critical prompt
ctx.add(ContextItem(
    id="prompt_001",
    content="Implement a JWT authentication middleware...",
    priority=ContextPriority.CRITICAL,
    token_count=50,
    source="current",
))

# Add retrieved symbols
for symbol in retrieved_symbols:
    ctx.add(ContextItem(
        id=symbol.id,
        content=symbol.summary,
        priority=ContextPriority.HIGH,
        token_count=20,
        source="retrieved",
    ))

# Auto-compress if over budget
compressed = ctx.compress_if_needed(threshold_ratio=0.85)

print(ctx.stats())
# {'total_items': 12, 'total_tokens': 3480, 'usage_ratio': 0.85, ...}
```

---

## ModelAdapter

**Module:** `nooht.adapters.base`  
**Purpose:** Abstract bridge between Nooht and any LLM.

### Abstract Methods

```python
get_hidden_states(input_ids, attention_mask=None, layer_idx=-1, **kwargs) -> Tensor
inject_memory(hidden_states, memory_embeddings, **kwargs) -> Tensor
generate(input_ids, memory_embeddings=None, max_new_tokens=256, **kwargs) -> Any
encode(text: str, **kwargs) -> Tensor
get_config() -> Dict[str, Any]
get_tokenizer() -> Any
```

---

## TransformersAdapter

**Module:** `nooht.adapters.base`  
**Purpose:** HuggingFace Transformers integration.

### Constructor

```python
TransformersAdapter(
    model_name: str,
    device: str = "cuda",
    load_in_8bit: bool = False,
    load_in_4bit: bool = False,
    **kwargs
)
```

### Methods

Implements all `ModelAdapter` methods plus:

| Method | Description |
|--------|-------------|
| `get_hidden_states()` | Returns hidden states from specified layer |
| `inject_memory()` | Placeholder for gated fusion (adds memory to hidden states) |
| `generate()` | Standard HF generate with optional memory injection |
| `encode()` | Mean-pooled last-layer hidden states for retrieval |

### Example

```python
from nooht.adapters.base import TransformersAdapter

adapter = TransformersAdapter(
    model_name="Qwen/Qwen2.5-Coder-3B",
    device="cuda",
    load_in_4bit=True,
)

# Encode text for retrieval embedding
embedding = adapter.encode("def authenticate_user(credentials):")

# Get model config
config = adapter.get_config()
# {'model_name': 'Qwen/Qwen2.5-Coder-3B', 'hidden_size': 2048, ...}
```

---

## Type Reference

### Enums

```python
class SymbolType(Enum):
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    API = "api"
    MODULE = "module"
    CONSTANT = "constant"

class SymbolStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

class MemoryLevel(IntEnum):
    L0_RAW = 0
    L1_SUMMARY = 1
    L2_SEMANTIC = 2
    L3_ARCHIVE = 3

class ContextPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ARCHIVE = "archive"

class RetrievalStrategy(Enum):
    EMBEDDING = "embedding"
    KEYWORD = "keyword"
    GRAPH = "graph"
    HYBRID = "hybrid"
    SYMBOLIC = "symbolic"
```

---

## Error Handling

All public methods raise the following exceptions:

| Exception | Condition |
|-----------|-----------|
| `ValueError` | Invalid parameter (e.g., unknown SymbolType) |
| `KeyError` | Entity ID not found (in strict modes) |
| `ImportError` | Optional dependency missing (DuckDB, FAISS) |
| `NotImplementedError` | Abstract method not implemented |
| `RuntimeError` | Backend connection failure |

---

<p align="center"><i>API documentation maintained by Qwen-Coder (Framework Maintainer)</i></p>
'''
