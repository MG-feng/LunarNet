import pytest
from nooht.retrieval.retriever import (
    EmbeddingRetriever,
    KeywordRetriever,
    HybridRetriever,
    RetrievalStrategy,
    RetrieverFactory,
)


def test_embedding_retriever():
    retriever = EmbeddingRetriever(dimension=128)
    retriever.index([])
    
    results = retriever.retrieve("test", top_k=5)
    assert isinstance(results, list)


def test_keyword_retriever():
    retriever = KeywordRetriever()
    results = retriever.retrieve("test", top_k=5)
    assert isinstance(results, list)


def test_hybrid_retriever():
    retriever1 = EmbeddingRetriever(dimension=128)
    retriever2 = KeywordRetriever()
    
    hybrid = HybridRetriever([retriever1, retriever2], weights=[0.5, 0.5])
    hybrid.index([])
    
    results = hybrid.retrieve("test", top_k=5)
    assert isinstance(results, list)


def test_retriever_factory():
    retriever = RetrieverFactory.create(RetrievalStrategy.EMBEDDING, dimension=128)
    assert isinstance(retriever, EmbeddingRetriever)
    
    retriever = RetrieverFactory.create(RetrievalStrategy.KEYWORD)
    assert isinstance(retriever, KeywordRetriever)
