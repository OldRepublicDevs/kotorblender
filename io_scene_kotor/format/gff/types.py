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

FILE_VERSION = "V3.2"

FIELD_TYPE_DWORD = 4
FIELD_TYPE_FLOAT = 8
FIELD_TYPE_STRUCT = 14
FIELD_TYPE_LIST = 15


class KeyValue:
    def __init__(self, key: str, value: int | float | dict[str, object] | list[dict[str, object]]) -> None:
        self.key: str = key
        self.value: int | float | dict[str, object] | list[dict[str, object]] = value


class GffStruct:
    def __init__(self, type: int, data_or_data_offset: int, num_fields: int) -> None:
        self.type: int = type
        self.data_or_data_offset: int = data_or_data_offset
        self.num_fields: int = num_fields


class GffField:
    def __init__(self, type: int, label_idx: int, data_or_data_offset: int) -> None:
        self.type: int = type
        self.label_idx: int = label_idx
        self.data_or_data_offset: int = data_or_data_offset
