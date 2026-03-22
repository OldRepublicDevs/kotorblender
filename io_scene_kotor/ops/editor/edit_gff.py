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

import bpy
from bpy_extras.io_utils import ImportHelper

from ...constants import LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_import_invoke_entry,
)
from ...format.gff.reader import GffReader
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import convert_pykotor_gff_to_tree, get_use_pykotor_readers, is_pykotor_available, load_gff_via_pykotor


class KB_OT_edit_gff(bpy.types.Operator, ImportHelper):  # pyright: ignore[reportIncompatibleMethodOverride]
    bl_idname = "kb.edit_gff"
    bl_label = "Edit GFF File"
    bl_description = "Edit a KotOR GFF file (loads GFF structure for editing)"

    filename_ext = ".gff"
    filter_glob: bpy.props.StringProperty(default="*.gff", options={"HIDDEN"})  # pyright: ignore[reportInvalidTypeForm]

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def _execute_edit_gff_core(self, context: bpy.types.Context) -> set[str]:
        if not os.path.isfile(self.filepath):  # pyright: ignore[reportAttributeAccessIssue]
            self.report({"ERROR"}, f"File not found: {self.filepath}")  # pyright: ignore[reportAttributeAccessIssue]
            return {"CANCELLED"}

        # Load GFF using PyKotor or current reader
        tree = None
        if get_use_pykotor_readers() and is_pykotor_available():
            pykotor_gff = load_gff_via_pykotor(self.filepath)  # pyright: ignore[reportAttributeAccessIssue]
            if pykotor_gff:
                tree = convert_pykotor_gff_to_tree(pykotor_gff)
            if not tree:
                # Fallback to current reader
                try:
                    # Infer file type from filename or use generic
                    file_type = os.path.splitext(os.path.basename(self.filepath))[0].upper()[:4]  # pyright: ignore[reportAttributeAccessIssue]
                    if len(file_type) < 4:
                        file_type = "GFF "
                    loader = GffReader(self.filepath, file_type)  # pyright: ignore[reportAttributeAccessIssue]
                    tree = loader.load()
                except Exception as e:
                    self.report({"ERROR"}, f"Failed to load GFF (PyKotor and fallback failed): {e}")
                    return {"CANCELLED"}
        else:
            # Use current reader
            try:
                file_type = os.path.splitext(os.path.basename(self.filepath))[0].upper()[:4]  # pyright: ignore[reportAttributeAccessIssue]
                if len(file_type) < 4:
                    file_type = "GFF "
                loader = GffReader(self.filepath, file_type)  # pyright: ignore[reportAttributeAccessIssue]
                tree = loader.load()
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load GFF: {e.__class__.__name__}: {e}")
                return {"CANCELLED"}

        if not tree:
            self.report({"ERROR"}, "Failed to load GFF file")
            return {"CANCELLED"}

        # GFF editor UI (tree view) planned for a future release.
        self.report(
            {"INFO"},
            f"Loaded GFF file: {self.filepath} (struct type: {tree.get('_type', 'unknown')})",  # pyright: ignore[reportAttributeAccessIssue]
        )
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.editor.edit_gff")
        session = begin_import_operator_diag(log, "kb.edit_gff", self, self.filepath or "")
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_edit_gff_core(context)
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
                "kb.edit_gff",
                session.run_id,
                reason_code.value,
                exc_info=True,
            )
            self.report({"ERROR"}, str(ex))
            ret = {"CANCELLED"}
        except Exception as ex:
            outcome = "ERROR"
            work_done = False
            reason_code = LogReasonCode.INTERNAL_ERROR
            log.exception(
                "event=op_error operator_id=%s run_id=%s reason_code=%s",
                "kb.edit_gff",
                session.run_id,
                reason_code.value,
                exc_info=True,
            )
            self.report({"ERROR"}, str(ex))
            ret = {"CANCELLED"}
        finally:
            end_import_operator_diag(
                session,
                outcome=outcome,
                work_done=work_done,
                reason_code=reason_code,
            )
        return ret
