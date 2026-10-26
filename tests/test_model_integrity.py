"""Unit tests for APEX Cryptographic Model Integrity Engine."""
import os
import pytest
from core.security.model_integrity import (
    compute_file_sha256,
    sign_model_file,
    verify_model_integrity,
)


def test_sha256_computation(tmp_path):
    sample_file = tmp_path / "model.bin"
    sample_file.write_bytes(b"F1_TELEMETRY_WEIGHTS_2026")

    digest = compute_file_sha256(str(sample_file))
    assert len(digest) == 64
    assert isinstance(digest, str)


def test_sign_and_verify_model_success(tmp_path):
    model_file = tmp_path / "apex_model.joblib"
    model_file.write_bytes(b"VALID_SERIALIZED_MODEL_BYTES")

    sig_file = tmp_path / "apex_model.joblib.sig"
    manifest = sign_model_file(
        str(model_file),
        key="test-signing-key",
        output_sig_path=str(sig_file),
    )
    assert manifest["sha256"]
    assert manifest["hmac_sha256_signature"]

    is_valid, reason = verify_model_integrity(
        str(model_file),
        sig_path=str(sig_file),
        key="test-signing-key",
    )
    assert is_valid is True
    assert "verified successfully" in reason


def test_verify_rejects_tampered_model(tmp_path):
    model_file = tmp_path / "apex_model.joblib"
    model_file.write_bytes(b"ORIGINAL_BYTES")

    sig_file = tmp_path / "apex_model.joblib.sig"
    sign_model_file(str(model_file), key="test-key", output_sig_path=str(sig_file))

    # Tamper with file
    model_file.write_bytes(b"TAMPERED_BYTES_MALICIOUS_PAYLOAD")

    is_valid, reason = verify_model_integrity(
        str(model_file),
        sig_path=str(sig_file),
        key="test-key",
    )
    assert is_valid is False
    assert "mismatch" in reason.lower()
