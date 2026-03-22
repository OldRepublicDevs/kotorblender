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


class KB_OT_export_mdl(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.mdlexport"
    bl_label = "Export KotOR MDL"
    bl_description = "Export the selected KotOR model to binary MDL/MDX format"

    filename_ext = ".mdl"

    filter_glob: bpy.props.StringProperty(default="*.mdl", options={"HIDDEN"})

    export_for_tsl: bpy.props.BoolProperty(
        name="Export for TSL",
        description="Use The Sith Lords MDL format",
    )

    export_for_xbox: bpy.props.BoolProperty(
        name="Export for Xbox",
        description="Use Xbox MDL format",
    )

    export_animations: bpy.props.BoolProperty(name="Export Animations", default=True)

    export_walkmeshes: bpy.props.BoolProperty(
        name="Export Walkmeshes",
        description="Import area, door and placeable walkmeshes",
        default=True,
    )

    compress_quaternions: bpy.props.BoolProperty(name="Compress Quaternions", default=False)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_filepath_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ExportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.mdl.export")
        session = begin_import_operator_diag(
            log, "kb.mdlexport", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.INTERNAL_ERROR
        options = ExportOptions()
        options.export_for_tsl = self.export_for_tsl
        options.export_for_xbox = self.export_for_xbox
        options.export_animations = self.export_animations
        options.export_walkmeshes = self.export_walkmeshes
        options.compress_quaternions = self.compress_quaternions

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
                "kb.mdlexport",
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
                "kb.mdlexport",
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
