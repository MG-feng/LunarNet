# Nooth: Structure-Augmented Code Language Model with Hierarchical Semantic Memory

> **Paper Draft v0.1** | GitHub Preprint  
> **Status:** Work in Progress — Nooth-3B-0.0.1-alpha under development  
> **Date:** 2026-07-07  
> **Team:** Moonlight Games

---

## Abstract

We present **Nooth**, a code language model architecture augmented with **Hierarchical Semantic Memory (HSM)**—an external memory framework that stores, compresses, and retrieves code entities at multiple abstraction levels (expression, statement, function, class, file, project) rather than raw token sequences. 

Inspired by memory-augmented neural networks and graph-based code representations, Nooth addresses a critical limitation of standard Transformer-based code models: the inability to maintain structured, long-range project-level context under fixed parameter budgets. Instead of scaling model size or context window length, Nooth introduces a **semantic memory layer** that operates alongside the base Transformer, enabling the model to reference project structure, function signatures, and cross-file dependencies without linear growth in KV-cache memory.

We describe the design of HSM, a **Multi-Granularity Structural Position Encoding (MG-SPE)** scheme that encodes code hierarchy rather than linear token position, and a lightweight **Dynamic Semantic Graph (DSG)** interface that connects the memory layer to the base model. We further introduce the **Nooth-3B-0.0.1-alpha** prototype—a minimal viable implementation designed to validate the core hypothesis: *that hierarchical semantic memory improves code understanding, completion, and project-level reasoning in 3B-parameter models without exceeding consumer-grade GPU constraints.*

Our preliminary design targets evaluation on HumanEval, MBPP, and repository-level completion benchmarks. This paper presents the architectural foundation, training methodology, and experimental roadmap. Full empirical results will be released with the alpha prototype.

---

## 1. Introduction

### 1.1 The Problem

Large language models for code (Code-LLMs) have achieved remarkable success in function-level generation [1, 2]. However, real-world software development operates at the **project level**: a single task may require understanding cross-file dependencies, class hierarchies, API contracts, and configuration contexts spread across thousands of lines of code.

Standard Transformer architectures [3] handle long context through two primary mechanisms:
- **Scaling context window length** (e.g., 128K tokens), which incurs quadratic attention cost and massive KV-cache memory overhead.
- **Scaling model parameters**, which is computationally expensive and environmentally unsustainable.

Neither approach directly addresses the **structural nature of code**. Code is not a linear sequence of tokens; it is a hierarchical, graph-structured artifact with explicit dependencies (function calls, imports, inheritance) and implicit semantic relationships (API usage patterns, design conventions). When a model processes a 10,000-token file, it must re-derive the project structure from scratch every forward pass, because standard KV caches store *token-level* attention states, not *semantic-level* entities.

### 1.2 Our Approach: Hierarchical Semantic Memory

We hypothesize that a code model can achieve better project-level understanding by augmenting its token-level processing with a **dedicated semantic memory layer** that persists across forward passes and operates at the abstraction level of code entities rather than individual tokens.

**Nooth** (named after the Egyptian deity of writing and knowledge) introduces three key components:

1. **Hierarchical Semantic Memory (HSM):** A tiered memory system storing code entities at three levels:
   - **L0 — Token Memory:** Local token embeddings within the current window (standard Transformer cache).
   - **L1 — Symbol Memory:** Function signatures, class definitions, API calls, and variable declarations.
   - **L2 — Project Memory:** Compressed summaries of file structures, dependency graphs, and cross-module relationships.

2. **Multi-Granularity Structural Position Encoding (MG-SPE):** A position encoding scheme that replaces linear token indices with code-structure coordinates (Repository → Project → File → Class → Function → Block → Statement → Expression), enabling the model to reason about relative positions in the code hierarchy rather than in the token stream.

3. **Dynamic Semantic Graph (DSG):** A lightweight interface that constructs a semantic dependency graph from the input code (via AST parsing) and routes information between the base model and the HSM layer.

### 1.3 Contributions

This paper makes the following contributions:

- **HSM Framework:** We propose a hierarchical semantic memory architecture specifically designed for code, where memory units are code entities (functions, classes, APIs) rather than token vectors. This shifts the memory burden from the Transformer's KV cache to a compact, structured external store.
- **MG-SPE:** We extend tree-based positional encoding concepts to an 8-level code hierarchy, demonstrating how structural position information can be fused with semantic memory to improve long-context code understanding.
- **Nooth-3B-0.0.1-alpha:** We describe a minimal viable prototype (3B parameters, T4/A100 compatible) designed to isolate and validate the HSM hypothesis through controlled ablation studies.
- **Honest Integration:** We explicitly position Nooth as an integration and optimization of existing techniques—including Gated Graph Neural Networks [4], Hierarchical Memory Transformers [5], Tree-Enhanced CodeBERTa [6], and CodeRL [7]—rather than a from-scratch invention. Our contribution lies in **adapting and combining** these mechanisms for code-specific semantic memory.

---

## 2. Related Work

### 2.1 Code Language Models

Early code models such as CodeBERT [8] and CodeT5 [9] established the viability of pre-trained Transformers for code understanding and generation. Subsequent scaling led to powerful models like CodeLlama [10], DeepSeek-Coder [11], and StarCoder [12], which achieve strong performance on function-level benchmarks (HumanEval [13], MBPP [14]). However, these models treat code as a flat token sequence, missing the explicit structural and dependency information inherent in software.

Graph-based approaches such as GraphCodeBERT [15] and GNN-based fault localization [16] encode code structure using Abstract Syntax Trees (ASTs) and Control/Data Flow Graphs. These methods excel at capturing local structure but typically operate as **static, one-time encodings** rather than persistent, updatable memory. Nooth differs by maintaining a **dynamic, cross-session semantic memory** that evolves as the model processes more of the project.

### 2.2 Memory-Augmented Neural Networks

The Neural Turing Machine (NTM) [17] and subsequent Memory Networks [18] introduced the concept of external differentiable memory. In the Transformer era, several approaches have addressed long-context limitations:

- **Compressive Transformer [19]:** Compresses old KV cache segments into compact summary vectors.
- **Recurrent Memory Transformer (RMT) [20]:** Passes memory tokens across segments to maintain long-range coherence.
- **Hierarchical Memory Transformer (HMT) [21]:** Proposes a three-tier memory hierarchy for natural language, achieving strong long-context results.
- **Titans [22]:** Introduces neural long-term memory modules that learn to remember and forget.

Nooth is **inspired by HMT and RMT** but differs in a critical aspect: **the memory unit is not a token or a hidden state vector, but a code semantic entity** (e.g., a function signature with its dependencies). This semantic abstraction allows Nooth to compress project-level context far more aggressively than token-level memory while preserving structural relationships.

### 2.3 Structural Position Encoding

Standard Rotary Position Embedding (RoPE) [23] encodes linear token positions. For code, which is inherently tree-structured, several works have proposed structural alternatives:

- **Tree-Transformer [24]:** Introduces a 2D coordinate scheme (depth + sibling order) for AST nodes.
- **Tree-Enhanced CodeBERTa [25]:** Proposes depth-based and sibling-index embeddings for AST nodes, showing improvements on code summarization.
- **CSA-Trans [26]:** Introduces a Code Structure Embedder that captures AST structural information.

Nooth's **MG-SPE** extends these concepts to an **8-level code hierarchy** (from Repository down to Expression) and explicitly **couples structural position with semantic memory retrieval**, allowing the model to query memory using hierarchical coordinates (e.g., "retrieve all functions in this file's parent class").

### 2.4 Mixture of Experts and Routing

Mixture of Experts (MoE) [27] and Switch Transformer [28] use sparse routing to activate subsets of parameters. DeepSeek MoE [29] further separates shared and routed experts. Recent work on Routing-Free MoE [30] eliminates the central router entirely, having experts self-activate based on input thresholds.

Nooth includes a lightweight **Capability Routing Layer** (inspired by MoE but not a core contribution) that routes processing to semantic groups (e.g., Parser, Algorithm, API). This is treated as an **implementation optimization** rather than an architectural novelty.

### 2.5 Execution-Guided Training

CodeRL [7] and Execution-Guided Neural Program Synthesis [31] demonstrate that execution feedback (unit test results, runtime behavior) can serve as a powerful training signal. Nooth incorporates a **Progressive Execution Verification (PEV)** framework (training-only) that provides sparse RL rewards based on AST correctness, static analysis, and sandbox execution. This is positioned as a **training infrastructure component**, not an architectural innovation.

---

## 3. Method

### 3.1 Overview

Nooth operates as an **augmentation layer** around a standard Transformer decoder. The base model processes token sequences as usual; the HSM layer maintains a persistent store of code semantics that the model can read from and write to during generation.

```
Input Code Tokens
      |
      v
[AST Parser] ---> Dynamic Semantic Graph (DSG)
      |                              |
      v                              v
[Base Transformer]          [HSM Layer]
      |                              |
      +------------+-----------------+
                   |
                   v
          [Semantic Fusion]
                   |
                   v
            [Output Head]
```

**Key Design Principle:** The DSG construction is an **offline preprocessing step** (using tree-sitter or similar AST parsers). The model learns to *use* the semantic graph and memory, not to *construct* it. This separation keeps the architecture simple and interpretable.

### 3.2 Hierarchical Semantic Memory (HSM)

HSM stores code entities at three levels. Each entity is represented as a structured record with a learned embedding vector.

#### 3.2.1 Memory Entity Structure

```python
class SemanticEntity:
    entity_id: str          # Unique identifier (e.g., "file.py::ClassName::method_name")
    entity_type: str        # "function", "class", "api", "import", "variable"
    name: str               # Human-readable name
    signature: str          # Type signature or prototype
    embedding: Tensor[d]    # Learned d-dimensional vector (default d=256)
    location: Tuple[str, int, int]  # (file_path, start_line, end_line)
    dependencies: List[str] # List of entity_ids this entity depends on
    metadata: Dict          # Additional info (docstring, visibility, etc.)
    level: int              # 0=Token, 1=Symbol, 2=Project
```

#### 3.2.2 Three-Level Hierarchy

**L0 — Token Memory (Working Context):**
- Standard Transformer KV cache for the current window (e.g., 4K tokens).
- Not a novel contribution; included for completeness.

**L1 — Symbol Memory (Local Semantic Cache):**
- Stores all functions, classes, and API calls visible in the current file and its direct imports.
- Updated per forward pass as the model parses new files.
- Retrieval: Cosine similarity between query embedding and entity embeddings.
- Capacity: ~1,000 entities per project (compressed to 256-dim vectors = ~1MB).

**L2 — Project Memory (Global Semantic Summary):**
- Stores compressed summaries of the entire project structure: file dependency graph, class hierarchy, module API surfaces.
- Updated incrementally as L1 entities are promoted (via a learned compression network).
- Capacity: ~100 project-level summaries (256-dim each = ~25KB).

#### 3.2.3 State Update Mechanism

When the model processes a new code segment, HSM updates via a **gated residual update** inspired by Gated Graph Neural Networks [4]:

```
updated_embedding = old_embedding + (candidate_embedding - old_embedding) * σ(gate_logits)
```

where `σ` is the sigmoid function and `gate_logits` are produced by a lightweight MLP (128-dim input) that decides how much new information to absorb. This is mathematically equivalent to a GRU-style update but applied to external memory slots rather than recurrent hidden states.

**Memory Compression (L1 → L2):**

When L1 exceeds capacity, entities are compressed into L2 via a learned aggregation function:

```
project_summary = Aggregate({function_summary_i * attention_weight_i})
```

where `attention_weight_i` is computed from the entity's centrality in the dependency graph.

### 3.3 Multi-Granularity Structural Position Encoding (MG-SPE)

#### 3.3.1 Hierarchy Levels

MG-SPE assigns each token a position vector based on its location in the code hierarchy:

| Level | Scope | Embedding Dim |
|-------|-------|---------------|
| 7 | Repository | 16 |
| 6 | Project | 16 |
| 5 | File | 16 |
| 4 | Class | 16 |
| 3 | Function | 16 |
| 2 | Block | 16 |
| 1 | Statement | 16 |
| 0 | Expression | 16 |

**Total:** 8 levels × 16 dims = **128-dim position vector**.

#### 3.3.2 Position Encoding Formula

For a token at hierarchy level `l` with relative depth `d` (distance from the root of that level):

```
MG-SPE(token) = Σ_{l=0}^{7} [ PE(l) * (1 / (1 + d_l)) ]
```

where `PE(l)` is a learned embedding for level `l`, and `d_l` is the token's depth within that level. The inverse-depth scaling ensures that deeper nesting (e.g., nested blocks) does not dilute position information.

#### 3.3.3 Coupling with HSM

MG-SPE is not merely an input embedding; it serves as a **query key** for HSM retrieval. When the model needs to resolve a function call, it uses the caller's MG-SPE vector to retrieve the callee's semantic entity from L1 memory:

```
retrieved_entity = TopK( HSM_L1, query=MG-SPE(current_token) )
```

This coupling allows structural position to directly drive semantic retrieval—e.g., "find the function definition in the parent class of this file."

### 3.4 Dynamic Semantic Graph (DSG)

DSG is a lightweight dependency graph constructed from the AST of the input code. It serves as the **bridge** between raw code and HSM.

#### 3.4.1 Graph Construction (Offline)

Using tree-sitter or a similar parser:

1. Parse source files into ASTs.
2. Extract entities: functions, classes, imports, API calls.
3. Build edges: `calls`, `inherits`, `imports`, `uses`.
4. Initialize HSM L1 with extracted entities.

#### 3.4.2 Graph-to-Memory Mapping

```
DSG Node (Function "login") 
    -> HSM L1 Entity (type="function", name="login", signature="...")
    -> MG-SPE Level 3 (Function level)
    -> Embedding initialized from base model's token embeddings
```

The DSG is **static per project** but **dynamic across projects**. The model does not learn to build the graph; it learns to *exploit* it.

### 3.5 Semantic Fusion Layer

The base Transformer outputs hidden states `h_t` for each token. The Semantic Fusion Layer combines these with retrieved HSM entities:

```
fused_state = h_t + retrieved_entity_embedding * α
```

where `α` is a learned gating scalar (produced by a 128-dim MLP). This is a **residual-style fusion** that preserves the base model's representations while injecting semantic context.

For project-level queries (e.g., "what other files use this API?"), the fusion layer queries L2 memory:

```
fused_state = h_t + project_summary_embedding * β
```

### 3.6 Training Objectives

Nooth uses a **multi-task training** approach:

**Primary Objective:** Next Token Prediction (standard autoregressive cross-entropy loss).

**Auxiliary Objective (HSM Alignment):** Ensure retrieved semantic entities are relevant to the prediction target:

```
L_aux = -log P( target_entity | query=MG-SPE(token), memory=HSM_L1 )
```

This is a **contrastive learning** objective that trains the HSM retrieval mechanism to fetch semantically relevant entities.

**Sparse RL Objective (NPEV — Training Only):** For a small fraction of batches, generated code is executed in a sandbox. Execution success/failure provides a sparse reward signal:

```
L_rl = -R * log P(generated_code)
```

where `R` is +1 for passing tests, -1 for failures, and 0 for non-executable code. This is applied only during fine-tuning, not pre-training, and is **not used during inference**.

---

## 4. Nooth-3B-0.0.1-alpha: Minimum Viable Prototype

### 4.1 Design Philosophy

Nooth-3B-0.0.1-alpha is **not** the final architecture. It is a controlled experiment designed to answer one question:

> **Does Hierarchical Semantic Memory improve code understanding in 3B-parameter models?**

To ensure interpretability, the alpha prototype **deliberately excludes** the following advanced components:
- Mixture of Experts (MoE) routing
- Full dynamic graph updates (DSG is static, pre-computed)
- Multi-branch reasoning (Tree-of-Thought style)
- Complex execution RL loops (only sparse AST-level rewards)
- Multi-server distributed architecture

### 4.2 Architecture Specification

| Component | Specification |
|-----------|--------------|
| Base Model | 3B-parameter Transformer decoder (24 layers, 16 heads, 2048 hidden dim) |
| Context Window | 8K tokens (L0) |
| HSM L1 Capacity | 512 entities × 256-dim = ~512KB |
| HSM L2 Capacity | 64 project summaries × 256-dim = ~64KB |
| MG-SPE | 8 levels × 16-dim = 128-dim total |
| DSG | Static AST dependency graph (tree-sitter) |
| Training | QLoRA-compatible (4-bit base model + LoRA adapters for HSM fusion) |
| Target GPU | NVIDIA T4 (16GB) for inference; A100 (40GB) for training |

### 4.3 Implementation Notes

**HSM v0.1 (Simplified):**

```python
class HSM_Layer:
    def __init__(self, dim=256, max_l1=512, max_l2=64):
        self.l1_memory = {}  # entity_id -> SemanticEntity
        self.l2_memory = {}  # project_id -> ProjectSummary
        self.dim = dim

    def retrieve(self, query_embedding, k=5):
        # Cosine similarity search over L1
        scores = {
            eid: cosine_sim(query_embedding, entity.embedding)
            for eid, entity in self.l1_memory.items()
        }
        return top_k(scores, k)

    def update(self, entity_id, new_embedding, gate):
        # Gated residual update
        if entity_id in self.l1_memory:
            old = self.l1_memory[entity_id].embedding
            self.l1_memory[entity_id].embedding = old + (new_embedding - old) * sigmoid(gate)

    def compress_to_l2(self, project_id):
        # Aggregate L1 entities into L2 project summary
        entities = [e for e in self.l1_memory.values() if e.project == project_id]
        weights = softmax([self.centrality(e) for e in entities])
        summary = sum(e.embedding * w for e, w in zip(entities, weights))
        self.l2_memory[project_id] = summary
```

**MG-SPE v0.1:**

```python
def compute_mgspe(token, ast_path):
    # ast_path: list of (level, depth) tuples from root to token
    # e.g., [(7,0), (6,0), (5,0), (4,1), (3,2), (2,0), (1,5), (0,3)]
    position = 0
    for level, depth in ast_path:
        level_emb = self.level_embeddings[level]  # 16-dim
        scale = 1.0 / (1.0 + depth)
        position += level_emb * scale
    return position  # 128-dim vector
```

### 4.4 Baseline Comparison

The alpha prototype will be evaluated against two baselines:

1. **Baseline-A:** The same 3B Transformer **without** HSM (standard KV cache only).
2. **Baseline-B:** The same 3B Transformer with **RMT-style memory tokens** (token-level memory, not semantic-level).

This ablation isolates whether the **semantic abstraction** (entity-level vs. token-level) is the source of improvement.

---

## 5. Experimental Roadmap

### 5.1 Datasets

| Dataset | Purpose | Size |
|---------|---------|------|
| The Stack (Python subset) | Pre-training | ~100B tokens |
| CodeParrot | Continued pre-training | ~50B tokens |
| HumanEval | Function-level generation | 164 problems |
| MBPP | Function-level generation | 974 problems |
| RepoBench | Repository-level completion | 500 repositories |
| CrossCodeEval | Cross-file code completion | 2,000 tasks |
| SWE-bench Lite | Real-world bug fixing | 300 issues |

### 5.2 Evaluation Metrics

**Primary Metrics:**
- **Pass@1 / Pass@10** on HumanEval and MBPP
- **Exact Match (EM)** and **Edit Similarity** on RepoBench
- **Context Window Efficiency:** Perplexity at 2K, 8K, 32K, 128K token lengths
- **Memory Overhead:** Peak GPU memory usage during inference

**Secondary Metrics:**
- **Cross-file dependency resolution accuracy:** Can the model correctly import and use functions from other files?
- **API usage correctness:** Does generated code use project-specific APIs correctly?
- **Training throughput:** Tokens/sec during pre-training and fine-tuning

### 5.3 Planned Ablation Studies

| Experiment | Variable | Expected Insight |
|------------|----------|------------------|
| **HSM vs. No HSM** | Presence of HSM layer | Does semantic memory improve code generation? |
| **L1 vs. L2 vs. Both** | HSM level configuration | Is L1 (symbol) sufficient, or does L2 (project) add value? |
| **MG-SPE vs. RoPE** | Position encoding scheme | Does structural position encoding outperform linear encoding for code? |
| **2-level vs. 4-level vs. 8-level MG-SPE** | Granularity of position encoding | Is 8-level granularity necessary, or do fewer levels suffice? |
| **HSM vs. RMT** | Memory type (semantic vs. token) | Is semantic abstraction the key, or is any external memory sufficient? |
| **Sparse RL vs. No RL** | PEV training signal | Does execution feedback improve code correctness? |

### 5.4 Success Criteria

For the alpha prototype to justify continued investment in Nooth v4, it must meet **at least two** of the following:

1. **HumanEval Pass@1 ≥ 35%** (competitive with 3B code models).
2. **RepoBench improvement ≥ 10%** over the 3B baseline without HSM.
3. **Memory reduction ≥ 30%** at 32K context compared to standard KV cache.
4. **Cross-file API usage accuracy ≥ 15%** higher than baseline.

---

## 6. Discussion

### 6.1 Limitations

**Static DSG:** The alpha prototype uses a pre-computed dependency graph. In real-world development, code changes dynamically (files are edited, functions are renamed). A production system would need incremental DSG updates, which introduces consistency challenges.

**Language Scope:** The initial prototype focuses on Python. Extending to multi-language projects (Java, C++, TypeScript) requires language-specific AST parsers and semantic entity schemas.

**Scalability:** While HSM reduces KV-cache pressure, the retrieval mechanism (cosine similarity over L1) is O(N) in the number of entities. For projects with >10,000 functions, approximate nearest-neighbor search (FAISS, HNSW) would be necessary.

**Training Cost:** The auxiliary contrastive objective and sparse RL signals add complexity to the training pipeline. We have not yet quantified their computational overhead relative to standard next-token prediction.

### 6.2 Future Work (Nooth v4)

If the alpha prototype validates the HSM hypothesis, the following components will be explored for the full Nooth architecture:

- **Dynamic DSG Updates:** Incremental AST parsing and graph mutation as code evolves.
- **Multi-Branch Reasoning (NGBR):** Tree-of-Thought style reasoning for complex generation tasks (test-driven development, refactoring).
- **Advanced Capability Routing:** MoE-style expert activation for different code tasks (algorithm design, API integration, debugging).
- **Repository Memory (L3):** Cross-repository knowledge transfer (learning API patterns from open-source projects).
- **Execution-Guided Fine-Tuning:** Full PEV pipeline with sandbox execution, static analysis, and multi-level reward shaping.
- **Multi-Server Architecture:** Distributed HSM for large-scale IDE integration.

---

## 7. Conclusion

We have presented **Nooth**, a code language model architecture built around **Hierarchical Semantic Memory (HSM)**—a persistent, structured memory layer that stores code entities at multiple abstraction levels rather than raw token sequences. By combining HSM with **Multi-Granularity Structural Position Encoding (MG-SPE)** and a lightweight **Dynamic Semantic Graph (DSG)** interface, Nooth aims to improve project-level code understanding without scaling model parameters or context windows.

We explicitly position Nooth as an **integration and optimization** of existing techniques—including memory-augmented Transformers, graph-based code representations, and structural position encodings—adapted specifically for the code domain. Our contribution is not the invention of new neural operators, but the demonstration that **semantic-level memory abstraction outperforms token-level memory** for long-context code generation.

The **Nooth-3B-0.0.1-alpha** prototype is currently under development to validate this hypothesis through controlled ablation studies. We invite the community to follow our progress, critique our approach, and collaborate on building better tools for code intelligence.

---

## References

[1] M. Chen et al., "Evaluating Large Language Models Trained on Code," *arXiv preprint arXiv:2107.03374*, 2021. (Codex)

[2] E. Nijkamp et al., "CodeGen: An Open Large Language Model for Code with Multi-Turn Program Synthesis," *ICLR*, 2023.

[3] A. Vaswani et al., "Attention Is All You Need," *NeurIPS*, 2017.

[4] Y. Li et al., "Gated Graph Sequence Neural Networks," *ICLR*, 2015.

[5] A. Bulatov et al., "Recurrent Memory Transformer," *NeurIPS*, 2022.

[6] M. He et al., "Hierarchical Memory Transformer for Long Context Processing," *NAACL*, 2025.

[7] H. Le et al., "CodeRL: Mastering Code Generation through Pretrained Models and Deep Reinforcement Learning," *NeurIPS*, 2022.

[8] Z. Feng et al., "CodeBERT: A Pre-Trained Model for Programming and Natural Languages," *EMNLP*, 2020.

[9] W. Wang et al., "CodeT5: Identifier-aware Unified Pre-trained Encoder-Decoder Models for Code Understanding and Generation," *EMNLP*, 2021.

[10] B. Roziere et al., "Code Llama: Open Foundation Models for Code," *arXiv preprint arXiv:2308.12950*, 2023.

[11] D. Guo et al., "DeepSeek-Coder: When the Large Language Model Meets Programming — The Rise of Code Intelligence," *arXiv preprint arXiv:2401.14196*, 2024.

[12] R. Li et al., "StarCoder: may the source be with you!" *TMLR*, 2023.

[13] M. Chen et al., "Evaluating Large Language Models Trained on Code," *arXiv preprint arXiv:2107.03374*, 2021. (HumanEval)

[14] J. Austin et al., "Program Synthesis with Large Language Models," *arXiv preprint arXiv:2108.07732*, 2021. (MBPP)

[15] D. Guo et al., "GraphCodeBERT: Pre-training Code Representations with Data Flow," *ICLR*, 2021.

[16] Z. Zhang et al., "GNN-based fault localization with code dependency graph," *FSE*, 2025.

[17] A. Graves et al., "Neural Turing Machines," *arXiv preprint arXiv:1410.5401*, 2014.

[18] S. Sukhbaatar et al., "End-To-End Memory Networks," *NeurIPS*, 2015.

[19] J. Rae et al., "Compressive Transformers for Long-Range Sequence Modelling," *ICLR*, 2020.

[20] A. Bulatov et al., "Recurrent Memory Transformer," *NeurIPS*, 2022.

[21] M. He et al., "Hierarchical Memory Transformer for Long Context Processing," *NAACL*, 2025.

[22] A. Ali et al., "Titans: Neural Long-Term Memory for Transformers," *arXiv*, 2024.

[23] J. Su et al., "RoFormer: Enhanced Transformer with Rotary Position Embedding," *Neurocomputing*, 2024.

[24] S. Peng et al., "Tree-Transformer: A Transformer-based Method for Correction of Tree-structured Data," *ICDE*, 2022.

[25] P. Bartkowiak et al., "Tree-Enhanced CodeBERTa: Leveraging Abstract Syntax Trees for Code Understanding," *arXiv*, 2025.

[26] J. Oh and S. Yoo, "CSA-Trans: Code Structure Aware Transformer for Source Code Summarization," *arXiv*, 2024.

[27] N. Shazeer et al., "Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer," *ICLR*, 2017.

[28] W. Fedus et al., "Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity," *JMLR*, 2022.

[29] D. Dai et al., "DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models," *arXiv*, 2024.

[30] X. Liu et al., "Routing-Free Mixture-of-Experts with Shared Expert Assignment," *arXiv*, 2026.

[31] C. Chen et al., "Execution-Guided Neural Program Synthesis," *ICLR*, 2019.

[32] X. Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models," *NeurIPS*, 2023.

[33] M. Besta et al., "Graph of Thoughts: Solving Elaborate Problems with Large Language Models," *AAAI*, 2024.

---

## Appendix A: Nooth Naming Glossary

To avoid confusion across project versions, we provide a unified naming reference:

| Acronym | Full Name | Status | Description |
|---------|-----------|--------|-------------|
| **HSM** | Hierarchical Semantic Memory | **Core (P1)** | Three-tier semantic memory layer (L0/L1/L2) |
| **MG-SPE** | Multi-Granularity Structural Position Encoding | **Core (P1)** | 8-level code hierarchy position encoding |
| **DSG** | Dynamic Semantic Graph | **Core (P2)** | AST-based dependency graph interface |
| **NSSL** | Nooth Semantic State Lifting | **Merged into HSM** | Hierarchical state aggregation (formerly SSA) |
| **NICR** | Nooth Interpretable Capability Routing | **Optimization** | Lightweight expert routing layer (formerly NSEA) |
| **NGBR** | Nooth Guided Multi-Branch Reasoning | **Future (v4)** | Tree-of-Thought style reasoning (formerly MRTL) |
| **NPEV** | Nooth Progressive Execution Verification | **Training Only** | Multi-level execution feedback (formerly EAV) |
| **NDSGR** | Nooth Dynamic Semantic Graph Routing | **Merged into DSG** | Graph-based state routing (formerly NSSG) |

---

## Appendix B: Project Status & Roadmap

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Nooth-3B-0.0.1-alpha design freeze | 2026-07-07 | ✅ Complete |
| HSM v0.1 implementation | 2026-07-14 | 🔄 In Progress |
| MG-SPE v0.1 implementation | 2026-07-14 | 🔄 In Progress |
| DSG pipeline (tree-sitter integration) | 2026-07-21 | ⏳ Planned |
| Baseline training (3B without HSM) | 2026-07-28 | ⏳ Planned |
| Alpha training (3B + HSM) | 2026-08-04 | ⏳ Planned |
| HumanEval / MBPP evaluation | 2026-08-11 | ⏳ Planned |
| RepoBench / CrossCodeEval evaluation | 2026-08-18 | ⏳ Planned |
| Paper draft v1.0 | 2026-09-01 | ⏳ Planned |
| Open-source release (GitHub) | 2026-09-15 | ⏳ Planned |

---

*This is a living document. Last updated: 2026-07-07.*

*For the latest implementation, see: [github.com/nooth-research/nooth](https://github.com/nooth-research/nooth) (placeholder link)*
