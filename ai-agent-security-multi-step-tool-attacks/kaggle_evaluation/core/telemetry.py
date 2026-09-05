"""Opt-in OpenTelemetry instrumentation for the core relay and gateway.

Telemetry is OFF by default: with the default ``TelemetryLevel.NONE`` the helpers
below short-circuit and create no spans, so the library behaves exactly as it
does without OpenTelemetry. Callers enable tracing via ``configure_telemetry``.

This module only creates spans. It never configures an exporter; the deployer is
responsible for attaching whatever exporter (OTLP, console, etc.) they want to
the global ``TracerProvider``.
"""

import contextlib
import enum
import functools
import inspect
import json
import os
from collections.abc import Iterator
from typing import IO, Any

from opentelemetry import trace

_TRACER_NAME = 'kaggle_evaluation'


class TelemetryLevel(enum.Enum):
    """How much detail the relay and gateway should emit as spans."""

    NONE = 0  # Default: no spans, no overhead.
    GATEWAY = 1  # Gateway lifecycle: public methods, sampled predict calls, errors.
    FULL = 2  # Gateway + relay wire detail: serialization, transport, handler spans.


class PayloadLogging(enum.Enum):
    """Which relay payloads the client records as dedicated spans.

    Ordered so a payload logs whenever the configured setting's value is at least the payload's own
    category value: a response (``RESPONSES``) logs at ``RESPONSES`` and ``ALL``, while a request
    (``ALL``) logs only at ``ALL``. Fully orthogonal to ``TelemetryLevel``: payloads are captured at
    any setting other than ``NONE`` -- even when the level dial is ``NONE`` -- without emitting any of
    the method/profiling spans. Enabling capture for a competition with large observations produces
    very large traces, so this is debugging-only.
    """

    NONE = 0  # Default: capture no payloads.
    RESPONSES = 1  # Capture inference-server results only (relay responses).
    ALL = 2  # Capture both relay requests and responses.


level = TelemetryLevel.NONE
log_payloads = PayloadLogging.NONE
# True once configure_telemetry has run, so callers (e.g. the gateway) can avoid
# clobbering an explicit configuration with their own default one.
configured = False
# A NoOpTracer keeps span calls safe before configure_telemetry is ever called.
_tracer: trace.Tracer = trace.NoOpTracer()
_span_budget: 'SpanBudget'  # Initialized after SpanBudget is defined; reset by configure_telemetry.
_payload_budget: 'PayloadBudget'  # Byte budget bounding logged payloads; initialized/reset alongside _span_budget.
# Track the processor/file we install so a later configure_telemetry can tear them down.
_span_processor: Any = None
_output_file: IO[str] | None = None


def _format_span(span) -> str:
    """Compact single-line JSON per span, dropping OTel boilerplate."""
    # IDs are stored as ints; format as 0x-prefixed hex to match OTel convention.
    ctx = span.get_span_context()
    entry = {
        'name': span.name,
        'trace_id': f'0x{ctx.trace_id:032x}',
        'span_id': f'0x{ctx.span_id:016x}',
        'duration_ns': span.end_time - span.start_time,
    }
    if span.parent:
        entry['parent_id'] = f'0x{span.parent.span_id:016x}'
    if span.attributes:
        entry['attributes'] = dict(span.attributes)
    if span.events:
        entry['events'] = [{'name': e.name, **(dict(e.attributes) if e.attributes else {})} for e in span.events]
    if span.status.status_code != trace.StatusCode.UNSET:
        entry['status'] = span.status.status_code.name
    return json.dumps(entry) + '\n'


def _parse_payload_logging(value: str) -> PayloadLogging:
    """Resolve a HEARTH_LOG_PAYLOADS override given as a PayloadLogging name or integer value."""
    try:
        return PayloadLogging[value]
    except KeyError:
        pass
    try:
        return PayloadLogging(int(value))
    except ValueError:
        raise ValueError(f'unknown HEARTH_LOG_PAYLOADS: {value!r}') from None


def configure_telemetry(
    rerun_level: TelemetryLevel = TelemetryLevel.NONE,
    local_level: TelemetryLevel = TelemetryLevel.NONE,
    output: str | os.PathLike[str] | IO[str] | None = None,
    span_budget: int = 100,
    rerun_log_payloads: PayloadLogging = PayloadLogging.NONE,
    local_log_payloads: PayloadLogging = PayloadLogging.NONE,
    payload_budget_bytes: int = 1024 * 1024 * 1024,
) -> None:
    """Set the telemetry verbosity level and span output destination.

    Uses ``rerun_level`` during production reruns (``KAGGLE_IS_COMPETITION_RERUN``
    set) and ``local_level`` otherwise. Both default to ``NONE``. The
    ``HEARTH_TELEMETRY_LEVEL`` env var overrides the resolved level in either case.

    ``rerun_log_payloads`` / ``local_log_payloads`` select relay payload capture with the same
    rerun/local split; both default to ``PayloadLogging.NONE`` since payloads are heavy and off by
    default. ``RESPONSES`` captures inference-server results only; ``ALL`` also captures requests. The
    ``HEARTH_LOG_PAYLOADS`` env var overrides the resolved setting and must name a ``PayloadLogging``
    member (``NONE``/``RESPONSES``/``ALL``) or its integer value (``0``/``1``/``2``), so payload
    debugging can be turned on in a containerized run without a code change. This switch is
    independent of the level: any setting other than ``NONE`` installs the exporter and captures
    payloads even at ``NONE`` level, so data logging can run without any method/profiling spans.
    ``payload_budget_bytes`` caps the total serialized payload bytes logged (default 1 GB) as a
    disk failsafe: once crossed, payload logging stops without serializing further payloads.

    With ``NONE`` and no payload capture the library creates no spans. Otherwise a
    ``TracerProvider`` is installed (unless one is already set, so we don't clobber
    an exporter the caller configured) and a ``ConsoleSpanExporter`` is attached.

    Calling this more than once closes the previous output file and repoints our
    single span processor at the new destination rather than attaching another.

    Args:
        rerun_level: Telemetry level for production reruns. Defaults to ``NONE``.
        local_level: Telemetry level for local testing. Defaults to ``NONE``.
        output: Where to write spans. ``None`` (default) opens ``telemetry.jsonl``
                in the current working directory in append mode.
                A path (str or os.PathLike) opens that file in append mode.
                A file-like object writes spans there directly (not closed by us).
        span_budget: Maximum number of ``sampled_span`` calls that emit spans.
    """
    global level, log_payloads, _tracer, _span_budget, _payload_budget, _span_processor, _output_file, configured

    configured = True

    # Close the file handle a prior call opened before we replace its exporter below.
    if _output_file is not None:
        _output_file.close()
        _output_file = None

    if os.getenv('KAGGLE_IS_COMPETITION_RERUN') is not None:
        effective_level = rerun_level
        log_payloads = rerun_log_payloads
    else:
        effective_level = local_level
        log_payloads = local_log_payloads

    level_override = os.getenv('HEARTH_TELEMETRY_LEVEL')
    if level_override is not None:
        try:
            effective_level = TelemetryLevel[level_override]
        except KeyError:
            raise ValueError(f'unknown HEARTH_TELEMETRY_LEVEL: {level_override!r}') from None

    payloads_override = os.getenv('HEARTH_LOG_PAYLOADS')
    if payloads_override is not None:
        log_payloads = _parse_payload_logging(payloads_override)

    level = effective_level
    _span_budget = SpanBudget(limit=span_budget)
    _payload_budget = PayloadBudget(limit_bytes=payload_budget_bytes)

    # Stand up the exporter whenever spans OR payloads need somewhere to go. Payload capture is
    # orthogonal to the level dial, so log_payloads keeps the real tracer alive even at NONE.
    if effective_level == TelemetryLevel.NONE and log_payloads == PayloadLogging.NONE:
        _tracer = trace.NoOpTracer()
        return

    # Import the SDK lazily so the default NONE path never pays for it.
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        provider = TracerProvider()
        trace.set_tracer_provider(provider)

    if isinstance(output, (str, os.PathLike)):
        _output_file = open(str(output), 'a')  # noqa: SIM115 -- lifetime is the exporter's; closed by configure().
        out = _output_file
    elif output is not None:
        out = output
    else:
        _output_file = open('telemetry.jsonl', 'a')  # noqa: SIM115 -- lifetime is the exporter's; closed by configure().
        out = _output_file

    # OTel provides no API to detach a processor from a provider, so we install ours
    # exactly once and repoint its exporter on later calls. Re-adding a processor per
    # call would leak the old ones; a shut-down BatchSpanProcessor left attached would
    # also short-circuit the provider's force_flush and drop later spans. A
    # SimpleSpanProcessor exports synchronously, so spans reach the file without a flush.
    exporter = ConsoleSpanExporter(out=out, formatter=_format_span)
    if _span_processor is None:
        _span_processor = SimpleSpanProcessor(exporter)
        provider.add_span_processor(_span_processor)
    else:
        _span_processor.span_exporter = exporter
    _tracer = trace.get_tracer(_TRACER_NAME)


@contextlib.contextmanager
def span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[trace.Span | None]:
    """Top-level span, active at GATEWAY and FULL. Yields None when disabled."""
    if level == TelemetryLevel.NONE:
        yield None
        return
    with _tracer.start_as_current_span(name, attributes=attributes) as current:
        yield current


@contextlib.contextmanager
def detailed_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[trace.Span | None]:
    """Wire-level span, active only at FULL. Yields None otherwise."""
    if level != TelemetryLevel.FULL:
        yield None
        return
    with _tracer.start_as_current_span(name, attributes=attributes) as current:
        yield current


def add_event(name: str, attributes: dict[str, Any] | None = None) -> None:
    """Record an event on the current span when telemetry is enabled."""
    if level == TelemetryLevel.NONE:
        return
    trace.get_current_span().add_event(name, attributes=attributes)


def detailed_event(name: str, attributes: dict[str, Any] | None = None) -> None:
    """Record an event on the current span only at FULL."""
    if level != TelemetryLevel.FULL:
        return
    trace.get_current_span().add_event(name, attributes=attributes)


def log_payload(name: str, payload: Any, category: PayloadLogging = PayloadLogging.ALL) -> None:
    """Record a full data payload as its own span when payload capture includes its category.

    ``category`` is the payload's own place in the ``PayloadLogging`` order: a response passes
    ``RESPONSES`` and a request passes ``ALL``, so responses log at ``RESPONSES`` or ``ALL`` while
    requests log only at ``ALL``.

    Fully independent of the level dial: payloads are captured whenever ``log_payloads`` selects them
    -- even at ``NONE`` level and without emitting any of the method/profiling spans. The payload
    rides a dedicated span (nesting under an active span when one exists) so it never depends on
    ambient profiling. It is JSON-encoded because span attributes must be primitives; unserializable
    values fall back to ``str`` via ``default``. Serialization that still fails (non-string dict keys,
    circular references, a ``__str__`` that raises) is swallowed and noted rather than allowed to
    crash the relay path -- telemetry must never interrupt core execution.

    A cumulative byte budget bounds the total logged so an accidental toggle on a data-heavy
    competition can't fill the disk. Once exhausted we skip before serializing, so no further payload
    is even materialized; a single breadcrumb span marks where truncation began.
    """
    if log_payloads.value < category.value or _payload_budget.exhausted:
        return
    try:
        serialized = json.dumps(payload, default=str)
    except Exception as exc:  # noqa: BLE001 -- telemetry must never interrupt core execution.
        with _tracer.start_as_current_span('relay.payload_unserializable') as marker:
            marker.set_attribute('name', name)
            marker.set_attribute('error', str(exc))
        return
    if not _payload_budget.consume(len(serialized)):
        with _tracer.start_as_current_span('PayloadBudget.exhausted') as marker:
            marker.set_attribute('limit_bytes', _payload_budget.limit_bytes)
        return
    with _tracer.start_as_current_span(name) as current:
        current.set_attribute('payload', serialized)


def set_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span when telemetry is enabled."""
    if level == TelemetryLevel.NONE:
        return
    trace.get_current_span().set_attribute(key, value)


class SpanBudget:
    """Tracks a fixed call budget for sampled_span.

    Not thread-safe: ``consume`` mutates ``_count`` without a lock. The gateway
    drives sampled spans from a single thread, so this is intentional. A
    concurrent caller would need to guard ``consume`` externally.
    """

    def __init__(self, limit: int = 100):
        self.limit = limit
        self._count = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self._count)

    def consume(self) -> bool:
        self._count += 1
        if self._count == self.limit + 1:
            add_event('SpanBudget.exhausted', {'limit': self.limit})
        return self._count <= self.limit


_span_budget = SpanBudget()


class PayloadBudget:
    """Tracks a cumulative byte budget for logged payloads, bounding their disk footprint.

    Payloads vary enormously in size, so the call-count cap of SpanBudget can't protect the disk;
    this sums the serialized bytes instead and refuses everything once the limit is crossed. Not
    thread-safe, matching SpanBudget: payload logging is driven from a single thread.
    """

    def __init__(self, limit_bytes: int):
        self.limit_bytes = limit_bytes
        self._spent = 0
        self.exhausted = False

    def consume(self, nbytes: int) -> bool:
        """Charge nbytes against the budget, returning whether the payload fits. Rejects it whole
        rather than truncating, so a single oversized payload is dropped instead of half-written.
        Once the budget is crossed it stays exhausted and rejects everything thereafter."""
        if self.exhausted or self._spent + nbytes > self.limit_bytes:
            self.exhausted = True
            return False
        self._spent += nbytes
        return True


# 1 GB default: generous for debugging capture, far below anything that would fill a disk.
_payload_budget = PayloadBudget(limit_bytes=1024 * 1024 * 1024)


@contextlib.contextmanager
def sampled_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[trace.Span | None]:
    """Span that only emits while the global span budget has remaining calls.

    Always enforces the budget at any non-NONE level. At NONE, never emits.
    """
    if level == TelemetryLevel.NONE:
        yield None
        return
    if not _span_budget.consume():
        yield None
        return
    with _tracer.start_as_current_span(name, attributes=attributes) as current:
        yield current


def wrap_with_span(cls: type, detailed_only: bool = False, exclude: set[str] | None = None) -> None:
    """Wrap every public method defined directly on *cls* with a telemetry span.

    Args:
        cls: The class whose methods should be wrapped.
        detailed_only: If True, use detailed_span (FULL level only).
                       If False, use span (GATEWAY and FULL).
        exclude: Method names to skip (e.g. methods that manage their own spans).
    """
    span_fn = detailed_span if detailed_only else span
    exclude = exclude or set()

    for name, attr in list(cls.__dict__.items()):
        if name.startswith('_'):
            continue
        if name in exclude:
            continue
        if isinstance(attr, (property, staticmethod, classmethod)):
            continue
        fn = attr
        if not callable(fn):
            continue
        # Skip methods we already wrapped so re-running (e.g. class re-import) doesn't nest spans.
        if getattr(fn, '__telemetry_wrapped__', False):
            continue

        span_name = f'{cls.__name__}.{name}'

        # Async support is intentionally omitted; entering the span context in the
        # wrapper would not span the awaited body. Fail loudly instead of silently
        # producing a span that ends before the coroutine runs.
        if inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn):
            raise NotImplementedError(f'wrap_with_span does not support async method {span_name}')

        if inspect.isgeneratorfunction(fn):

            @functools.wraps(fn)
            def gen_wrapper(*args, _fn=fn, _span_name=span_name, _span_fn=span_fn, **kwargs):
                with _span_fn(_span_name):
                    yield from _fn(*args, **kwargs)

            gen_wrapper.__telemetry_wrapped__ = True  # ty: ignore[unresolved-attribute]
            setattr(cls, name, gen_wrapper)
        else:

            @functools.wraps(fn)
            def wrapper(*args, _fn=fn, _span_name=span_name, _span_fn=span_fn, **kwargs):
                with _span_fn(_span_name):
                    return _fn(*args, **kwargs)

            wrapper.__telemetry_wrapped__ = True  # ty: ignore[unresolved-attribute]
            setattr(cls, name, wrapper)
