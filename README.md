
# ============================================================
# 1. README.md — Quick overview with anchor links
# ============================================================

readme_md = r'''# 🌙 Nooht Framework

**A model-agnostic, extensible cognitive infrastructure for long-term code intelligence.**

[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)](https://github.com/MG-feng/Nooht)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-purple)](https://python.org)

> **Nooht does not make models remember more tokens — it gives models a compressible, retrievable, and long-term maintainable code cognition system.**

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

Apache License — see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Repository:** https://github.com/MG-feng/Nooht-by-MG
- **Issues:** https://github.com/MG-feng/Nooht-by-MG/issues
- **Discussions:** https://github.com/MG-feng/Nooht-by-MG/discussions

---

<p align="center"><i>Built for Nightglow. Open to all.</i></p>
'''
