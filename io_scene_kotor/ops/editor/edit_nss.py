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


def _find_text_editor_area(context: bpy.types.Context) -> bpy.types.SpaceTextEditor | None:
    """Return the first TEXT_EDITOR space found in any window, or None.

    Args:
        context: Blender context

    Returns:
        First TEXT_EDITOR space found, or None if no text editor area exists
    """
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "TEXT_EDITOR":
                continue
            for space in area.spaces:
                if space.type == "TEXT_EDITOR":
                    return space
    return None


class KB_OT_edit_nss(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.edit_nss"
    bl_label = "Edit Script"
    bl_description = "Open a KotOR Script (NSS) file in the Blender Text Editor"

    filename_ext = ".nss"
    filter_glob: bpy.props.StringProperty(default="*.nss", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def _execute_edit_nss_core(self, context: bpy.types.Context) -> set[str]:
        if not self.filepath or not os.path.isfile(self.filepath):
            self.report({"ERROR"}, "No valid NSS file path")
            return {"CANCELLED"}
        try:
            text_block = bpy.data.texts.load(self.filepath, internal=False)
        except Exception as ex:
            self.report({"ERROR"}, f"Failed to load NSS file: {ex}")
            return {"CANCELLED"}
        space = _find_text_editor_area(context)
        if space is not None:
            space.text = text_block
        self.report({"INFO"}, f"Opened NSS in Text Editor: {os.path.basename(self.filepath)}")
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.editor.edit_nss")
        session = begin_import_operator_diag(log, "kb.edit_nss", self, self.filepath or "")
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_edit_nss_core(context)
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
                "kb.edit_nss",
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
                "kb.edit_nss",
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
