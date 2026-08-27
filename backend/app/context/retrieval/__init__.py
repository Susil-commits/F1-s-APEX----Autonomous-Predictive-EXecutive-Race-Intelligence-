"""APEX Context Retrieval Package.

Provides hybrid graph and embedding-based context retrieval mechanisms for agent decision-making.
"""

from backend.app.context.retrieval.context_retriever import (
    ContextRetriever,
    context_retriever,
)

__all__ = ["ContextRetriever", "context_retriever"]
