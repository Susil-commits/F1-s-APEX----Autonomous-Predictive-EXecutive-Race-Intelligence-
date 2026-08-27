"""Dataset Metadata delegator for backend.app.context.metadata.dataset_metadata.

Provides access to curated metadata cards, source manifests, and feature schemas.
"""

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
