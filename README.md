# Nooht Framework

**Model-agnostic code intelligence memory engine.**

Nooht 是一个轻量级、可扩展的框架，用于构建具备代码感知能力的 AI 系统。它不绑定特定模型，而是提供一套标准化的"记忆"与"上下文"基础设施，让任何 LLM 都能获得长期记忆和代码理解能力。

## 🌟 核心特性

- **🧠 Symbol Memory**: 基于图结构的符号存储，支持函数、类、变量等代码实体的增删改查与依赖追踪。
- **🗜️ Hierarchical Memory Compression (HMC)**: 独创的分层压缩机制 (L0_RAW → L1_SUMMARY → L2_SEMANTIC → L3_ARCHIVE)，实现"压缩优于删除"的长期记忆管理。
- **🔍 Semantic Code Memory**: 基于规则（Rule-based）的代码语义分析，无需训练即可提取代码的输入输出、依赖与功能意图。
- **⚖️ Context Manager**: 严格的 Token 预算管理，支持优先级调度与自动压缩，防止上下文溢出。
- **🔌 Model Adapters**: 统一的模型适配层，支持 HuggingFace Transformers、vLLM 或自定义模型无缝接入。
- **📦 Vector Store**: 基于 FAISS 的高性能向量检索，支持 Tombstone 机制以实现高效的软删除与索引重建。
- **💾 Multiple Backends**: 灵活的存储后端，开发期使用 `InMemory`，生产期无缝切换至 `DuckDB` 支持百万级实体。

## 📦 安装

```bash
# 基础安装 (仅包含核心内存与 DuckDB 支持)
pip install -e .

# 完整安装 (包含 Transformers 适配器与 FAISS 向量检索)
pip install -e ".[all]"
```

## 🚀 快速开始

### 1. 初始化记忆库

```python
from nooht import SymbolMemory, SymbolEntity, SymbolType, DuckDBBackend

# 使用 DuckDB 后端支持持久化与大规模数据
memory = SymbolMemory(backend=DuckDBBackend("project_memory.db"))
```

### 2. 存储代码符号

```python
# 创建一个函数符号
entity = SymbolEntity(
    name="calculate_discount",
    type=SymbolType.FUNCTION,
    source="def calculate_discount(price, rate): ...",
    file_path="src/utils/pricing.py",
    tags=["pricing", "utility"],
    dependencies=["validate_price"]
)

# 存入记忆
entity_id = memory.add(entity)
print(f"Stored entity: {entity_id}")
```

### 3. 检索与依赖分析

```python
# 按标签检索
results = memory.query(tag="pricing", limit=10)
for r in results:
    print(f"Found: {r.name}")

# 获取依赖关系
deps = memory.get_dependencies(entity_id)
callers = memory.get_callers(entity_id)
```

### 4. 语义分析与压缩

```python
from nooht import CodeSemanticAnalyzer, HMCController, MemoryLevel

# 语义分析
analyzer = CodeSemanticAnalyzer()
semantic = analyzer.analyze(entity.source, entity_type="function")
print(f"Purpose: {semantic.purpose}")

# 记忆压缩控制器
compressor = HMCController(max_raw_count=100)
compressor.add_memory(entity, initial_level=MemoryLevel.L0_RAW)
```

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        Nooht Framework                     │
├─────────────────────────────────────────────────────────────┤
│  Adapter Layer  │  Context Manager  │  Semantic Code Memory │
│  (Model-agnostic)  (Token Budget)    (Rule-based AST)      │
├─────────────────────────────────────────────────────────────┤
│  Retriever      │  HMC Compression  │  Vector Store        │
│  (Unified)       (L0→L1→L2→L3)       (FAISS + Tombstone)   │
├─────────────────────────────────────────────────────────────┤
│                    Symbol Memory + Backend                   │
│              InMemory (Dev) / DuckDB (Prod)                │
└─────────────────────────────────────────────────────────────┘
```

## 📂 项目结构

```
nooht/
├── core/               # 核心导出
├── memory/             # 符号记忆与存储后端 (SymbolEntity, Backend, VectorStore)
├── compression/        # 分层记忆压缩 (HMC)
├── semantic/           # 代码语义分析 (SCM)
├── context/            # 上下文与 Token 管理
├── adapters/           # 模型适配层 (Transformers, etc.)
└── retrieval/          # 统一检索接口
tests/                  # 单元测试
```

## 🧪 运行测试

```bash
pytest tests/ -v
```

## 🤝 贡献指南

请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发规范与提交约定。

## 📄 许可证

MIT License
