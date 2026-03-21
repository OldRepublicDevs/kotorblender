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
from ...vendor.pykotor_adapter import get_bif_resource_bytes, get_erf_resource_bytes


def clear_resource_list(kb: Any) -> None:
    kb.resource_list.clear()


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


def resource_entry_bytes(entry: Any) -> bytes | None:
    """Load raw bytes for a module browser resource row."""
    if entry.storage == ResourceStorage.LOOSE:
        lp = entry.loose_path
        if lp and os.path.isfile(lp):
            with open(lp, "rb") as fh:
                return fh.read()
        return None
    if entry.storage == ResourceStorage.ERF:
        return get_erf_resource_bytes(entry.erf_path, entry.resref, entry.restype_ext)
    if entry.storage == ResourceStorage.BIF:
        return get_bif_resource_bytes(entry.erf_path, entry.resref, entry.restype_ext)
    return None


def write_bytes_to_filepath(data: bytes, filepath: str) -> None:
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
    return path
