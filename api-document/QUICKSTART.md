
# ============================================================
# 6. api-document/QUICKSTART.md
# ============================================================

quickstart_md = r'''# Nooht Framework — Quick Start Guide

**Version:** 0.1.0-alpha  
**Time to first query:** ~5 minutes

---

## Installation

### From PyPI (when published)

```bash
pip install nooht
```

### From Source

```bash
git clone https://github.com/MG-feng/Nooht.git
cd Nooht
pip install -e ".[dev]"
```

### Optional Dependencies

| Feature | Command |
|---------|---------|
| DuckDB backend | `pip install nooht[duckdb]` |
| FAISS retrieval | `pip install nooht[faiss]` |
| Full stack | `pip install nooht[all]` |

---

## 1. Your First Symbol Memory

```python
from nooht import SymbolMemory, SymbolEntity, SymbolType

# Create an in-memory symbol store
memory = SymbolMemory()

# Define a code symbol
entity = SymbolEntity(
    name="authenticate_user",
    type=SymbolType.FUNCTION,
    source='''
def authenticate_user(credentials):
    """Validate credentials and return JWT token."""
    user = db.query(User).filter_by(email=credentials.email).first()
    if not user or not bcrypt.check(credentials.password, user.hash):
        raise AuthError("Invalid credentials")
    return jwt.encode({"sub": user.id}, SECRET)
''',
    signature="authenticate_user(credentials: Credentials) -> Token",
    parameters=["credentials"],
    return_type="Token",
    dependencies=["db", "bcrypt", "jwt"],
    summary="Validates user credentials and issues JWT",
    tags=["auth", "security", "api"],
    file_path="src/auth.py",
    line_start=10,
    line_end=18,
)

# Store it
eid = memory.add(entity)
print(f"Stored entity: {eid}")

# Retrieve it
retrieved = memory.get(eid)
print(f"Name: {retrieved.name}")
print(f"Tags: {retrieved.tags}")

# Query by tag
results = memory.query(tag="auth", limit=5)
print(f"Found {len(results)} auth-related symbols")
```

**Output:**
```
Stored entity: 550e8400-e29b-41d4-a716-446655440000
Name: authenticate_user
Tags: ['auth', 'security', 'api']
Found 1 auth-related symbols
```

---

## 2. Switching to DuckDB (Production)

```python
from nooht import SymbolMemory
from nooht.memory.backend import DuckDBBackend

# Persistent storage with SQL-powered queries
memory = SymbolMemory(backend=DuckDBBackend("my_project.db"))

# All operations are identical to InMemoryBackend
# Data persists across process restarts

# Don't forget to close
memory.close()
```

---

## 3. Analyzing Code Semantics

```python
from nooht.semantic.scm import SemanticCodeMemory

scm = SemanticCodeMemory()

code = """
def calculate_total(items, tax_rate=0.08):
    subtotal = sum(item.price for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax
"""

# Extract semantic structure
semantic = scm.analyze_and_store(
    code,
    entity_id="calc_001",
    entity_type="function"
)

print(semantic.to_dict())
```

**Output:**
```json
{
  "name": "calculate_total",
  "type": "function",
  "inputs": ["items", "tax_rate"],
  "outputs": ["subtotal + tax"],
  "dependencies": [],
  "purpose": "calculation",
  "key_operations": ["sum"],
  "complexity": "simple"
}
```

---

## 4. Hierarchical Memory Compression

```python
from nooht.compression.hmc import HMCController, MemoryLevel
from nooht import SymbolEntity, SymbolType

# Initialize with small thresholds to trigger compression
hmc = HMCController(max_raw_count=3)

# Add multiple symbols
for i in range(5):
    entity = SymbolEntity(
        name=f"func_{i}",
        type=SymbolType.FUNCTION,
        source=f"def func_{i}(x): return x * {i}" * 50,  # Long content
    )
    hmc.add_memory(entity, MemoryLevel.L0_RAW)

# Check compression stats
print(hmc.stats())
```

**Output:**
```json
{
  "raw": 3,
  "summary": 2,
  "semantic": 0,
  "archive": 0,
  "total": 5
}
```

> Notice: 2 items were automatically compressed from L0 to L1 because `max_raw_count=3` was exceeded.

---

## 5. Managing Context with Token Budgets

```python
from nooht.context.manager import ContextManager, ContextItem, ContextPriority

ctx = ContextManager(max_tokens=1000)

# Add items with different priorities
ctx.add(ContextItem(
    id="user_prompt",
    content="Refactor this authentication module...",
    priority=ContextPriority.CRITICAL,
    token_count=20,
    source="current",
))

ctx.add(ContextItem(
    id="symbol_1",
    content="authenticate_user: Validates credentials...",
    priority=ContextPriority.HIGH,
    token_count=15,
    source="retrieved",
))

ctx.add(ContextItem(
    id="symbol_2",
    content="hash_password: Uses bcrypt...",
    priority=ContextPriority.HIGH,
    token_count=12,
    source="retrieved",
))

# Check usage
stats = ctx.stats()
print(f"Usage: {stats['usage_ratio']:.1%} ({stats['total_tokens']} / {stats['max_tokens']} tokens)")
```

---

## 6. Vector Retrieval with FAISS

```python
import numpy as np
from nooht.memory.vector_store import FAISSVectorStore

# Create vector store (768-dim = UniXcoder default)
store = FAISSVectorStore(dimension=768)

# Simulate embeddings (in production, use an encoder)
vectors = np.random.randn(100, 768).astype(np.float32)
metadata = [
    {"id": f"sym_{i}", "name": f"function_{i}", "type": "function"}
    for i in range(100)
]

# Index
store.add(vectors, metadata)

# Search
query = np.random.randn(768).astype(np.float32)
results = store.search(query, top_k=5)

for score, meta in results:
    print(f"Score: {score:.3f} | {meta['name']} ({meta['type']})")
```

---

## 7. Full Pipeline Example

```python
from nooht import SymbolMemory, SymbolEntity, SymbolType
from nooht.memory.backend import DuckDBBackend
from nooht.memory.vector_store import FAISSVectorStore
from nooht.semantic.scm import SemanticCodeMemory
from nooht.compression.hmc import HMCController, MemoryLevel
from nooht.context.manager import ContextManager, ContextItem, ContextPriority

# 1. Initialize infrastructure
memory = SymbolMemory(backend=DuckDBBackend("project.db"))
vector_store = FAISSVectorStore(dimension=768)
scm = SemanticCodeMemory()
hmc = HMCController()
ctx = ContextManager(max_tokens=4096)

# 2. Ingest code repository (simplified)
code_snippets = [
    ("auth.py", "def login(user, password): ..."),
    ("auth.py", "def logout(session_id): ..."),
    ("db.py", "def query(table, filters): ..."),
]

for file_path, source in code_snippets:
    entity = SymbolEntity(
        name=source.split("(")[0].replace("def ", ""),
        type=SymbolType.FUNCTION,
        source=source,
        file_path=file_path,
    )
    
    # Store in Symbol Memory
    eid = memory.add(entity)
    
    # Extract semantics
    scm.analyze_and_store(source, eid)
    
    # Add to compression pipeline
    hmc.add_memory(entity, MemoryLevel.L0_RAW)

# 3. Query and retrieve
results = memory.query(tag="auth", limit=5)

# 4. Build context for LLM
for symbol in results:
    ctx.add(ContextItem(
        id=symbol.id,
        content=symbol.summary or symbol.name,
        priority=ContextPriority.HIGH,
        token_count=20,  # Approximate
        source="retrieved",
    ))

print(f"Context ready: {ctx.stats()['usage_ratio']:.1%} token usage")

# 5. Cleanup
memory.close()
```

---

## Next Steps

- Read the <a href="ARCHITECTURE.md">Architecture Overview</a> for design principles
- Explore the <a href="API_REFERENCE.md">API Reference</a> for complete method documentation
- Check the <a href="BACKEND_GUIDE.md">Backend Guide</a> for storage configuration
- Learn about <a href="HMC_GUIDE.md">HMC compression policies</a>
- See <a href="ADAPTER_GUIDE.md">Adapter Guide</a> for integrating custom LLMs

---

<p align="center"><i>Questions? Open a <a href="https://github.com/MG-feng/Nooht/discussions">Discussion</a></i></p>
'''
