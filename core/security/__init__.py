"""APEX Enterprise Security & Defense-in-Depth Package.

Provides production-grade AI security controls:
1. Guardrails: Anti-Prompt Injection, Canary Honeytokens, PII & IP Redaction, Input Sanitization.
2. Gateway: Security HTTP Headers, Strict CORS, Request Boundary Protection.
3. Auth & RBAC: API Key Hashing, Role Scoping, Constant-Time Verification.
4. Circuit Breaker: Multi-Provider AI Resiliency, Failover, Degradation Handling.
5. Audit: Cryptographically Chained Immutable Audit Trails.
"""
from core.security.guardrails import (
    InputSanitizer,
    PromptShield,
    CanaryTrap,
    PIISanitizer,
)
from core.security.auth import (
    APIKeyAuthenticator,
    Role,
    get_current_role,
    require_role,
    validate_production_security_config,
)
from core.security.audit import (
    AuditLogger,
    AuditEvent,
    get_audit_logger,
)
from core.security.circuit_breaker import (
    AICircuitBreaker,
    CircuitState,
    get_circuit_breaker,
)
from core.security.gateway import (
    EnterpriseSecurityHeadersMiddleware,
    configure_enterprise_cors,
)

from core.security.model_integrity import (
    compute_file_sha256,
    sign_model_file,
    verify_model_integrity,
)

__all__ = [
    "InputSanitizer",
    "PromptShield",
    "CanaryTrap",
    "PIISanitizer",
    "APIKeyAuthenticator",
    "Role",
    "get_current_role",
    "require_role",
    "validate_production_security_config",
    "AuditLogger",
    "AuditEvent",
    "get_audit_logger",
    "AICircuitBreaker",
    "CircuitState",
    "get_circuit_breaker",
    "EnterpriseSecurityHeadersMiddleware",
    "configure_enterprise_cors",
    "compute_file_sha256",
    "sign_model_file",
    "verify_model_integrity",
]
