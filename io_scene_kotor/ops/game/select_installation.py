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
from ...log_config import get_kb_logger


class KB_OT_select_game_installation(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.select_game_installation"
    bl_label = "Select Game Installation"
    bl_description = "Select the KotOR game installation directory"

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.game.select_installation")
        session = begin_import_operator_diag(
            log, "kb.select_game_installation", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            if not self.filepath:
                self.report({"ERROR"}, "No path selected")
                outcome = "CANCELLED"
                ret = {"CANCELLED"}
            else:
                # ImportHelper gives us a file path, but we need a directory
                directory = (
                    os.path.dirname(self.filepath) if os.path.isfile(self.filepath) else self.filepath
                )

                scene: bpy.types.Scene = context.scene
                kb = getattr(scene, "kb", None)
                if kb is None:
                    self.report({"ERROR"}, "Scene.kb is None")
                    outcome = "CANCELLED"
                    ret = {"CANCELLED"}
                else:
                    kb.game_installation_path = directory
                    self.report({"INFO"}, f"Game installation path set to: {directory}")
                    work_done = True
                    reason_code = LogReasonCode.OK
                    outcome = "FINISHED"
                    ret = {"FINISHED"}
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
                "kb.select_game_installation",
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
                "kb.select_game_installation",
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
