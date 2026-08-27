"""APEX Context Metadata Package.

Provides registries and lookups for model cards and dataset lineage cards.
"""

from backend.app.context.metadata.model_metadata import (
    MODEL_REGISTRY,
    get_model_metadata,
    list_all_model_metadata,
)
from backend.app.context.metadata.dataset_metadata import (
    DATASET_REGISTRY,
    get_dataset_metadata,
    list_all_dataset_metadata,
)

__all__ = [
    "MODEL_REGISTRY",
    "get_model_metadata",
    "list_all_model_metadata",
    "DATASET_REGISTRY",
    "get_dataset_metadata",
    "list_all_dataset_metadata",
]
