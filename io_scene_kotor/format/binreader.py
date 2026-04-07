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


class SeekOrigin:
    BEGIN = 0
    CURRENT = 1
    END = 2


class BinaryReader:
    def __init__(self, path: str, byteorder: Literal["little", "big"] = "little"):
        self.file: BinaryIO = open(path, "rb")
        self.byteorder: Literal["little", "big"] = byteorder

    def __del__(self):
        file_handle = getattr(self, "file", None)
        if file_handle is not None:
            try:
                file_handle.close()
            except Exception:
                pass

    def seek(self, offset: int, origin: int = SeekOrigin.BEGIN):
        self.file.seek(offset, origin)

    def skip(self, offset: int):
        self.file.seek(offset, SeekOrigin.CURRENT)

    def tell(self) -> int:
        return self.file.tell()

    def read_int8(self) -> int:
        return int.from_bytes(self.file.read(1), self.byteorder, signed=True)

    def read_int16(self) -> int:
        return int.from_bytes(self.file.read(2), self.byteorder, signed=True)

    def read_int32(self) -> int:
        return int.from_bytes(self.file.read(4), self.byteorder, signed=True)

    def read_uint8(self) -> int:
        return int.from_bytes(self.file.read(1), self.byteorder, signed=False)

    def read_uint16(self) -> int:
        return int.from_bytes(self.file.read(2), self.byteorder, signed=False)

    def read_uint32(self) -> int:
        return int.from_bytes(self.file.read(4), self.byteorder, signed=False)

    def read_float(self) -> float:
        bo_literal = ">" if self.byteorder == "big" else "<"
        [val] = struct.unpack(bo_literal + "f", self.file.read(4))
        return val

    def read_string(self, len: int) -> str:
        return self.file.read(len).decode("utf-8")

    def read_c_string(self) -> str:
        str = ""
        while True:
            raw = self.file.read(1)
            if not raw:
                break
            ch = raw.decode("utf-8")
            if ch == "\0":
                break
            str += ch
        return str

    def read_c_string_up_to(self, max_len: int) -> str:
        str = ""
        len = max_len
        while len > 0:
            ch = self.file.read(1).decode("utf-8")
            len -= 1
            if ch == "\0":
                break
            str += ch
        if len > 0:
            self.file.seek(len, 1)
        return str

    def read_bytes(self, count: int) -> bytes:
        return self.file.read(count)
