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

import difflib
import os
import subprocess

import bpy
from bpy_extras.io_utils import ImportHelper

from ...constants import LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_import_invoke_entry,
)
from ...log_config import get_kb_logger
from ...utils import kotor_addon_preferences


class KB_OT_kotor_diff(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.kotor_diff"
    bl_label = "KotorDiff (text)"
    bl_description = (
        "Pick file A via the file browser, set file B in the redo panel (bottom left), "
        "then run again — unified diff is written to a Text datablock; optional external "
        "diff from add-on preferences"
    )

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="*.*", options={"HIDDEN"})

    other_path: bpy.props.StringProperty(
        name="Other File",
        subtype="FILE_PATH",
        description="Second file to compare against",
        default="",
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout is None:
            return
        layout.label(text="After choosing file A, set file B here (adjust in redo panel):")
        layout.prop(self, "other_path")

    def _execute_kotor_diff_core(self, context: bpy.types.Context) -> set[str]:
        a = self.filepath
        b = (self.other_path or "").strip()
        if not a or not os.path.isfile(a):
            self.report({"ERROR"}, "Choose a valid first file.")
            return {"CANCELLED"}
        if not b or not os.path.isfile(b):
            self.report({"ERROR"}, "Set Other File to a valid path (Properties panel after running).")
            return {"CANCELLED"}

        try:
            with open(a, "rb") as fa:
                da = fa.read()
            with open(b, "rb") as fb:
                db = fb.read()
        except OSError as e:
            self.report({"ERROR"}, f"Read failed: {e}")
            return {"CANCELLED"}

        try:
            sa = da.decode("utf-8", errors="replace").splitlines(keepends=True)
            sb = db.decode("utf-8", errors="replace").splitlines(keepends=True)
        except Exception:
            self.report(
                {"INFO"},
                "Binary comparison: sizes differ" if da != db else "Binary comparison: identical size",
            )
            return {"FINISHED"}

        diff = difflib.unified_diff(sa, sb, fromfile=a, tofile=b)
        text_body = "".join(diff)
        if not text_body.strip():
            self.report({"INFO"}, "No textual differences.")
            return {"FINISHED"}

        name = "KotorDiff_Result"
        text = bpy.data.texts.get(name) or bpy.data.texts.new(name)
        text.clear()
        text.write(text_body)
        self.report({"INFO"}, f"Diff written to Text '{name}'. Open Text Editor to view.")

        aprefs = kotor_addon_preferences()
        ext_diff = str(getattr(aprefs, "external_diff_path", "") if aprefs else "").strip()
        if ext_diff and os.path.isfile(ext_diff):
            try:
                subprocess.run([ext_diff, a, b], check=False, timeout=120)  # noqa: S603
            except (OSError, subprocess.SubprocessError):
                pass

        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.kotor_diff")
        session = begin_import_operator_diag(
            log, "kb.kotor_diff", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_kotor_diff_core(context)
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
                "kb.kotor_diff",
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
                "kb.kotor_diff",
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
