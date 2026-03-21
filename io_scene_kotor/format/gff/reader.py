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

from struct import pack, unpack

from ...format.binreader import BinaryReader

from .types import (
    FILE_VERSION,
    FIELD_TYPE_DWORD,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_LIST,
    FIELD_TYPE_STRUCT,
    GffField,
    GffStruct,
    KeyValue,
)


class GffReader:
    def __init__(self, path: str, file_type: str) -> None:
        self.reader: BinaryReader = BinaryReader(path, "little")
        self.file_type: str = file_type.ljust(4)

    def load(self) -> dict[str, object]:
        file_type = self.reader.read_string(4)
        file_version = self.reader.read_string(4)

        if file_type != self.file_type:
            raise RuntimeError(
                f"GFF file type is invalid: expected='{self.file_type}', actual='{file_type}'",
            )
        if file_version != FILE_VERSION:
            raise RuntimeError(
                f"GFF file version is invalid: expected='{FILE_VERSION}', actual='{file_version}'",
            )

        self.off_structs = self.reader.read_uint32()
        self.num_structs = self.reader.read_uint32()
        self.off_fields = self.reader.read_uint32()
        self.num_fields = self.reader.read_uint32()
        self.off_labels = self.reader.read_uint32()
        self.num_labels = self.reader.read_uint32()
        self.off_field_data = self.reader.read_uint32()
        self.num_field_data = self.reader.read_uint32()
        self.off_field_indices = self.reader.read_uint32()
        self.num_field_indices = self.reader.read_uint32()
        self.off_list_indices = self.reader.read_uint32()
        self.num_list_indices = self.reader.read_uint32()

        self.load_structs()
        self.load_fields()
        self.load_labels()
        self.load_field_indices()
        self.load_list_indices()

        return self.new_tree_struct(0)

    def load_structs(self) -> None:
        self.structs = []
        self.reader.seek(self.off_structs)
        for _ in range(self.num_structs):
            struct = GffStruct(
                self.reader.read_uint32(),
                self.reader.read_uint32(),
                self.reader.read_uint32(),
            )
            self.structs.append(struct)

    def load_fields(self) -> None:
        self.fields = []
        self.reader.seek(self.off_fields)
        for _ in range(self.num_fields):
            field = GffField(
                self.reader.read_uint32(),
                self.reader.read_uint32(),
                self.reader.read_uint32(),
            )
            self.fields.append(field)

    def load_labels(self):
        self.reader.seek(self.off_labels)
        self.labels = [self.reader.read_string(16).rstrip("\0") for _ in range(self.num_labels)]

    def load_field_data(self) -> None:
        self.reader.seek(self.off_field_data)
        self.field_data = self.reader.read_bytes(self.num_field_data)

    def load_field_indices(self) -> None:
        self.reader.seek(self.off_field_indices)
        self.field_indices = [self.reader.read_uint32() for _ in range(self.num_field_indices // 4)]

    def load_list_indices(self) -> None:
        self.reader.seek(self.off_list_indices)
        self.list_indices = [self.reader.read_uint32() for _ in range(self.num_list_indices // 4)]

    def new_tree_struct(self, structIdx: int) -> dict[str, object]:
        tree: dict[str, object] = {}
        struct = self.structs[structIdx]
        nodes = []
        if struct.num_fields == 1:
            nodes.append(self.new_tree_field(struct.data_or_data_offset))
        else:
            start = struct.data_or_data_offset // 4
            stop = start + struct.num_fields
            for index in self.field_indices[start:stop]:
                nodes.append(self.new_tree_field(index))
        for node in nodes:
            tree[node.key] = node.value
        return tree

    def new_tree_field(self, field_idx: int) -> KeyValue:
        field: GffField = self.fields[field_idx]
        label = self.labels[field.label_idx]

        if field.type == FIELD_TYPE_DWORD:
            data = field.data_or_data_offset
        elif field.type == FIELD_TYPE_FLOAT:
            data = self.repack_int_to_float(field.data_or_data_offset)
        elif field.type == FIELD_TYPE_STRUCT:
            data = self.new_tree_struct(field.data_or_data_offset)
        elif field.type == FIELD_TYPE_LIST:
            list_idx = field.data_or_data_offset // 4
            if list_idx >= len(self.list_indices):
                raise RuntimeError(
                    f"GFF list index out of range: index={list_idx}, count={len(self.list_indices)}",
                )
            size = self.list_indices[list_idx]
            start = list_idx + 1
            stop = start + size
            if stop > len(self.list_indices):
                raise RuntimeError(
                    f"GFF list entries out of range: start={start}, stop={stop}, count={len(self.list_indices)}",
                )
            indices = self.list_indices[start:stop]
            data = [self.new_tree_struct(idx) for idx in indices]
        else:
            raise NotImplementedError(f"Field type {field.type} is not supported")

        return KeyValue(label, data)

    def repack_int_to_float(self, val: int) -> float:
        packed = pack("I", val)
        return unpack("f", packed)[0]
