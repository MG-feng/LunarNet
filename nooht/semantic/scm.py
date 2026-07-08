"""
Semantic Code Memory (SCM)
代码语义理解 — 将代码转换为语义结构
Rule-based 实现（不依赖训练模型）
"""

import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CodeSemantic:
    """代码语义结构"""
    name: str
    entity_type: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    purpose: str = ""
    key_operations: List[str] = field(default_factory=list)
    complexity_estimate: str = "simple"
    raw_code: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.entity_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "purpose": self.purpose,
            "key_operations": self.key_operations,
            "complexity": self.complexity_estimate,
            "raw_code": self.raw_code[:200] + "..." if len(self.raw_code) > 200 else self.raw_code,
        }


class CodeSemanticAnalyzer:
    """代码语义分析器 — Rule-based，不依赖训练模型"""
    
    def __init__(self):
        self._keyword_map = {
            "login": "user authentication",
            "auth": "authentication",
            "validate": "validation",
            "parse": "parsing",
            "convert": "conversion",
            "transform": "transformation",
            "compute": "computation",
            "calculate": "calculation",
            "fetch": "data retrieval",
            "load": "data loading",
            "save": "data persistence",
            "delete": "data deletion",
            "update": "data update",
            "create": "creation",
            "get": "retrieval",
            "set": "assignment",
            "init": "initialization",
            "clean": "cleanup",
            "process": "processing",
            "handle": "handling",
        }
    
    def analyze(self, code: str, entity_type: str = "function") -> CodeSemantic:
        if entity_type == "function":
            return self._analyze_function(code)
        elif entity_type == "class":
            return self._analyze_class(code)
        else:
            return self._analyze_generic(code, entity_type)
    
    def _analyze_function(self, code: str) -> CodeSemantic:
        try:
            tree = ast.parse(code)
            if not tree.body or not isinstance(tree.body[0], ast.FunctionDef):
                return self._fallback_analysis(code, "function")
            
            func = tree.body[0]
            name = func.name
            inputs = [arg.arg for arg in func.args.args]
            
            outputs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value:
                    outputs.append(self._node_to_string(node.value))
            
            dependencies = self._extract_dependencies(tree)
            purpose = self._infer_purpose(name, code)
            operations = self._extract_key_operations(tree)
            complexity = self._estimate_complexity(tree)
            
            return CodeSemantic(
                name=name,
                entity_type="function",
                inputs=inputs,
                outputs=outputs or ["unknown_return"],
                dependencies=dependencies,
                purpose=purpose,
                key_operations=operations,
                complexity_estimate=complexity,
                raw_code=code,
            )
        except SyntaxError:
            return self._fallback_analysis(code, "function")
    
    def _analyze_class(self, code: str) -> CodeSemantic:
        try:
            tree = ast.parse(code)
            if not tree.body or not isinstance(tree.body[0], ast.ClassDef):
                return self._fallback_analysis(code, "class")
            
            cls = tree.body[0]
            name = cls.name
            methods = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
            bases = [self._node_to_string(base) for base in cls.bases]
            purpose = self._infer_purpose(name, code)
            
            return CodeSemantic(
                name=name,
                entity_type="class",
                inputs=bases,
                outputs=methods,
                dependencies=bases,
                purpose=f"Class: {purpose}",
                key_operations=methods,
                complexity_estimate="moderate" if len(methods) > 10 else "simple",
                raw_code=code,
            )
        except SyntaxError:
            return self._fallback_analysis(code, "class")
    
    def _analyze_generic(self, code: str, entity_type: str) -> CodeSemantic:
        return self._fallback_analysis(code, entity_type)
    
    def _fallback_analysis(self, code: str, entity_type: str) -> CodeSemantic:
        name_match = re.search(r'(?:def|class)\s+(\w+)', code)
        name = name_match.group(1) if name_match else "unknown"
        param_match = re.search(r'def\s+\w+\s*\(([^)]*)\)', code)
        inputs = [p.strip() for p in param_match.group(1).split(',') if p.strip()] if param_match else []
        purpose = self._infer_purpose(name, code)
        
        return CodeSemantic(
            name=name,
            entity_type=entity_type,
            inputs=inputs,
            outputs=[],
            dependencies=[],
            purpose=purpose,
            key_operations=[],
            complexity_estimate="simple",
            raw_code=code,
        )
    
    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    deps.append(f"{module}.{alias.name}")
        return list(set(deps))[:20]
    
    def _extract_key_operations(self, tree: ast.AST) -> List[str]:
        ops = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                ops.append(node.func.id)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                ops.append(f"{self._node_to_string(node.func.value)}.{node.func.attr}")
        return list(set(ops))[:20]
    
    def _infer_purpose(self, name: str, code: str) -> str:
        name_lower = name.lower()
        for keyword, purpose in self._keyword_map.items():
            if keyword in name_lower:
                return purpose
        doc_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if doc_match:
            doc = doc_match.group(1).strip()
            if doc:
                return doc[:100]
        return f"Handles {name} operation"
    
    def _estimate_complexity(self, tree: ast.AST) -> str:
        node_count = sum(1 for _ in ast.walk(tree))
        if node_count < 20:
            return "simple"
        elif node_count < 50:
            return "moderate"
        else:
            return "complex"
    
    def _node_to_string(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._node_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Call):
            return f"{self._node_to_string(node.func)}(...)"
        else:
            return "?"


class SemanticCodeMemory:
    """语义代码记忆库 — SCM 容器"""
    
    def __init__(self):
        self._analyzer = CodeSemanticAnalyzer()
        self._semantics: Dict[str, CodeSemantic] = {}
        self._name_index: Dict[str, List[str]] = {}
        self._purpose_index: Dict[str, List[str]] = {}
    
    def analyze_and_store(self, code: str, entity_id: str, entity_type: str = "function") -> CodeSemantic:
        semantic = self._analyzer.analyze(code, entity_type)
        self._semantics[entity_id] = semantic
        self._name_index.setdefault(semantic.name, []).append(entity_id)
        purpose_key = semantic.purpose[:20]
        self._purpose_index.setdefault(purpose_key, []).append(entity_id)
        return semantic
    
    def get(self, entity_id: str) -> Optional[CodeSemantic]:
        return self._semantics.get(entity_id)
    
    def find_by_name(self, name: str) -> List[CodeSemantic]:
        return [self._semantics[eid] for eid in self._name_index.get(name, []) if eid in self._semantics]
    
    def find_by_purpose(self, purpose_keyword: str) -> List[CodeSemantic]:
        results = []
        for key, eids in self._purpose_index.items():
            if purpose_keyword.lower() in key.lower():
                for eid in eids:
                    if eid in self._semantics:
                        results.append(self._semantics[eid])
        return results
    
    def to_dict(self) -> Dict[str, Dict]:
        return {eid: sem.to_dict() for eid, sem in self._semantics.items()}
