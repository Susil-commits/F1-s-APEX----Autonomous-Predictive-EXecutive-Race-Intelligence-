"""Dataset Metadata delegator for backend.app.context.metadata.dataset_metadata."""

from context.metadata.dataset_metadata import (
    DATASET_REGISTRY,
    get_dataset_metadata,
    list_all_dataset_metadata,
)

__all__ = [
    "DATASET_REGISTRY",
    "get_dataset_metadata",
    "list_all_dataset_metadata",
]
