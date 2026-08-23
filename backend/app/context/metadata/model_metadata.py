"""Model Metadata delegator for backend.app.context.metadata.model_metadata."""

from context.metadata.model_metadata import (
    MODEL_REGISTRY,
    get_model_metadata,
    list_all_model_metadata,
)

__all__ = [
    "MODEL_REGISTRY",
    "get_model_metadata",
    "list_all_model_metadata",
]
