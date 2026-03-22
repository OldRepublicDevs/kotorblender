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
from bpy_extras.io_utils import ImportHelper

from ...constants import ImportOptions, LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_import_invoke_entry,
)
from ...io import lyt
from ...log_config import get_kb_logger


class KB_OT_import_lyt(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.lytimport"
    bl_label = "Import KotOR LYT"
    bl_description = "Import a KotOR area layout file (.lyt) with room and instance references"
    bl_options = {"UNDO"}

    filename_ext = ".lyt"

    filter_glob: bpy.props.StringProperty(default="*.lyt", options={"HIDDEN"})

    import_animations: bpy.props.BoolProperty(name="Import Animations", default=True)

    import_walkmeshes: bpy.props.BoolProperty(
        name="Import Walkmeshes",
        description="Import area, placeable and door walkmeshes",
        default=True,
    )

    build_materials: bpy.props.BoolProperty(
        name="Build Materials",
        description="Build object materials",
        default=True,
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """When filepath is set (e.g. drag-and-drop), run execute(); otherwise open file browser."""
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.lyt.importop")
        session = begin_import_operator_diag(
            log, "kb.lytimport", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.INTERNAL_ERROR
        options = ImportOptions()
        options.import_animations = self.import_animations
        options.import_walkmeshes = self.import_walkmeshes
        options.build_materials = self.build_materials

        # Texture/lightmap search paths are built in load_mdl() (called by load_lyt()) from addon preferences
        # if not already set. Operators can still override by setting them here if needed.

        try:
            lyt.load_lyt(self, self.filepath, options)
            work_done = True
            reason_code = LogReasonCode.OK
        except OSError as e:
            outcome = "ERROR"
            reason_code = (
                LogReasonCode.MISSING_FILE
                if isinstance(e, FileNotFoundError)
                else LogReasonCode.IO_ERROR
            )
            log.exception(
                "event=op_error operator_id=%s run_id=%s reason_code=%s",
                "kb.lytimport",
                session.run_id,
                reason_code.value,
                exc_info=True,
            )
            self.report({"ERROR"}, str(e))
        except Exception as e:
            outcome = "ERROR"
            reason_code = LogReasonCode.INTERNAL_ERROR
            log.exception(
                "event=op_error operator_id=%s run_id=%s reason_code=%s",
                "kb.lytimport",
                session.run_id,
                reason_code.value,
                exc_info=True,
            )
            self.report({"ERROR"}, str(e))
        finally:
            end_import_operator_diag(
                session,
                outcome=outcome,
                work_done=work_done,
                reason_code=reason_code,
            )

        return {"FINISHED"}
