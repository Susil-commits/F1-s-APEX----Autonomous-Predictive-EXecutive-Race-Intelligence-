"""Context Retriever delegator for backend.app.context.retrieval.context_retriever.

Executes hybrid multi-hop graph retrieval and vector similarity queries over race history.
"""

from context.retrieval.context_retriever import (
    ContextRetriever,
    context_retriever,
)

__all__ = [
    "ContextRetriever",
    "context_retriever",
]
