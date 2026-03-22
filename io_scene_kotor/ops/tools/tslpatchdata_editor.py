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

"""TSLPatchData changes.ini load/save (stdlib configparser; no PyKotor required)."""

from __future__ import annotations

import configparser
import os

import bpy
from bpy_extras.io_utils import ImportHelper

from ...constants import LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    run_simple_operator_logged,
    set_import_invoke_entry,
)
from ...log_config import get_kb_logger


def tslpatch_config_parser() -> configparser.ConfigParser:
    """Match Holocron TSLPatchDataEditor ini parsing options."""
    return configparser.ConfigParser(
        delimiters=("=",),
        allow_no_value=True,
        strict=False,
        interpolation=None,
        inline_comment_prefixes=(";", "#"),
    )


def _abs_path(path: str) -> str:
    p = (path or "").strip()
    if not p:
        return ""
    try:
        return bpy.path.abspath(p)
    except Exception:
        return os.path.normpath(p)


def resolve_changes_ini_path(kb: bpy.types.PropertyGroup) -> str | None:
    """Path to ``changes.ini``: folder + changes.ini, or explicit ``.ini`` filepath."""
    folder = _abs_path(str(getattr(kb, "tslpatchdata_folder", "") or ""))
    if folder and os.path.isdir(folder):
        return os.path.join(folder, "changes.ini")
    fp = _abs_path(str(getattr(kb, "tslpatchdata_filepath", "") or ""))
    if fp.lower().endswith(".ini"):
        return fp
    return None


def sync_kb_settings_from_ini_text(text: str, kb: bpy.types.PropertyGroup) -> None:
    """Fill ``mod_name`` / ``mod_author`` from a ``[settings]`` section when parseable."""
    cp = tslpatch_config_parser()
    try:
        cp.read_string(text)
    except configparser.Error:
        return
    for sec in cp.sections():
        if sec.lower() != "settings":
            continue
        for opt in cp.options(sec):
            ol = opt.lower()
            val = (cp.get(sec, opt, fallback="") or "").strip()
            if ol == "modname":
                kb.tslpatchdata_mod_name = val
            elif ol == "author":
                kb.tslpatchdata_mod_author = val
        break


class KB_OT_tslpatchdata_editor(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.tslpatchdata_editor"
    bl_label = "TSLPatchData — Pick changes.ini"
    bl_description = "Choose a changes.ini; content loads into Scene → KotOR → TSLPatchData (edit and save there)"

    filename_ext = ".ini"
    filter_glob: bpy.props.StringProperty(default="*.ini", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def _execute_tslpatchdata_editor_core(self, context: bpy.types.Context) -> set[str]:
        fp = (self.filepath or "").strip()
        if not fp or not os.path.isfile(fp):
            self.report({"ERROR"}, "No valid INI file selected.")
            return {"CANCELLED"}
        kb = context.scene.kb
        kb.tslpatchdata_filepath = fp
        kb.tslpatchdata_folder = os.path.dirname(fp)
        try:
            with open(fp, encoding="utf-8", errors="replace") as f:
                body = f.read()
        except OSError as e:
            self.report({"ERROR"}, f"Could not read INI: {e}")
            return {"CANCELLED"}
        if len(body) > 65535:
            self.report({"ERROR"}, "INI exceeds 65535 characters (Blender string limit on scene.kb).")
            return {"CANCELLED"}
        kb.tslpatchdata_ini_body = body
        sync_kb_settings_from_ini_text(body, kb)
        self.report({"INFO"}, f"Loaded TSLPatchData INI into scene: {fp}")
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.tslpatchdata_editor")
        session = begin_import_operator_diag(
            log, "kb.tslpatchdata_editor", self, self.filepath or ""
        )
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_tslpatchdata_editor_core(context)
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
                "kb.tslpatchdata_editor",
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
                "kb.tslpatchdata_editor",
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


class KB_OT_tslpatchdata_load_changes_ini(bpy.types.Operator):
    bl_idname = "kb.tslpatchdata_load_changes_ini"
    bl_label = "Load changes.ini"
    bl_description = "Reload changes.ini from TSLPatchData folder or filepath on scene.kb"

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.tslpatchdata_load_changes_ini")

        def _body() -> set[str]:
            kb = context.scene.kb
            path = resolve_changes_ini_path(kb)
            if not path:
                self.report(
                    {"ERROR"},
                    "Set TSLPatchData folder or a .ini filepath on the scene (KotOR sidebar).",
                )
                return {"CANCELLED"}
            if not os.path.isfile(path):
                self.report({"ERROR"}, f"changes.ini not found: {path}")
                return {"CANCELLED"}
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    body = f.read()
            except OSError as e:
                self.report({"ERROR"}, f"Could not read: {e}")
                return {"CANCELLED"}
            if len(body) > 65535:
                self.report({"ERROR"}, "INI exceeds 65535 characters.")
                return {"CANCELLED"}
            kb.tslpatchdata_ini_body = body
            kb.tslpatchdata_filepath = path
            sync_kb_settings_from_ini_text(body, kb)
            self.report({"INFO"}, f"Loaded {path}")
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.tslpatchdata_load_changes_ini", _body)


class KB_OT_tslpatchdata_save_changes_ini(bpy.types.Operator):
    bl_idname = "kb.tslpatchdata_save_changes_ini"
    bl_label = "Save changes.ini"
    bl_description = "Write scene.kb changes.ini text to disk (folder or .ini path)"

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.tslpatchdata_save_changes_ini")

        def _body() -> set[str]:
            kb = context.scene.kb
            path = resolve_changes_ini_path(kb)
            if not path:
                self.report({"ERROR"}, "Set TSLPatchData folder or .ini filepath before saving.")
                return {"CANCELLED"}
            body = kb.tslpatchdata_ini_body or ""
            if not body.strip():
                self.report({"WARNING"}, "INI body is empty; writing minimal [settings] from mod name/author.")
                mod = (kb.tslpatchdata_mod_name or "My Mod").strip()
                auth = (kb.tslpatchdata_mod_author or "Unknown").strip()
                body = f"[settings]\nmodname={mod}\nauthor={auth}\n"
            parent = os.path.dirname(path)
            if parent and not os.path.isdir(parent):
                try:
                    os.makedirs(parent, exist_ok=True)
                except OSError as e:
                    self.report({"ERROR"}, f"Could not create folder: {e}")
                    return {"CANCELLED"}
            try:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(body)
            except OSError as e:
                self.report({"ERROR"}, f"Could not save: {e}")
                return {"CANCELLED"}
            kb.tslpatchdata_filepath = path
            self.report({"INFO"}, f"Saved {path}")
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.tslpatchdata_save_changes_ini", _body)
