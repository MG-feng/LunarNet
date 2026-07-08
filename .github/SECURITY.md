
# ============================================================
# 3.Security policy for Q&A
# ============================================================

security_md = r'''# Security Policy

This document outlines the security practices, vulnerability reporting process, and supported versions for the Nooht Framework.

---

## Supported Versions

| Version | Status | Support Level |
|---------|--------|---------------|
| 0.1.x (Alpha) | Active development | Security patches only |
| < 0.1.0 | Unsupported | No patches |

> **Note:** Nooht is currently in Alpha. APIs may change. Security fixes will be backported to the latest Alpha release.

---

## Reporting a Vulnerability

### Private Disclosure (Preferred)

If you discover a security vulnerability, **do not open a public issue**.

Instead, email the security team:

```
security@nooht.dev
```

**Include the following:**

1. **Description** — What is the vulnerability?
2. **Impact** — What data or functionality is at risk?
3. **Reproduction** — Step-by-step instructions to reproduce
4. **Environment** — Python version, OS, Nooht version
5. **Proof of Concept** — Minimal code demonstrating the issue
6. **Suggested Fix** — If you have one (optional but appreciated)

### Response Timeline

| Phase | Timeline | Action |
|-------|----------|--------|
| Acknowledgment | Within 48 hours | Confirm receipt, assign CVE if applicable |
| Initial Assessment | Within 7 days | Validate severity, plan fix |
| Fix Development | Severity-dependent | See table below |
| Disclosure | After fix release | Public advisory with CVE |

### Severity-Based Response

| Severity | CVSS Range | Fix Timeline | Example |
|----------|------------|--------------|---------|
| Critical | 9.0–10.0 | 7 days | Remote code execution, data breach |
| High | 7.0–8.9 | 14 days | SQL injection, path traversal |
| Medium | 4.0–6.9 | 30 days | Information disclosure, DoS |
| Low | 0.1–3.9 | 60 days | Best-practice violations |

---

## Security Design Principles

### 1. No Remote Execution by Default

Nooht does **not**:
- Open network ports
- Execute arbitrary code from memory
- Download or execute external scripts

### 2. Storage Isolation

| Backend | Isolation Model | Risk |
|---------|----------------|------|
| InMemory | Process-local only | Low — data lost on exit |
| DuckDB | File-based | Medium — file permissions matter |
| FAISS | File-based | Medium — index files contain embeddings |

**Recommendation:** Run Nooht in a container with restricted filesystem access for production.

### 3. Input Validation

All user-facing APIs validate:

- **Entity IDs** — UUID format or custom slug (alphanumeric + hyphen)
- **File paths** — Must be within allowed directories (no `../` traversal)
- **Source code** — Length limited to 1MB per entity (configurable)
- **Tags** — Alphanumeric + hyphen, max 50 characters
- **Metadata** — JSON-serializable only, max 64KB per entity

### 4. SQL Injection Prevention

DuckDB backend uses **parameterized queries exclusively**:

```python
# ✅ Safe
self.conn.execute("SELECT * FROM symbols WHERE id = ?", (entity_id,))

# ❌ Never do this
self.conn.execute(f"SELECT * FROM symbols WHERE id = '{entity_id}'")
```

Any PR introducing string interpolation in SQL will be **immediately rejected**.

---

## Known Security Considerations

### Pickle Storage

`PickleStorage` uses Python's `pickle` module, which can execute arbitrary code during deserialization.

**Mitigation:**
- Pickle files must come from trusted sources only
- Use `JSONStorage` or `SQLiteStorage` for untrusted data
- Future versions may add pickle signing

### FAISS Index Files

FAISS index files (`.faiss`) are binary blobs. Maliciously crafted files could cause memory corruption.

**Mitigation:**
- Validate index dimension matches expected value on load
- Load indices in isolated processes where possible

### Thread-Local DuckDB Connections

`DuckDBBackend` uses `threading.local()` for connection isolation. In multi-process environments (e.g., Gunicorn), each process gets its own connection pool.

**Risk:** Race conditions during `vacuum()` if called concurrently.

**Mitigation:**
- `vacuum()` should be called during maintenance windows only
- Future versions may add advisory locking

---

## Security Checklist for Deployments

```
□ Use DuckDBBackend with file-based storage (not :memory:)
□ Set restrictive file permissions on .db and .faiss files (600)
□ Run Nooht in a container with read-only root filesystem
□ Limit source code length per entity (default: 1MB)
□ Enable tombstone filtering in all queries (default: enabled)
□ Do not expose Nooht APIs directly to the internet
□ Use JSONStorage instead of PickleStorage for untrusted data
□ Monitor vacuum() operations — schedule during low-traffic periods
□ Keep DuckDB and FAISS dependencies updated
```

---

## Dependency Security

### Core Dependencies

| Package | Purpose | Security Tracking |
|---------|---------|-------------------|
| `duckdb` | Columnar storage | [DuckDB Security](https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview.html) |
| `faiss-cpu` | Vector similarity | [Meta Security](https://github.com/facebookresearch/faiss/security) |
| `numpy` | Numerical operations | [NumPy Security](https://numpy.org/doc/stable/reference/security.html) |

### Optional Dependencies

| Package | Purpose | Security Note |
|---------|---------|---------------|
| `torch` | Adapter layer only | Not loaded in core modules |
| `transformers` | Adapter layer only | Not loaded in core modules |

> **Core modules (`memory/`, `compression/`, `semantic/`) do not import `torch` or `transformers`.** This is an architectural guarantee.

---

## Vulnerability Disclosure History

| Date | CVE | Severity | Description | Status |
|------|-----|----------|-------------|--------|
| — | — | — | No vulnerabilities reported yet | — |

---

## Security Team

| Role | Contact | Responsibility |
|------|---------|---------------|
| Security Lead | security@nooht.dev | Vulnerability triage, CVE coordination |
| Architecture Lead | ChatGPT 5.5 | Security design review |
| Audit Lead | Qwen 3.7 | Code security audit |

---

## FAQ

### Q: Can Nooht be used in a multi-tenant environment?

**A:** Not recommended in v0.1. Each tenant should have a separate DuckDB file and FAISS index. Multi-tenant isolation is planned for v0.2.

### Q: Does Nooht encrypt data at rest?

**A:** No. v0.1 does not include encryption. Use filesystem-level encryption (e.g., LUKS, EFS) for sensitive data.

### Q: Can malicious code in `source` field execute?

**A:** No. Nooht stores source code as strings. It does not execute or evaluate the code. However, downstream consumers (e.g., SCM analyzer using `ast.parse()`) should handle malformed code gracefully.

### Q: Is the API rate-limited?

**A:** Nooht is a library, not a service. Rate limiting must be implemented by the application using Nooht.

### Q: What happens if DuckDB connection leaks?

**A:** Thread-local connections are garbage collected when the thread exits. For long-running threads, call `backend.close()` explicitly.

---

## Acknowledgments

We thank the following for responsible disclosure:

- *None yet — be the first!*

---

<p align="center"><i>Security is a shared responsibility. Report early, report often.</i></p>
'''
