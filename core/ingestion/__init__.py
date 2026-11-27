"""APEX Core Data Ingestion Adapters.

Handles historical race results, qualifying data, and standings from the Jolpica F1 API.
"""
from core.ingestion.jolpica_adapter import JolpicaAdapter

__all__ = ["JolpicaAdapter"]
