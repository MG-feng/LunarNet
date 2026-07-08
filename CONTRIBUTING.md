# Nooht Framework 贡献指南

## 🎯 开发规范

### Python 代码风格

1. **遵循 PEP 8**
   - 使用 4 空格缩进
   - 行宽限制 100 字符
   - 导入顺序：标准库 → 第三方库 → 本地模块

2. **类型提示 (Type Hints)**
   - 所有公共 API 必须包含类型注解
   - 使用 `Optional[]` 表示可为空的参数
   - 使用 `Union[]` 或 `|` 表示联合类型

3. **文档字符串 (Docstring)**
   - 所有公共类、函数必须包含 docstring
   - 遵循 Google Style 格式
   - 包含 Args、Returns、Raises 章节

示例：
```python
def add(self, entity: SymbolEntity) -> str:
    """
    添加符号实体到记忆库。

    Args:
        entity: 要添加的符号实体

    Returns:
        实体的唯一 ID

    Raises:
        ValueError: 当实体已存在时
    """
    pass
```

---

## 📝 Git Commit 规范

### Commit Message 格式

```
<type>: <subject>

<body>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 代码重构（不改变行为）
- `test`: 测试相关
- `docs`: 文档更新
- `chore`: 构建/工具/配置变更
- `perf`: 性能优化

### 示例

```bash
feat(memory): 添加 DuckDB 后端支持

- 实现 MemoryBackend 抽象接口
- 支持线程安全的列式存储
- 添加墓碑软删除机制

Closes #42
```

```bash
fix(compression): 修复 HMC 层级压缩逻辑

- 修正 L1→L2 压缩阈值计算错误
- 添加边界条件测试

Fixes #57
```

---

## 🧪 测试规范

### 单元测试要求

1. **测试覆盖率**
   - 核心模块覆盖率 ≥ 80%
   - 所有公共 API 必须有对应测试

2. **测试命名**
   ```python
   def test_<module>_<function>_<scenario>():
       pass
   
   # 示例
   def test_symbol_memory_crud_operations():
       pass
   
   def test_hmc_compression_triggers_at_threshold():
       pass
   ```

3. **测试结构 (AAA Pattern)**
   ```python
   def test_example():
       # Arrange
       memory = SymbolMemory()
       entity = SymbolEntity(name="test")
       
       # Act
       eid = memory.add(entity)
       
       # Assert
       assert memory.get(eid) is not None
   ```

### 运行测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_symbol_memory.py -v

# 带覆盖率报告
pytest tests/ --cov=nooht --cov-report=html
```

---

## 📦 项目结构

```
nooht/
├── __init__.py           # 包版本和公共导出
├── core/                 # 核心模块导出
├── memory/               # 记忆层
│   ├── symbol_entity.py  # SymbolEntity 定义
│   ├── symbol_memory.py  # SymbolMemory 主类
│   ├── backend.py        # 存储后端抽象
│   └── vector_store.py   # 向量检索
├── compression/          # 压缩层
│   └── hmc.py            # 分层记忆压缩
├── semantic/             # 语义层
│   └── scm.py            # 代码语义分析
├── context/              # 上下文层
│   └── manager.py        # Token 预算管理
├── adapters/             # 适配层
│   └── base.py           # 模型适配器
└── retrieval/            # 检索层
    └── retriever.py      # 统一检索接口

tests/                    # 单元测试
├── test_symbol_memory.py
├── test_backend.py
├── test_hmc.py
├── test_scm.py
├── test_context.py
└── test_retriever.py
```

---

## 🔀 分支策略

### 分支命名

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/<name>`: 功能分支
- `fix/<name>`: 修复分支
- `release/vX.Y.Z`: 发布分支

### 工作流程

```bash
# 创建功能分支
git checkout develop
git checkout -b feature/new-backend

# 开发完成后提交
git commit -m "feat(backend): 添加新存储后端"

# 推送到远程并创建 Pull Request
git push origin feature/new-backend
```

---

## 🚀 发布流程

### 版本号规范 (SemVer)

- `MAJOR.MINOR.PATCH` (例：0.1.3)
- MAJOR: 破坏性变更
- MINOR: 向后兼容的新功能
- PATCH: 向后兼容的 Bug 修复

### 发布步骤

1. 更新版本号 (`__init__.py`, `setup.py`, `pyproject.toml`)
2. 更新 `CHANGELOG.md`
3. 创建 release branch
4. 运行完整测试套件
5. 合并到 main 并打 tag
6. 发布到 PyPI

---

## ⚠️ 禁止事项

根据团队约定，以下行为严格禁止：

❌ 引入 Qwen/Llama 作为基础模型  
❌ 将 Nooht 做成外挂 RAG  
❌ 修改核心设计追求 Benchmark  
❌ 为论文牺牲产品能力  

Nooht 的核心定位是**独立、可扩展、模型无关的基础架构**。

---

## 📞 问题反馈

遇到问题请：
1. 检查现有 Issue 是否已报告
2. 创建新 Issue 并提供：
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（Python 版本、依赖版本）
   - 相关日志/错误信息

---

## 🙏 致谢

感谢所有为 Nooht Framework 做出贡献的开发者！
