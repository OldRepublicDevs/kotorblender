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
from ...format.tpc.reader import TpcReader
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import convert_pykotor_tpc_to_tpcimage, get_use_pykotor_readers, is_pykotor_available, load_tpc_via_pykotor


class KB_OT_extract_tpc_textures(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.extract_tpc_textures"
    bl_label = "Extract TPC Textures"
    bl_description = "Extract textures from TPC files to TGA format"

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="*.tpc", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_filepath_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ExportHelper.invoke(self, context, event)

    def _execute_extract_tpc_textures_core(self, context: bpy.types.Context) -> set[str]:
        if not os.path.isdir(self.filepath):
            self.report({"ERROR"}, f"Directory not found: {self.filepath}")
            return {"CANCELLED"}

        # Find all TPC files in the directory
        tpc_files = [f for f in os.listdir(self.filepath) if f.lower().endswith(".tpc")]
        if not tpc_files:
            self.report({"WARNING"}, f"No TPC files found in: {self.filepath}")
            return {"CANCELLED"}

        converted = 0
        failed = 0

        for tpc_filename in tpc_files:
            tpc_path = os.path.join(self.filepath, tpc_filename)
            if not os.path.isfile(tpc_path):
                continue

            # Load TPC using PyKotor or current reader
            tpc_image = None
            if get_use_pykotor_readers() and is_pykotor_available():
                pykotor_tpc = load_tpc_via_pykotor(tpc_path)
                if pykotor_tpc:
                    tpc_image = convert_pykotor_tpc_to_tpcimage(pykotor_tpc)
                if not tpc_image:
                    # Fallback to current reader
                    try:
                        tpc_image = TpcReader(tpc_path).load()
                    except Exception:
                        failed += 1
                        continue
            else:
                # Use current reader
                try:
                    tpc_image = TpcReader(tpc_path).load()
                except Exception:
                    failed += 1
                    continue

            if not tpc_image:
                failed += 1
                continue

            # Create Blender image and save as TGA
            temp_name = tpc_filename[:-4]  # Remove .tpc extension
            image = bpy.data.images.new(temp_name, tpc_image.w, tpc_image.h)
            image.pixels = tpc_image.pixels
            image.update()

            tga_path = os.path.join(self.filepath, temp_name + ".tga")
            image.filepath = tga_path
            image.file_format = "TARGA"
            image.save()

            # Clean up temporary image
            bpy.data.images.remove(image)
            converted += 1

        if converted > 0:
            self.report({"INFO"}, f"Extracted {converted} TPC texture(s) to TGA format")
        if failed > 0:
            self.report({"WARNING"}, f"Failed to extract {failed} TPC file(s)")

        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.texture.extract_tpc_textures")
        session = begin_import_operator_diag(
            log, "kb.extract_tpc_textures", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_extract_tpc_textures_core(context)
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
                "kb.extract_tpc_textures",
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
                "kb.extract_tpc_textures",
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
