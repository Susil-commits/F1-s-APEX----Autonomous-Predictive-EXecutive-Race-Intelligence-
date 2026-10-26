"""Cryptographic Model Integrity & Anti-Tampering Engine.

Guarantees binary models loaded into the APEX runtime have not been
injected, poisoned, or altered in transit or at rest on the paddock filesystem.
Uses SHA-256 hashing and HMAC-SHA256 signature verification.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_SIGNING_KEY = os.environ.get(
    "APEX_MODEL_SIGNING_KEY",
    "apex-f1-enterprise-secret-signing-key-2026-v1"
)


def compute_file_sha256(file_path: str, chunk_size: int = 65536) -> str:
    """Computes hexadecimal SHA-256 digest of a target file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target model file not found: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sign_model_file(
    model_path: str,
    key: Optional[str] = None,
    output_sig_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates an HMAC-SHA256 signature and verification manifest for a model artifact."""
    signing_key = (key or DEFAULT_SIGNING_KEY).encode("utf-8")
    sha256_hash = compute_file_sha256(model_path)

    signature = hmac.new(
        signing_key,
        sha256_hash.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    manifest: Dict[str, Any] = {
        "model_file": os.path.basename(model_path),
        "sha256": sha256_hash,
        "hmac_sha256_signature": signature,
        "algorithm": "HMAC-SHA256",
        "file_size_bytes": os.path.getsize(model_path),
    }

    if metadata:
        manifest["custom_metadata"] = metadata

    sig_file = output_sig_path or f"{model_path}.sig"
    with open(sig_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Successfully signed %s -> %s", model_path, sig_file)
    return manifest


def verify_model_integrity(
    model_path: str,
    sig_path: Optional[str] = None,
    key: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verifies that the target model matches its cryptographic signature and hash.

    Returns:
        (is_valid, reason_message)
    """
    if not os.path.exists(model_path):
        return False, f"Model file missing: {model_path}"

    sig_file = sig_path or f"{model_path}.sig"
    if not os.path.exists(sig_file):
        return False, f"Model signature file missing: {sig_file}"

    try:
        with open(sig_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        return False, f"Signature manifest unreadable or corrupt: {exc}"

    expected_sha256 = manifest.get("sha256")
    expected_sig = manifest.get("hmac_sha256_signature")

    if not expected_sha256 or not expected_sig:
        return False, "Malformed signature manifest: missing sha256 or signature"

    # Step 1: Verify raw file hash
    actual_sha256 = compute_file_sha256(model_path)
    if not hmac.compare_digest(actual_sha256, expected_sha256):
        return False, (
            f"Model file hash mismatch! File altered. Expected: {expected_sha256}, "
            f"Actual: {actual_sha256}"
        )

    # Step 2: Verify HMAC signature
    signing_key = (key or DEFAULT_SIGNING_KEY).encode("utf-8")
    computed_sig = hmac.new(
        signing_key,
        actual_sha256.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_sig, expected_sig):
        return False, "Cryptographic HMAC signature validation failed! Key mismatch or tampered signature."

    return True, "Model cryptographic signature and SHA-256 hash verified successfully."
