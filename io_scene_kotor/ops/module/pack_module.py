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
from bpy_extras.io_utils import ExportHelper

from ...constants import LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    set_filepath_invoke_entry,
)
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import is_pykotor_available


class KB_OT_pack_module(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.pack_module"
    bl_label = "Pack Module"
    bl_description = "Pack loose files from Pack Source Folder into a .mod / .erf using PyKotor"

    filename_ext = ".mod"
    filter_glob: bpy.props.StringProperty(default="*.mod;*.erf", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_filepath_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ExportHelper.invoke(self, context, event)

    def _execute_pack_module_core(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        kb = context.scene.kb
        src = str(kb.pack_source_directory or "").strip()
        if not src or not os.path.isdir(src):
            self.report(
                {"ERROR"},
                "Set Pack Source Folder in View3D sidebar (N) → KotOR → Module Designer.",
            )
            return {"CANCELLED"}

        try:
            from pykotor.resource.formats.erf import write_erf
            from pykotor.resource.formats.erf.erf_data import ERF, ERFType
            from pykotor.resource.type import ResourceType
        except ImportError:
            self.report({"ERROR"}, "PyKotor ERF modules could not be imported.")
            return {"CANCELLED"}

        erf = ERF(ERFType.MOD)
        count = 0
        for dirpath, _dirnames, filenames in os.walk(src):
            for fn in filenames:
                path = os.path.join(dirpath, fn)
                if not os.path.isfile(path):
                    continue
                base, ext = os.path.splitext(fn)
                ext_l = ext.lstrip(".").lower() or "dat"
                dot = "." + ext_l
                try:
                    rt = ResourceType.from_extension(dot)
                except (ValueError, KeyError, TypeError):
                    continue
                resref = (base or "resource")[:16]
                try:
                    with open(path, "rb") as fh:
                        data = fh.read()
                except OSError:
                    continue
                erf.set_data(resref, rt, data)
                count += 1

        if count == 0:
            self.report({"WARNING"}, "No packable files found (check extensions PyKotor recognizes).")
            return {"CANCELLED"}

        try:
            write_erf(erf, self.filepath)
        except Exception as e:
            self.report({"ERROR"}, f"Pack failed: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Packed {count} resource(s) to {self.filepath}")
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.module.pack_module")
        session = begin_import_operator_diag(log, "kb.pack_module", self, self.filepath or "")
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_pack_module_core(context)
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
                "kb.pack_module",
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
                "kb.pack_module",
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
