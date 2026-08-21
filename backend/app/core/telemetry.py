"""OpenTelemetry Distributed Tracing Setup & Context Propagation for APEX."""
import contextlib
import logging
import os
import time
import uuid
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger("apex.core.telemetry")

OTEL_ENABLED = os.getenv("ENABLE_OTEL_TRACING", "1").lower() in ("1", "true", "yes")
OTEL_EXPORTER_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


class MockSpan:
    """Zero-overhead mock OpenTelemetry span for testing and standalone operation."""
    def __init__(self, name: str, trace_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id or uuid.uuid4().hex
        self.span_id = uuid.uuid4().hex[:16]
        self.attributes: Dict[str, Any] = {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None

    def set_attribute(self, key: str, value: Any) -> "MockSpan":
        self.attributes[key] = value
        return self

    def record_exception(self, exception: Exception) -> "MockSpan":
        self.attributes["exception.type"] = type(exception).__name__
        self.attributes["exception.message"] = str(exception)
        return self

    def end(self) -> None:
        self.end_time = time.time()


class ApexTracer:
    """Distributed tracing manager with OpenTelemetry SDK and lightweight fallback."""

    _instance: Optional["ApexTracer"] = None

    def __init__(self):
        self._tracer = None
        self._is_initialized = False
        self._init_tracer()

    @classmethod
    def get_instance(cls) -> "ApexTracer":
        if cls._instance is None:
            cls._instance = ApexTracer()
        return cls._instance

    def _init_tracer(self) -> None:
        if not OTEL_ENABLED:
            logger.info("[Telemetry] OpenTelemetry tracing disabled via environment.")
            return

        try:
            from opentelemetry import trace  # type: ignore
            from opentelemetry.sdk.resources import Resource  # type: ignore
            from opentelemetry.sdk.trace import TracerProvider  # type: ignore
            from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter  # type: ignore

            resource = Resource.create({"service.name": "apex-race-intelligence", "environment": "production"})
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer("apex.core")
            self._is_initialized = True
            logger.info("[Telemetry] OpenTelemetry SDK initialized successfully.")
        except Exception:
            logger.info("[Telemetry] OpenTelemetry SDK not present. Operating with Native Mock Tracer.")
            self._tracer = None

    @contextlib.contextmanager
    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[Any, None, None]:
        """Starts a distributed tracing span."""
        if self._tracer and hasattr(self._tracer, "start_as_current_span"):
            with self._tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))
                yield span
        else:
            span = MockSpan(name=name, trace_id=trace_id)
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                raise
            finally:
                span.end()

    def generate_traceparent(self) -> str:
        """Generates a standard W3C traceparent header: 00-{trace_id}-{span_id}-01."""
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        return f"00-{trace_id}-{span_id}-01"

    def parse_traceparent(self, header_val: str) -> Dict[str, str]:
        """Parses W3C traceparent header into trace_id and parent_span_id."""
        parts = header_val.split("-")
        if len(parts) >= 4:
            return {"version": parts[0], "trace_id": parts[1], "parent_span_id": parts[2], "flags": parts[3]}
        return {"trace_id": uuid.uuid4().hex, "parent_span_id": uuid.uuid4().hex[:16]}


tracer = ApexTracer.get_instance()
