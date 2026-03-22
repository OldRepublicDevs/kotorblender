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

from ...constants import ExportOptions, LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_filepath_invoke_entry,
)
from ...io import mdl
from ...log_config import get_kb_logger


class KB_OT_export_ascii_mdl(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.asciimdlexport"
    bl_label = "Export KotOR ASCII MDL"
    bl_description = "Export the selected KotOR model to ASCII MDL format (.mdl.ascii)"

    filename_ext = ".mdl.ascii"

    filter_glob: bpy.props.StringProperty(default="*.mdl.ascii;*.ascii", options={"HIDDEN"})

    export_animations: bpy.props.BoolProperty(name="Export Animations", default=True)

    export_walkmeshes: bpy.props.BoolProperty(
        name="Export Walkmeshes",
        description="Export area, door and placeable walkmeshes",
        default=True,
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_filepath_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ExportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.mdl.ascii_export")
        session = begin_import_operator_diag(
            log, "kb.asciimdlexport", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.INTERNAL_ERROR
        options = ExportOptions()
        options.export_for_tsl = False  # ASCII format doesn't support TSL/Xbox variants
        options.export_for_xbox = False
        options.export_animations = self.export_animations
        options.export_walkmeshes = self.export_walkmeshes
        options.compress_quaternions = False  # ASCII format doesn't use quaternion compression

        try:
            mdl.save_mdl(self, self.filepath, options)
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
                "kb.asciimdlexport",
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
                "kb.asciimdlexport",
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
