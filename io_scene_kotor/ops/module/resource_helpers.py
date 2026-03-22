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

from __future__ import annotations

import os
import tempfile
from typing import Any

from ...constants import ResourceStorage
from ...diagnostic_log import path_id_for_filepath, sanitize_scene_context
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import get_bif_resource_bytes, get_erf_resource_bytes


def clear_resource_list(kb: Any) -> None:
    rl = kb.resource_list
    try:
        n = len(rl)
    except TypeError:
        n = -1
    get_kb_logger("ops.module.resource_helpers").debug("event=resource_list op=clear count=%s", n)
    rl.clear()


def add_resource_entry(
    kb: Any,
    *,
    label: str,
    resref: str,
    restype_ext: str,
    storage: str,
    erf_path: str = "",
    loose_path: str = "",
) -> None:
    e = kb.resource_list.add()
    e.label = label
    e.resref = resref
    e.restype_ext = restype_ext.lower().lstrip(".")
    e.storage = storage
    e.erf_path = erf_path
    e.loose_path = loose_path
    get_kb_logger("ops.module.resource_helpers").debug(
        "event=resource_list op=add storage=%s resref=%s restype=%s path_id=%s",
        storage,
        sanitize_scene_context(resref),
        e.restype_ext,
        path_id_for_filepath(loose_path) if loose_path else path_id_for_filepath(erf_path),
    )


def resource_entry_bytes(entry: Any) -> bytes | None:
    """Load raw bytes for a module browser resource row."""
    log = get_kb_logger("ops.module.resource_helpers")
    rr = sanitize_scene_context(str(getattr(entry, "resref", "")))
    rt = str(getattr(entry, "restype_ext", "")).lower().lstrip(".")
    if entry.storage == ResourceStorage.LOOSE:
        lp = entry.loose_path
        if lp and os.path.isfile(lp):
            with open(lp, "rb") as fh:
                data = fh.read()
            log.debug(
                "event=resource_bytes storage=LOOSE resref=%s restype=%s bytes=%s path_id=%s",
                rr,
                rt,
                len(data),
                path_id_for_filepath(lp),
            )
            return data
        log.debug(
            "event=resource_bytes storage=LOOSE resref=%s miss path_id=%s",
            rr,
            path_id_for_filepath(lp) if lp else "",
        )
        return None
    if entry.storage == ResourceStorage.ERF:
        erf_path = str(getattr(entry, "erf_path", "") or "")
        out = get_erf_resource_bytes(entry.erf_path, entry.resref, entry.restype_ext)
        log.debug(
            "event=resource_bytes storage=ERF resref=%s restype=%s hit=%s bytes=%s erf_path_id=%s",
            rr,
            rt,
            out is not None,
            len(out) if out else 0,
            path_id_for_filepath(erf_path),
        )
        return out
    if entry.storage == ResourceStorage.BIF:
        bif_key = str(getattr(entry, "erf_path", "") or "")
        out = get_bif_resource_bytes(entry.erf_path, entry.resref, entry.restype_ext)
        log.debug(
            "event=resource_bytes storage=BIF resref=%s restype=%s hit=%s bytes=%s key_path_id=%s",
            rr,
            rt,
            out is not None,
            len(out) if out else 0,
            path_id_for_filepath(bif_key),
        )
        return out
    log.debug("event=resource_bytes storage=unknown resref=%s raw=%s", rr, entry.storage)
    return None


def write_bytes_to_filepath(data: bytes, filepath: str) -> None:
    get_kb_logger("ops.module.resource_helpers").debug(
        "event=resource_write path_id=%s bytes=%s",
        path_id_for_filepath(filepath),
        len(data),
    )
    directory = os.path.dirname(os.path.abspath(filepath))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filepath, "wb") as fh:
        fh.write(data)


def temp_file_with_suffix(suffix: str, data: bytes) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    get_kb_logger("ops.module.resource_helpers").debug(
        "event=resource_temp suffix=%s bytes=%s path_id=%s",
        suffix,
        len(data),
        path_id_for_filepath(path),
    )
    return path
