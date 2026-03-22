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
from ...format.tpc.reader import TpcReader
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import (
    convert_pykotor_tpc_to_tpcimage,
    get_use_pykotor_readers,
    is_pykotor_available,
    load_tpc_via_pykotor,
)


class KB_OT_convert_tpc_to_tga(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.convert_tpc_to_tga"
    bl_label = "Convert TPC to TGA"
    bl_description = "Convert KotOR TPC texture to TGA format"

    filename_ext = ".tpc"
    filter_glob: bpy.props.StringProperty(default="*.tpc", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def _execute_convert_tpc_to_tga_core(self, context: bpy.types.Context) -> set[str]:
        if not os.path.isfile(self.filepath):
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}

        tpc_image = None
        if get_use_pykotor_readers() and is_pykotor_available():
            pykotor_tpc = load_tpc_via_pykotor(self.filepath)
            if pykotor_tpc:
                tpc_image = convert_pykotor_tpc_to_tpcimage(pykotor_tpc)
            if not tpc_image:
                try:
                    tpc_image = TpcReader(self.filepath).load()
                except Exception as e:
                    self.report({"ERROR"}, f"Failed to load TPC (PyKotor and fallback failed): {e}")
                    return {"CANCELLED"}
        else:
            try:
                tpc_image = TpcReader(self.filepath).load()
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load TPC: {e}")
                return {"CANCELLED"}

        if not tpc_image:
            self.report({"ERROR"}, "Failed to load TPC file")
            return {"CANCELLED"}

        temp_name = os.path.basename(self.filepath)[:-4]
        image = bpy.data.images.new(temp_name, tpc_image.w, tpc_image.h)
        image.pixels = tpc_image.pixels
        image.update()

        tga_path = self.filepath[:-4] + ".tga"
        image.filepath = tga_path
        image.file_format = "TARGA"
        image.save()

        bpy.data.images.remove(image)

        self.report({"INFO"}, f"Converted TPC to TGA: {tga_path}")
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.texture.convert_tpc_to_tga")
        session = begin_import_operator_diag(
            log, "kb.convert_tpc_to_tga", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_convert_tpc_to_tga_core(context)
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
                "kb.convert_tpc_to_tga",
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
                "kb.convert_tpc_to_tga",
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
