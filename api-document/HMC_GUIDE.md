
# ============================================================
# 8. HMC_GUIDE.md
# ============================================================

hmc_guide_md = r'''# Nooht Framework — HMC Guide

**Version:** 0.1.0-alpha  
**Scope:** Hierarchical Memory Compression policies, levels, and best practices

---

## Core Principle

> **Compression is always preferred over deletion.**

```
Raw Memory (L0)
    ↓
Summary Memory (L1) — 30% size
    ↓
Semantic Memory (L2) — 10% size
    ↓
Archive Memory (L3) — 1% size
    ↓
Delete — only when all compression exhausted
```

This principle is enforced at the architecture level. Any system that deletes memory before attempting compression violates Nooht's design invariant.

---

## Compression Levels

### L0 — Raw Memory

**Content:** Full source code, docstring, all metadata, relationships  
**Use Case:** Active development, recently accessed symbols  
**Size:** 1.0x (baseline)

```python
{
    "name": "authenticate_user",
    "type": "function",
    "source": "def authenticate_user(creds): ...",  # Full source
    "docstring": "Validate credentials and return JWT.",
    "signature": "authenticate_user(credentials: Credentials) -> Token",
    "parameters": ["credentials"],
    "return_type": "Token",
    "dependencies": ["db", "bcrypt", "jwt"],
    "callers": ["login_handler", "api_gateway"],
    "file_path": "src/auth.py",
    "line_start": 10,
    "line_end": 25,
    "metadata": {"language": "python", "framework": "fastapi"},
}
```

### L1 — Summary Memory

**Content:** Signature, summary, file location, top 10 dependencies  
**Use Case:** Frequently referenced but not actively modified symbols  
**Size:** ~0.3x

```python
{
    "name": "authenticate_user",
    "type": "function",
    "signature": "authenticate_user(credentials: Credentials) -> Token",
    "summary": "Validates credentials and returns JWT token",
    "file_path": "src/auth.py",
    "line_start": 10,
    "line_end": 25,
    "dependencies": ["db", "bcrypt", "jwt"],  # Top 10 only
}
```

**What is lost:** Full source code, docstring, callers list, metadata

### L2 — Semantic Memory

**Content:** Embedding vector, key metadata, top 5 dependencies, summary  
**Use Case:** Infrequently accessed but semantically important symbols  
**Size:** ~0.1x

```python
{
    "id": "550e8400-...",
    "name": "authenticate_user",
    "type": "function",
    "embedding": [0.12, -0.45, 0.89, ...],  # 768-dim vector (truncated to 64)
    "semantic_hash": "a3f7c2d8e1b4...",
    "dependencies": ["db", "bcrypt"],  # Top 5 only
    "summary": "Validates credentials and returns JWT",
}
```

**What is lost:** Source code, signature details, file location, most dependencies

### L3 — Archive Memory

**Content:** ID, name, type, semantic hash, archive timestamp  
**Use Case:** Historical symbols, rarely accessed  
**Size:** ~0.01x

```python
{
    "id": "550e8400-...",
    "name": "authenticate_user",
    "type": "function",
    "semantic_hash": "a3f7c2d8e1b4...",
    "archived_at": "2026-07-08T14:30:00",
}
```

**What is lost:** Everything except identity and hash

---

## Trigger Policies

### Automatic Triggers

```python
HMCController(
    max_raw_count=10000,      # L0 threshold
    max_summary_count=50000,  # L1 threshold
    max_semantic_count=100000, # L2 threshold
    archive_after_days=90,     # Time-based trigger
)
```

**Level Promotion Logic:**

```
When len(L0) > max_raw_count:
    Sort L0 by compressed_at (oldest first)
    Take oldest 20%
    Compress each to L1
    Delete from L0

When len(L1) > max_summary_count:
    Sort L1 by compressed_at (oldest first)
    Take oldest 20%
    Compress each to L2
    Delete from L1

When len(L2) > max_semantic_count:
    Sort L2 by compressed_at (oldest first)
    Take oldest 20%
    Compress each to L3
    Delete from L2
```

### Time-Based Trigger

```python
# Archive all memories older than 90 days
archived = hmc.force_archive_old(days_threshold=90)
print(f"Archived {archived} old memories to L3")
```

---

## Compression Quality

### Information Preservation Matrix

| Level | Name | Type | Source | Signature | Dependencies | Embedding | Hash |
|-------|------|------|--------|-----------|--------------|-----------|------|
| L0 | ✅ | ✅ | ✅ Full | ✅ | ✅ All | ✅ | ✅ |
| L1 | ✅ | ✅ | ❌ | ✅ | ✅ Top 10 | ❌ | ✅ |
| L2 | ✅ | ✅ | ❌ | ❌ | ✅ Top 5 | ✅ Truncated | ✅ |
| L3 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |

### Recovery Path

```
L3 (Archive)
    ↓  [Cannot recover to L2/L1/L0 — only identity]
    
L2 (Semantic)
    ↓  [Can regenerate approximate signature from embedding]
    
L1 (Summary)
    ↓  [Can fetch original source from version control if needed]
    
L0 (Raw)
    ↓  [Complete information]
```

---

## Best Practices

### 1. Tune Thresholds to Your Repository

| Repository Size | max_raw_count | max_summary_count | max_semantic_count |
|----------------|---------------|-------------------|--------------------|
| Small (< 10K symbols) | 5,000 | 10,000 | 20,000 |
| Medium (10K-100K) | 10,000 | 50,000 | 100,000 |
| Large (100K-1M) | 50,000 | 200,000 | 500,000 |
| Enterprise (> 1M) | 100,000 | 500,000 | 1,000,000 |

### 2. Monitor Compression Ratios

```python
stats = hmc.stats()
total_raw = sum(
    comp.compression_ratio 
    for comp in hmc.raw_memories.values()
)
print(f"Average compression ratio (L0→L1): {total_raw / len(hmc.raw_memories):.2f}x")
```

### 3. Never Skip Compression Levels

❌ **Wrong:** L0 → L3 (direct archive loses too much information)

✅ **Correct:** L0 → L1 → L2 → L3 (gradual degradation)

### 4. Schedule Maintenance

```python
import schedule
import time

def nightly_compression():
    # Archive old memories
    hmc.force_archive_old(days_threshold=30)
    
    # Vacuum tombstones
    backend.vacuum()
    
    # Log stats
    print(hmc.stats())

schedule.every().day.at("02:00").do(nightly_compression)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 5. Preserve Critical Symbols

Mark important symbols to prevent compression:

```python
# Set high access count to keep in L0
entity.access_count = 999999
memory.update(entity.id, {"access_count": 999999})
```

Or use `ContextPriority.CRITICAL` in ContextManager.

---

## Custom Compression Strategy

```python
from nooht.compression.hmc import CompressionStrategy, CompressedMemory, MemoryLevel

class MyCompressor(CompressionStrategy):
    def compress(self, symbol, target_level: MemoryLevel) -> CompressedMemory:
        if target_level == MemoryLevel.L1_SUMMARY:
            data = {
                "name": symbol.name,
                "custom_field": symbol.metadata.get("importance", "normal"),
            }
        # ... handle other levels
        
        return CompressedMemory(
            id=f"compressed_{symbol.id}_{target_level.value}",
            original_id=symbol.id,
            level=target_level,
            data=data,
            compression_ratio=len(symbol.source) / max(len(str(data)), 1),
        )

hmc = HMCController(compressor=MyCompressor())
```

---

## Anti-Patterns

### ❌ Direct Deletion Without Compression

```python
# WRONG — violates Memory Preservation Principle
if len(memory) > limit:
    oldest = find_oldest(memory)
    memory.remove(oldest.id)  # Information permanently lost
```

### ❌ Storing Everything in L0

```python
# WRONG — will exhaust memory
hmc = HMCController(max_raw_count=999999999)  # Effectively disables compression
```

### ❌ Compressing Active Symbols

```python
# WRONG — recently accessed symbols should stay in L0
# The trigger policy sorts by compressed_at, not last_accessed
# This is handled correctly by default, but don't override it
```

---

## Metrics to Monitor

| Metric | Target | Alert If |
|--------|--------|----------|
| L0 / Total ratio | 10-20% | > 50% (compression not triggering) |
| L3 / Total ratio | 30-50% | < 10% (over-retention) |
| Avg compression ratio | > 3x | < 2x (inefficient compression) |
| Archive age (avg) | < 180 days | > 365 days (vacuum needed) |

---

<p align="center"><i>For architecture questions, see <a href="ARCHITECTURE.md">Architecture Overview</a></i></p>
'''
