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
import shutil

import bpy
from bpy_extras.io_utils import ExportHelper

from ...constants import LogReasonCode, ResourceStorage
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_filepath_invoke_entry,
)
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import is_pykotor_available
from .resource_helpers import resource_entry_bytes, write_bytes_to_filepath


class KB_OT_extract_resource(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.extract_resource"
    bl_label = "Extract Selected Resource"
    bl_description = "Extract the selected resource to disk (choose output folder + filename)"

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="*.*", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_filepath_invoke_entry(self)
        scene = context.scene
        kb = scene.kb
        if kb.resource_list_idx < 0 or kb.resource_list_idx >= len(kb.resource_list):
            self.report({"ERROR"}, "No resource selected")
            return {"CANCELLED"}
        entry = kb.resource_list[kb.resource_list_idx]
        ext = entry.restype_ext or "dat"
        self.filename_ext = "." + ext.lstrip(".")
        base = entry.resref or "resource"
        self.filepath = base + self.filename_ext
        return ExportHelper.invoke(self, context, event)

    def _execute_extract_resource_core(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        kb = scene.kb

        if kb.resource_list_idx < 0 or kb.resource_list_idx >= len(kb.resource_list):
            self.report({"ERROR"}, "No resource selected")
            return {"CANCELLED"}

        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        entry = kb.resource_list[kb.resource_list_idx]

        if (
            entry.storage == ResourceStorage.LOOSE
            and entry.loose_path
            and os.path.isfile(entry.loose_path)
        ):
            try:
                shutil.copy2(entry.loose_path, self.filepath)
            except OSError as e:
                self.report({"ERROR"}, f"Copy failed: {e}")
                return {"CANCELLED"}
            self.report({"INFO"}, f"Copied to {self.filepath}")
            return {"FINISHED"}

        data = resource_entry_bytes(entry)
        if not data:
            self.report({"ERROR"}, "Could not read resource data.")
            return {"CANCELLED"}
        try:
            write_bytes_to_filepath(data, self.filepath)
        except OSError as e:
            self.report({"ERROR"}, f"Write failed: {e}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Wrote {self.filepath}")
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.module.extract_resource")
        session = begin_import_operator_diag(log, "kb.extract_resource", self, self.filepath or "")
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_extract_resource_core(context)
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
                "kb.extract_resource",
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
                "kb.extract_resource",
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
