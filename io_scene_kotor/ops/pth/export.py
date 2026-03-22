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

import bpy
from bpy_extras.io_utils import ExportHelper

from ...constants import LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_filepath_invoke_entry,
)
from ...io import pth
from ...log_config import get_kb_logger


class KB_OT_export_pth(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.pthexport"
    bl_label = "Export KotOR PTH"
    bl_description = "Export path point objects to a KotOR path file (.pth)"

    filename_ext = ".pth"

    filter_glob: bpy.props.StringProperty(default="*.pth", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_filepath_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ExportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.pth.export")
        session = begin_import_operator_diag(
            log, "kb.pthexport", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.INTERNAL_ERROR
        try:
            pth.save_pth(self, self.filepath)
            work_done = True
            reason_code = LogReasonCode.OK
        except OSError as ex:
            outcome = "ERROR"
            reason_code = (
                LogReasonCode.MISSING_FILE
                if isinstance(ex, FileNotFoundError)
                else LogReasonCode.IO_ERROR
            )
            log.exception(
                "event=op_error operator_id=%s run_id=%s reason_code=%s",
                "kb.pthexport",
                session.run_id,
                reason_code.value,
                exc_info=True,
            )
            self.report({"ERROR"}, str(ex))
        except Exception as ex:
            outcome = "ERROR"
            reason_code = LogReasonCode.INTERNAL_ERROR
            log.exception(
                "event=op_error operator_id=%s run_id=%s reason_code=%s",
                "kb.pthexport",
                session.run_id,
                reason_code.value,
                exc_info=True,
            )
            self.report({"ERROR"}, str(ex))
        finally:
            end_import_operator_diag(
                session,
                outcome=outcome,
                work_done=work_done,
                reason_code=reason_code,
            )

        return {"FINISHED"}
