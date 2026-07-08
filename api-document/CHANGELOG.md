
# ============================================================
# 10. CHANGELOG.md
# ============================================================

changelog_md = r'''# Changelog

All notable changes to the Nooht Framework are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-alpha] — 2026-07-08

### Added

#### Core Infrastructure

- **SymbolEntity** — Atomic data model for code entities with full lifecycle tracking (id, name, type, source, dependencies, callers, embedding, status, metadata, tags)
- **SymbolMemory** — Business logic facade with CRUD operations, multi-condition querying, and pagination
- **MemoryBackend** — Abstract storage interface enabling pluggable backends
- **InMemoryBackend** — High-performance, non-persistent backend for development and testing (< 100K entities)
- **DuckDBBackend** — Production-grade, persistent backend with columnar storage, thread-local connections, and tombstone soft-delete

#### Hierarchical Memory Compression (HMC)

- **MemoryLevel** enum — L0_RAW, L1_SUMMARY, L2_SEMANTIC, L3_ARCHIVE
- **HMCController** — Automatic compression trigger based on count thresholds and time-based archiving
- **SymbolCompressor** — Default compression strategy with configurable level transitions
- **Memory Preservation Principle** — Compression is always preferred over deletion

#### Semantic Code Memory (SCM)

- **CodeSemantic** — Structured semantic representation (name, type, inputs, outputs, dependencies, purpose, complexity)
- **CodeSemanticAnalyzer** — Rule-based AST parser with heuristic keyword inference (no model training)
- **SemanticCodeMemory** — Container with name-based and purpose-based indexing

#### Context Management

- **ContextManager** — Dynamic token budget allocation with priority-based eviction
- **ContextItem** — Context unit with priority tier (CRITICAL, HIGH, MEDIUM, LOW, ARCHIVE)
- **ContextPriority** enum — Hierarchical priority system for context scheduling
- **Auto-compression** — Automatic overflow handling with configurable threshold ratios

#### Retrieval Engine

- **Retriever** — Abstract retrieval interface
- **EmbeddingRetriever** — Vector similarity search placeholder
- **KeywordRetriever** — Keyword-based retrieval placeholder
- **GraphRetriever** — Dependency graph traversal placeholder
- **HybridRetriever** — Weighted fusion of multiple strategies
- **RetrieverFactory** — Dynamic strategy creation

#### Adapter Layer

- **ModelAdapter** — Abstract model-agnostic interface (get_hidden_states, inject_memory, generate, encode)
- **TransformersAdapter** — HuggingFace Transformers integration with 4-bit/8-bit quantization support
- **AdapterFactory** — Dynamic adapter instantiation
- **ModelOutput** — Standardized model output dataclass

#### Vector Storage

- **VectorStore** — Abstract vector storage interface
- **FAISSVectorStore** — CPU-optimized FAISS implementation with L2 normalization, tombstone filtering, and index persistence

#### Quality Assurance

- **Thread-Local Connections** — DuckDB concurrency safety via `threading.local()`
- **Tombstone Mechanism** — Soft-delete with `vacuum()` physical cleanup
- **GIN Index Removal** — DuckDB uses native SIMD vectorized scan instead of PostgreSQL-style GIN indexes
- **OOM Fix** — `InMemoryBackend.count()` calculates at Set level without Entity instantiation
- **SQL Injection Prevention** — Exclusive use of parameterized queries in DuckDBBackend

### Architecture

- Model-agnostic design — No binding to Qwen, DeepSeek, Llama, or any specific LLM
- Strategy pattern — Pluggable backends, retrievers, compressors, and adapters
- Factory pattern — Dynamic instantiation of backends, retrievers, and adapters
- Complete separation — Core modules (`memory/`, `compression/`, `semantic/`) never import `torch` or `transformers`

### Documentation

- `README.md` — Project overview with architecture comparisons
- `.github/CONTRIBUTING.md` — Contribution guidelines, commit conventions, coding standards, review process
- `.github/SECURITY.md` — Vulnerability reporting, security design principles, dependency security
- `api-document/ARCHITECTURE.md` — Design philosophy, module architecture, data flow, performance characteristics
- `api-document/API_REFERENCE.md` — Complete API documentation for all public classes and methods
- `api-document/QUICKSTART.md` — Installation, first query, backend switching, code analysis, HMC, context management
- `api-document/BACKEND_GUIDE.md` — Backend selection, configuration, migration, performance tuning, troubleshooting
- `api-document/HMC_GUIDE.md` — Compression levels, trigger policies, quality metrics, best practices, anti-patterns
- `api-document/ADAPTER_GUIDE.md` — Interface specification, custom implementation, integration patterns, testing
- `api-document/CHANGELOG.md` — This file

### Known Limitations

- `FAISSVectorStore.remove()` uses tombstone marking instead of physical deletion (FAISS IndexFlat limitation)
- `search_by_source()` performs full table scan (expected for text search)
- `TransformersAdapter` is inference-only (no training support by design)
- Multi-tenant isolation not implemented (planned for v0.2)
- Data at rest is not encrypted (use filesystem-level encryption)

---

## [Unreleased]

### Planned for v0.2 (Beta)

- Online Symbol Memory with incremental updates
- Memory rewrite and consolidation
- IDE integration (LSP-like protocol)
- Multi-repository support
- FAISS IndexIDMap2 for physical deletion support
- Connection pool for DuckDBBackend
- Full-text search plugin

### Planned for v0.3

- Continuous learning pipeline
- Dynamic memory graph
- Tool calling integration
- Distributed memory architecture
- Neural SCM as optional plugin

### Planned for v1.0 (Nightglow Integration)

- Nightglow-3B native adapter
- End-to-end training pipeline documentation
- Production deployment guides
- Benchmark suite (separate repository)

---
