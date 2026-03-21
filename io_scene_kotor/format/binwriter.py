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

import struct
from typing import BinaryIO, Literal


class BinaryWriter:
    def __init__(
        self, path: str, byteorder: Literal["little", "big"] = "little"
    ) -> None:
        self.file: BinaryIO = open(path, "wb")
        self.byteorder: Literal["little", "big"] = byteorder

    def __del__(self) -> None:
        file_handle = getattr(self, "file", None)
        if file_handle is not None:
            try:
                file_handle.close()
            except Exception:
                pass

    def tell(self) -> int:
        return self.file.tell()

    def write_int8(self, val: int) -> None:
        self.file.write(val.to_bytes(1, byteorder=self.byteorder, signed=True))

    def write_int16(self, val: int) -> None:
        self.file.write(val.to_bytes(2, byteorder=self.byteorder, signed=True))

    def write_int32(self, val: int) -> None:
        self.file.write(val.to_bytes(4, byteorder=self.byteorder, signed=True))

    def write_uint8(self, val: int) -> None:
        self.file.write(val.to_bytes(1, byteorder=self.byteorder, signed=False))

    def write_uint16(self, val: int) -> None:
        self.file.write(val.to_bytes(2, byteorder=self.byteorder, signed=False))

    def write_uint32(self, val: int) -> None:
        self.file.write(val.to_bytes(4, byteorder=self.byteorder, signed=False))

    def write_float(self, val: float) -> None:
        bo_literal = ">" if self.byteorder == "big" else "<"
        self.file.write(struct.pack(bo_literal + "f", val))

    def write_string(self, val: str) -> None:
        self.file.write(val.encode("utf-8"))

    def write_c_string(self, val: str) -> None:
        self.file.write((val + "\0").encode("utf-8"))

    def write_bytes(self, data: bytes) -> None:
        self.file.write(data)
