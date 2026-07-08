# Changelog

All notable changes to Nooht Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Online Memory Learning
- Project Graph Module
- Agent Planner
- Self Improvement Mechanism

---

## [0.1.3] - 2026-07-08

### Fixed
- **memory**: 创建缺失的 `symbol_entity.py` 文件（之前嵌入在 backend.py 中）
- **compression**: 创建缺失的 `hmc.py` 文件（核心压缩模块）
- **memory**: 修复 `FAISSVectorStore.vacuum()` 方法，支持传入原始向量重建索引
- **memory**: 修复 `DuckDBBackend` 索引创建，使用标准 ART 索引替代 GIN 索引
- **memory**: 修复 `InMemoryBackend._deindex_entity()` 防御性检查
- **context**: 修复 `ContextManager.close()` 方法实现

### Changed
- **README**: 更新为框架文档（移除论文草稿内容）
- **ARCHITECTURE**: 新增架构说明文档
- **CONTRIBUTING**: 新增贡献指南文档

---

## [0.1.2] - 2026-07-07

### Added
- **memory**: SymbolEntity 数据类（ID、名称、类型、依赖等）
- **memory**: SymbolMemory 核心类（CRUD + 查询接口）
- **memory**: InMemoryBackend（内存存储后端）
- **memory**: DuckDBBackend（列式数据库后端）
- **memory**: FAISSVectorStore（向量检索）
- **compression**: HMCController（分层记忆压缩控制器）
- **compression**: SymbolCompressor（符号压缩器）
- **semantic**: CodeSemanticAnalyzer（基于 AST 的代码语义分析）
- **semantic**: SemanticCodeMemory（语义记忆存储）
- **context**: ContextManager（Token 预算管理）
- **adapters**: ModelAdapter 抽象基类
- **adapters**: TransformersAdapter（HuggingFace 适配器）
- **retrieval**: Retriever 抽象基类
- **retrieval**: EmbeddingRetriever, KeywordRetriever, GraphRetriever, HybridRetriever
- **tests**: 完整的单元测试套件

### Technical Details
- 支持百万级 Entity 的存储设计
- Tombstone 软删除机制
- 线程安全的 DuckDB 连接管理
- Rule-based 代码语义分析（无需训练）
- 分层压缩：L0_RAW → L1_SUMMARY → L2_SEMANTIC → L3_ARCHIVE

---

## [0.1.0] - 2026-07-01

### Added
- 项目初始化
- 基础架构设计
- 核心模块规划
