import pytest
from nooht.semantic.scm import CodeSemanticAnalyzer, SemanticCodeMemory


def test_scm_analyze_function():
    analyzer = CodeSemanticAnalyzer()
    code = """
def login(user, password):
    \"\"\"Authenticate user\"\"\"
    token = generate_token(user)
    return token
"""
    semantic = analyzer.analyze(code, "function")
    
    assert semantic.name == "login"
    assert "user" in semantic.inputs
    assert "password" in semantic.inputs
    assert semantic.entity_type == "function"


def test_scm_analyze_class():
    analyzer = CodeSemanticAnalyzer()
    code = """
class UserAuth:
    def __init__(self):
        pass
    def login(self):
        pass
"""
    semantic = analyzer.analyze(code, "class")
    
    assert semantic.name == "UserAuth"
    assert semantic.entity_type == "class"
    assert "login" in semantic.outputs


def test_scm_store():
    scm = SemanticCodeMemory()
    
    code1 = "def login(): return token"
    code2 = "def logout(): return None"
    
    scm.analyze_and_store(code1, "id_1", "function")
    scm.analyze_and_store(code2, "id_2", "function")
    
    sem1 = scm.get("id_1")
    assert sem1.name == "login"
    
    results = scm.find_by_name("login")
    assert len(results) == 1
    assert results[0].name == "login"
