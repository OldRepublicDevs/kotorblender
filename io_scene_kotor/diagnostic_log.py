# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""Structured diagnostic helpers for KotOR operators (stderr via :mod:`log_config`).

Uses lazy ``%`` formatting for :mod:`logging`. Does not attach handlers.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .constants import LogReasonCode


@dataclass(frozen=True, slots=True)
class IoFileSpan:
    """DEBUG span for :mod:`io_scene_kotor.io` load/save entry points."""

    log: logging.Logger
    fn: str
    basename: str
    path_id: str
    t0: float


def begin_io_file_span(log: logging.Logger, fn: str, filepath: str) -> IoFileSpan:
    """Emit ``event=io_start`` at DEBUG (basename + path_id, no full path)."""
    bn = import_basename(filepath)
    pid = path_id_for_filepath(filepath)
    log.debug("event=io_start fn=%s basename=%s path_id=%s", fn, bn, pid)
    return IoFileSpan(log=log, fn=fn, basename=bn, path_id=pid, t0=time.perf_counter())


def end_io_file_span(span: IoFileSpan, *, error: bool) -> None:
    """Emit ``event=io_end`` at DEBUG with duration and OK/ERROR outcome."""
    duration_ms = int((time.perf_counter() - span.t0) * 1000)
    span.log.debug(
        "event=io_end fn=%s basename=%s path_id=%s outcome=%s duration_ms=%s",
        span.fn,
        span.basename,
        span.path_id,
        "ERROR" if error else "OK",
        duration_ms,
    )


@dataclass(frozen=True, slots=True)
class FormatFileSpan:
    """DEBUG span for :mod:`io_scene_kotor.format` reader/writer entry points."""

    log: logging.Logger
    fn: str
    basename: str
    path_id: str
    t0: float


def begin_format_file_span(log: logging.Logger, fn: str, filepath: str) -> FormatFileSpan:
    """Emit ``event=format_start`` at DEBUG (basename + path_id, no full path)."""
    bn = import_basename(filepath) if filepath else ""
    pid = path_id_for_filepath(filepath) if filepath else ""
    log.debug("event=format_start fn=%s basename=%s path_id=%s", fn, bn, pid)
    return FormatFileSpan(log=log, fn=fn, basename=bn, path_id=pid, t0=time.perf_counter())


def end_format_file_span(span: FormatFileSpan, *, error: bool) -> None:
    """Emit ``event=format_end`` at DEBUG with duration and OK/ERROR outcome."""
    duration_ms = int((time.perf_counter() - span.t0) * 1000)
    span.log.debug(
        "event=format_end fn=%s basename=%s path_id=%s outcome=%s duration_ms=%s",
        span.fn,
        span.basename,
        span.path_id,
        "ERROR" if error else "OK",
        duration_ms,
    )


def sanitize_scene_context(text: str, max_len: int = 96) -> str:
    """Single-line, length-limited context for ``event=scene_*`` (no paths)."""
    if not text:
        return ""
    t = " ".join(str(text).split())
    if len(t) > max_len:
        return t[: max_len - 3] + "..."
    return t


@dataclass(frozen=True, slots=True)
class SceneWorkSpan:
    """DEBUG span for :mod:`io_scene_kotor.scene` conversion entry points."""

    log: logging.Logger
    fn: str
    context: str
    t0: float


def begin_scene_work_span(log: logging.Logger, fn: str, context: str = "") -> SceneWorkSpan:
    """Emit ``event=scene_start`` at DEBUG (optional short ``context``, e.g. object/model name)."""
    ctx = sanitize_scene_context(context)
    log.debug("event=scene_start fn=%s context=%s", fn, ctx)
    return SceneWorkSpan(log=log, fn=fn, context=ctx, t0=time.perf_counter())


def end_scene_work_span(span: SceneWorkSpan, *, error: bool) -> None:
    """Emit ``event=scene_end`` at DEBUG with duration and OK/ERROR outcome."""
    duration_ms = int((time.perf_counter() - span.t0) * 1000)
    span.log.debug(
        "event=scene_end fn=%s context=%s outcome=%s duration_ms=%s",
        span.fn,
        span.context,
        "ERROR" if error else "OK",
        duration_ms,
    )


@dataclass(frozen=True, slots=True)
class VendorAdapterSpan:
    """DEBUG span for :mod:`io_scene_kotor.vendor.pykotor_adapter` entry points."""

    log: logging.Logger
    fn: str
    basename: str
    path_id: str
    context: str
    t0: float


def begin_vendor_adapter_span(
    log: logging.Logger,
    fn: str,
    *,
    filepath: str = "",
    context: str = "",
) -> VendorAdapterSpan:
    """Emit ``event=adapter_start`` at DEBUG (basename/path_id when ``filepath`` set)."""
    bn = import_basename(filepath) if filepath else ""
    pid = path_id_for_filepath(filepath) if filepath else ""
    ctx = sanitize_scene_context(context)
    log.debug(
        "event=adapter_start fn=%s basename=%s path_id=%s context=%s",
        fn,
        bn,
        pid,
        ctx,
    )
    return VendorAdapterSpan(
        log=log,
        fn=fn,
        basename=bn,
        path_id=pid,
        context=ctx,
        t0=time.perf_counter(),
    )


def end_vendor_adapter_span(span: VendorAdapterSpan, *, error: bool) -> None:
    """Emit ``event=adapter_end`` at DEBUG with duration and OK/ERROR outcome."""
    duration_ms = int((time.perf_counter() - span.t0) * 1000)
    span.log.debug(
        "event=adapter_end fn=%s basename=%s path_id=%s context=%s outcome=%s duration_ms=%s",
        span.fn,
        span.basename,
        span.path_id,
        span.context,
        "ERROR" if error else "OK",
        duration_ms,
    )


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def path_id_for_filepath(filepath: str) -> str:
    if not filepath:
        return ""
    norm = os.path.normpath(os.path.expanduser(filepath))
    digest = hashlib.sha256(norm.encode("utf-8", errors="replace")).hexdigest()
    return digest[:12]


def import_basename(filepath: str) -> str:
    if not filepath:
        return ""
    return os.path.basename(filepath)


def set_import_invoke_entry(operator: Any) -> None:
    """Call at the start of ``invoke`` for :class:`ImportHelper` operators.

    ``file_drop`` means ``filepath`` was already set when ``invoke`` ran (typical
    drag-and-drop / FileHandler). ``file_menu`` means the file browser will open.
    If ``execute`` runs without ``invoke``, use :func:`get_import_entry` → ``direct``.
    """
    fp = getattr(operator, "filepath", "") or ""
    operator._kb_import_entry = "file_drop" if fp else "file_menu"


# Same filepath semantics for :class:`ExportHelper` (preset path vs file browser).
set_filepath_invoke_entry = set_import_invoke_entry


def get_import_entry(operator: Any) -> str:
    raw = getattr(operator, "_kb_import_entry", None)
    if isinstance(raw, str) and raw:
        return raw
    return "direct"


def log_op_start(
    log: logging.Logger,
    *,
    operator_id: str,
    run_id: str,
    entry: str,
    basename: str,
    path_id: str,
) -> None:
    log.info(
        "event=op_start operator_id=%s run_id=%s entry=%s basename=%s path_id=%s",
        operator_id,
        run_id,
        entry,
        basename,
        path_id,
    )


def log_op_end(
    log: logging.Logger,
    *,
    operator_id: str,
    run_id: str,
    outcome: str,
    work_done: bool,
    reason_code: str,
    duration_ms: int,
) -> None:
    log.info(
        "event=op_end operator_id=%s run_id=%s outcome=%s work_done=%s reason_code=%s duration_ms=%s",
        operator_id,
        run_id,
        outcome,
        work_done,
        reason_code,
        duration_ms,
    )


@dataclass(frozen=True, slots=True)
class ImportDiagSession:
    log: logging.Logger
    operator_id: str
    run_id: str
    t0: float


def begin_simple_operator_diag(
    log: logging.Logger,
    operator_id: str,
    *,
    entry: str = "direct",
) -> ImportDiagSession:
    """Start diagnostics for operators with no filepath (scene toggles, etc.)."""
    run_id = new_run_id()
    log_op_start(
        log,
        operator_id=operator_id,
        run_id=run_id,
        entry=entry,
        basename="",
        path_id="",
    )
    return ImportDiagSession(
        log=log,
        operator_id=operator_id,
        run_id=run_id,
        t0=time.perf_counter(),
    )


def run_simple_operator_logged(
    log: logging.Logger,
    operator_id: str,
    body: Callable[[], set[str]],
    *,
    entry: str = "direct",
) -> set[str]:
    """Run ``body`` with ``op_start`` / ``op_end`` (no filepath fields).

    Maps exceptions to ``reason_code`` like import operators. Returns the set from
    ``body``, or ``{\"CANCELLED\"}`` after an uncaught exception.
    """
    session = begin_simple_operator_diag(log, operator_id, entry=entry)
    work_done = False
    reason_code = LogReasonCode.OK
    outcome = "FINISHED"
    ret: set[str] = {"CANCELLED"}
    try:
        ret = body()
        work_done = ret == {"FINISHED"}
        outcome = "FINISHED" if work_done else "CANCELLED"
    except OSError as ex:
        outcome = "ERROR"
        work_done = False
        reason_code = (
            LogReasonCode.MISSING_FILE
            if isinstance(ex, FileNotFoundError)
            else LogReasonCode.IO_ERROR
        )
        log.exception(
            "event=op_error operator_id=%s run_id=%s reason_code=%s",
            operator_id,
            session.run_id,
            reason_code.value,
            exc_info=True,
        )
        ret = {"CANCELLED"}
    except Exception:
        outcome = "ERROR"
        work_done = False
        reason_code = LogReasonCode.INTERNAL_ERROR
        log.exception(
            "event=op_error operator_id=%s run_id=%s reason_code=%s",
            operator_id,
            session.run_id,
            reason_code.value,
            exc_info=True,
        )
        ret = {"CANCELLED"}
    finally:
        end_import_operator_diag(
            session,
            outcome=outcome,
            work_done=work_done,
            reason_code=reason_code,
        )
    return ret


def begin_import_operator_diag(
    log: logging.Logger,
    operator_id: str,
    operator: object,
    filepath: str,
) -> ImportDiagSession:
    run_id = new_run_id()
    entry = get_import_entry(operator)
    bn = import_basename(filepath)
    pid = path_id_for_filepath(filepath)
    log_op_start(
        log,
        operator_id=operator_id,
        run_id=run_id,
        entry=entry,
        basename=bn,
        path_id=pid,
    )
    return ImportDiagSession(
        log=log,
        operator_id=operator_id,
        run_id=run_id,
        t0=time.perf_counter(),
    )


def end_import_operator_diag(
    session: ImportDiagSession,
    *,
    outcome: str,
    work_done: bool,
    reason_code: LogReasonCode,
) -> None:
    duration_ms = int((time.perf_counter() - session.t0) * 1000)
    log_op_end(
        session.log,
        operator_id=session.operator_id,
        run_id=session.run_id,
        outcome=outcome,
        work_done=work_done,
        reason_code=reason_code.value,
        duration_ms=duration_ms,
    )
