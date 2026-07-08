# Nooht Framework Architecture

## 概述

Nooht 是一个**模型无关的代码智能记忆引擎**，为 AI 系统提供长期记忆和代码理解能力。框架设计遵循以下核心原则：

1. **模型无关性**: 不绑定特定 LLM，通过 Adapter 层支持任意模型接入
2. **存储与业务分离**: Symbol Memory 业务逻辑与底层存储 (InMemory/DuckDB) 完全解耦
3. **压缩优于删除**: 通过 HMC 分层压缩机制保留历史信息，而非简单丢弃
4. **规则优先**: 语义分析采用 Rule-based AST 解析，不依赖训练模型

---

## 核心模块

### 1. Memory Layer (记忆层)

#### 1.1 SymbolEntity (`memory/symbol_entity.py`)
原子记忆单元，表示一个代码符号（函数、类、变量等）。

```python
@dataclass
class SymbolEntity:
    id: str                    # UUID
    name: str                  # 符号名称
    type: SymbolType           # FUNCTION | CLASS | VARIABLE | API | MODULE | CONSTANT
    source: str                # 源代码片段
    file_path: str             # 文件路径
    line_start: int            # 起始行号
    line_end: int              # 结束行号
    signature: str             # 函数签名
    docstring: str             # 文档字符串
    parameters: List[str]      # 参数列表
    return_type: str           # 返回类型
    dependencies: List[str]    # 依赖的 entity_id 列表
    callers: List[str]         # 调用者的 entity_id 列表
    parent_id: Optional[str]   # 父级符号 ID
    summary: str               # 摘要
    embedding: Optional[List[float]]  # 向量嵌入
    semantic_hash: str         # 语义哈希
    status: SymbolStatus       # ACTIVE | ARCHIVED | DEPRECATED
    created_at: str            # ISO 时间戳
    updated_at: str            # ISO 时间戳
    access_count: int          # 访问计数
    last_accessed: Optional[str]  # 最后访问时间
    metadata: Dict[str, Any]   # 扩展元数据
    tags: List[str]            # 标签列表
```

#### 1.2 SymbolMemory (`memory/symbol_memory.py`)
符号记忆库，提供 CRUD 和查询接口。

**核心 API**:
- `add(entity: SymbolEntity) -> str`: 添加实体
- `get(entity_id: str) -> Optional[SymbolEntity]`: 获取实体
- `update(entity_id: str, updates: Dict) -> bool`: 更新实体
- `remove(entity_id: str) -> bool`: 删除实体
- `query(...)` : 多条件查询（按名称、类型、标签、状态等）
- `get_dependencies(entity_id: str) -> List[SymbolEntity]`: 获取依赖
- `get_callers(entity_id: str) -> List[SymbolEntity]`: 获取调用者
- `stats() -> Dict[str, Any]`: 统计信息

#### 1.3 Backend (`memory/backend.py`)
存储后端抽象层。

**MemoryBackend (抽象基类)**:
- 定义所有存储操作的抽象接口
- 支持百万级 Entity 友好设计

**InMemoryBackend**:
- 纯内存实现，使用字典 + 倒排索引
- 适用于 < 10 万 Entity 的开发场景
- 支持 O(1) 复杂度的主键查询

**DuckDBBackend**:
- 列式数据库实现，SIMD 向量化扫描
- 适用于 > 10 万 Entity 的生产场景
- 线程安全（Thread-Local Connection）
- 支持墓碑（Tombstone）软删除机制

#### 1.4 VectorStore (`memory/vector_store.py`)
向量检索独立层。

**VectorStore (抽象基类)**:
- `add(vectors, metadata)`: 添加向量
- `search(query, top_k)`: 相似度检索
- `vacuum()`: 物理清理墓碑并重建索引

**FAISSVectorStore**:
- 基于 FAISS 的 CPU 向量检索
- 支持 Tombstone 过滤
- 内积相似度（需归一化）

---

### 2. Compression Layer (压缩层)

#### 2.1 Hierarchical Memory Compression (`compression/hmc.py`)

**MemoryLevel (层级枚举)**:
```python
L0_RAW = 0       # 原始代码
L1_SUMMARY = 1   # 摘要压缩
L2_SEMANTIC = 2  # 语义压缩
L3_ARCHIVE = 3   # 归档压缩
```

**HMCController**:
- 管理记忆的生命周期
- 自动触发层级压缩（当某层数量超过阈值时）
- 支持基于时间的强制归档

**压缩策略**:
- L0 → L1: 保留签名、摘要、关键依赖
- L1 → L2: 进一步压缩为语义哈希和嵌入
- L2 → L3: 仅保留 ID、名称、类型和归档时间

---

### 3. Semantic Layer (语义层)

#### 3.1 Semantic Code Memory (`semantic/scm.py`)

**CodeSemanticAnalyzer**:
- Rule-based 代码语义分析（基于 AST）
- 无需训练模型即可提取：
  - 输入/输出参数
  - 依赖关系（import/call）
  - 功能意图（基于关键词和文档字符串）
  - 复杂度估计

**CodeSemantic (数据结构)**:
```python
@dataclass
class CodeSemantic:
    name: str
    entity_type: str
    inputs: List[str]
    outputs: List[str]
    dependencies: List[str]
    purpose: str
    key_operations: List[str]
    complexity_estimate: str
    raw_code: str
```

**SemanticCodeMemory**:
- 存储和管理语义分析结果
- 支持按名称、目的检索

---

### 4. Context Layer (上下文层)

#### 4.1 Context Manager (`context/manager.py`)

**ContextPriority**:
```python
CRITICAL > HIGH > MEDIUM > LOW > ARCHIVE
```

**ContextManager**:
- `max_tokens`: Token 预算上限
- `allocate_context(items)`: 按优先级分配上下文
- `compress_if_needed(threshold)`: 超出阈值时压缩低优先级内容
- `remove_redundancy()`: 移除重复内容
- `stats()`: 使用情况统计

**设计原则**:
1. 永远不要溢出 Token 限制
2. 压缩优先于丢弃
3. 保留高优先级内容

---

### 5. Adapter Layer (适配层)

#### 5.1 Model Adapter (`adapters/base.py`)

**ModelAdapter (抽象基类)**:
- `get_hidden_states(...)`: 获取指定层隐藏状态
- `inject_memory(hidden_states, memory_embeddings)`: 注入记忆
- `generate(...)`: 生成输出
- `encode(text)`: 编码文本（用于检索）

**TransformersAdapter**:
- 支持所有 HuggingFace Transformers 模型
- 支持 8bit/4bit 量化加载
- 提供默认的记忆注入实现（加法融合）

**AdapterFactory**:
- 工厂模式创建适配器
- 支持动态扩展

---

### 6. Retrieval Layer (检索层)

#### 6.1 Retriever (`retrieval/retriever.py`)

**RetrievalStrategy**:
```python
EMBEDDING   # 向量相似度检索
KEYWORD     # TF-IDF / BM25 关键词检索
GRAPH       # 基于依赖图的检索
HYBRID      # 混合检索（加权融合）
```

**Retriever (抽象基类)**:
- `retrieve(query, top_k)`: 执行检索
- `index(entities)`: 建立索引
- `add(entity)`: 增量添加

**HybridRetriever**:
- 组合多个检索器
- 支持自定义权重配置

---

## 数据流

### 典型工作流程

```
1. 代码输入
      ↓
2. AST 解析 (CodeSemanticAnalyzer)
      ↓
3. 生成 SymbolEntity
      ↓
4. 存入 SymbolMemory (通过 Backend)
      ↓
5. 可选：生成 Embedding 存入 VectorStore
      ↓
6. 用户查询
      ↓
7. Retriever 检索相关 Entity
      ↓
8. ContextManager 组装上下文（控制 Token 预算）
      ↓
9. Adapter 注入记忆到模型
      ↓
10. 模型生成输出
```

### 压缩触发流程

```
SymbolMemory.add(entity)
      ↓
HMCController.add_memory(entity, L0_RAW)
      ↓
检查 L0 数量是否超过 max_raw_count
      ↓
若超过：将最旧的 20% 压缩到 L1_SUMMARY
      ↓
递归检查 L1、L2 层级
      ↓
定期任务：force_archive_old(days_threshold)
```

---

## 扩展点

### 新增存储后端
1. 继承 `MemoryBackend` 抽象类
2. 实现所有抽象方法
3. 在 `SymbolMemory` 中注入新后端

### 新增检索策略
1. 继承 `Retriever` 抽象类
2. 实现 `retrieve()`、`index()`、`add()` 方法
3. 在 `RetrieverFactory` 中注册

### 新增模型适配器
1. 继承 `ModelAdapter` 抽象类
2. 实现特定模型的推理接口
3. 在 `AdapterFactory` 中注册

---

## 性能考虑

### InMemoryBackend
- 适用规模：< 100,000 entities
- 查询复杂度：O(1) 主键，O(n) 范围查询
- 内存占用：~1KB/entity

### DuckDBBackend
- 适用规模：100,000 ~ 10,000,000 entities
- 查询优化：ART 索引 + SIMD 扫描
- 磁盘占用：~500B/entity（列式压缩）

### FAISSVectorStore
- 适用规模：< 1,000,000 vectors (CPU)
- 检索延迟：~1ms @ top_k=5
- 内存占用：4B/dimension/vector

---

## 版本历史

- **v0.1.2**: 初始发布，包含核心记忆、压缩、语义、上下文、适配、检索模块
- **v0.1.3**: 修复缺失文件（symbol_entity.py, hmc.py），完善 vacuum 逻辑
