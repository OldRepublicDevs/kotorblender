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

"""Import / export KotOR GIT instances as Blender empties (viewport placement).

Uses PyKotor's ``GIT`` type (``read_git`` / ``write_git``). Trigger encounter
geometry polygons and spawn points are preserved from the on-disk file; only
root position (and bearing / camera orientation where applicable) are updated
from transformed empties on export.
"""

from __future__ import annotations

import os
import re
from typing import Any

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Euler, Quaternion

from ...constants import GameType, GitGeometryRole, GitInstanceSection, LogReasonCode
from ...diagnostic_log import (
    begin_import_operator_diag,
    end_import_operator_diag,
    run_simple_operator_logged,
    set_import_invoke_entry,
)
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import is_pykotor_available, load_git_via_pykotor, save_git_via_pykotor

from .git_geometry import import_git_polygons_and_spawns, sync_git_geometry_from_blender

_BLENDER_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _game_is_k2(scene: bpy.types.Scene) -> bool:
    kb = getattr(scene, "kb", None)
    if kb is None:
        return False
    gt = getattr(kb, "game_type", None)
    return gt == GameType.KOTOR2.value


def _sanitize_object_name(raw: str, max_len: int = 60) -> str:
    s = _BLENDER_NAME_RE.sub("_", raw.strip()).strip("._")
    if not s:
        s = "instance"
    return s[:max_len]


def _empty_display_for_section(section: str) -> str:
    if section == GitInstanceSection.CAMERAS.value:
        return "IMAGE"
    if section == GitInstanceSection.SOUNDS.value:
        return "SPHERE"
    return "PLAIN_AXES"


def _set_empty_from_git_instance(
    obj: bpy.types.Object,
    section: str,
    instance: Any,
) -> None:
    """Apply PyKotor GIT instance transform to a Blender empty."""
    pos = getattr(instance, "position", None)
    if pos is not None:
        obj.location = (float(pos.x), float(pos.y), float(pos.z))

    if section == GitInstanceSection.CAMERAS.value:
        obj.rotation_mode = "QUATERNION"
        orient = getattr(instance, "orientation", None)
        if orient is not None:
            obj.rotation_quaternion = Quaternion(
                (float(orient.w), float(orient.x), float(orient.y), float(orient.z)),
            )
        return

    obj.rotation_mode = "XYZ"
    yaw = getattr(instance, "yaw", None)
    if callable(yaw):
        yv = yaw()
        if yv is not None:
            obj.rotation_euler = Euler((0.0, 0.0, float(yv)), "XYZ")
            return
    bearing = getattr(instance, "bearing", None)
    if isinstance(bearing, (int, float)):
        obj.rotation_euler = Euler((0.0, 0.0, float(bearing)), "XYZ")


def _apply_empty_to_git_instance(obj: bpy.types.Object, section: str, instance: Any) -> None:
    """Write Blender empty world transform back onto a PyKotor GIT instance."""
    pos = obj.location
    instance.position.x = float(pos.x)
    instance.position.y = float(pos.y)
    instance.position.z = float(pos.z)

    if section == GitInstanceSection.CAMERAS.value:
        q = obj.rotation_quaternion
        orient = getattr(instance, "orientation", None)
        if orient is not None:
            orient.x = float(q.x)
            orient.y = float(q.y)
            orient.z = float(q.z)
            orient.w = float(q.w)
        return

    euler = obj.rotation_euler
    z = float(euler.z)
    if section in (
        GitInstanceSection.CREATURES.value,
        GitInstanceSection.STORES.value,
        GitInstanceSection.WAYPOINTS.value,
    ):
        instance.bearing = z
    elif section in (GitInstanceSection.DOORS.value, GitInstanceSection.PLACEABLES.value):
        instance.bearing = z


def _resref_str(instance: Any) -> str:
    rr = getattr(instance, "resref", None)
    if rr is None:
        return ""
    return str(rr)


def _link_empty_metadata(obj: bpy.types.Object, section: str, idx: int, resref: str) -> None:
    kb = getattr(obj, "kb", None)
    if kb is None:
        return
    kb.git_instance_section = section
    kb.git_instance_index = idx
    kb.git_instance_resref = resref[:32] if resref else ""


def _import_section(
    coll: bpy.types.Collection,
    section: str,
    instances: list[Any],
) -> int:
    created = 0
    for idx, inst in enumerate(instances):
        resref = _resref_str(inst)
        stem = f"git.{section}.{idx}.{_sanitize_object_name(resref or 'norefs')}"
        obj = bpy.data.objects.new(stem, None)
        obj.empty_display_type = _empty_display_for_section(section)
        obj.show_name = True
        _set_empty_from_git_instance(obj, section, inst)
        _link_empty_metadata(obj, section, idx, resref)
        coll.objects.link(obj)
        created += 1
    return created


class KB_OT_git_import_instances(bpy.types.Operator, ImportHelper):
    """Spawn empties for each GIT instance so they can be moved in the viewport."""

    bl_idname = "kb.git_import_instances"
    bl_label = "Import GIT Instances"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".git"
    filter_glob: bpy.props.StringProperty(default="*.git", options={"HIDDEN"})  # pyright: ignore[reportInvalidTypeForm]

    replace_collection: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Replace Existing Collection",
        description="Remove a prior collection with the same name (from a previous import of this file)",
        default=True,
    )
    import_git_geometry: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Import Trigger/Encounter Geometry",
        description="Create hull meshes for triggers/encounters and empties for encounter spawn points",
        default=True,
    )

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return is_pykotor_available()

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        set_import_invoke_entry(self)
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def _execute_git_import_instances_core(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available.")
            return {"CANCELLED"}

        fp = self.filepath
        if not fp or not os.path.isfile(os.fsencode(fp)):
            self.report({"ERROR"}, "GIT file not found.")
            return {"CANCELLED"}

        git_obj = load_git_via_pykotor(fp)
        if git_obj is None:
            self.report({"ERROR"}, f"Could not read GIT: {fp}")
            return {"CANCELLED"}

        base = os.path.splitext(os.path.basename(fp))[0]
        coll_name = _sanitize_object_name(f"GIT_{base}", max_len=63)
        if coll_name in bpy.data.collections and self.replace_collection:
            c_old = bpy.data.collections[coll_name]
            root = context.scene.collection
            if c_old.name in {ch.name for ch in root.children}:
                root.children.unlink(c_old)
            for o in list(c_old.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c_old)

        coll = bpy.data.collections.new(coll_name)
        context.scene.collection.children.link(coll)

        git: Any = git_obj
        total = 0
        sections: tuple[tuple[str, str], ...] = (
            (GitInstanceSection.CREATURES.value, "creatures"),
            (GitInstanceSection.DOORS.value, "doors"),
            (GitInstanceSection.PLACEABLES.value, "placeables"),
            (GitInstanceSection.TRIGGERS.value, "triggers"),
            (GitInstanceSection.WAYPOINTS.value, "waypoints"),
            (GitInstanceSection.STORES.value, "stores"),
            (GitInstanceSection.ENCOUNTERS.value, "encounters"),
            (GitInstanceSection.SOUNDS.value, "sounds"),
            (GitInstanceSection.CAMERAS.value, "cameras"),
        )
        for section, attr in sections:
            inst_list = getattr(git, attr, None)
            if isinstance(inst_list, list):
                total += _import_section(coll, section, inst_list)

        geom_n = 0
        if self.import_git_geometry:
            geom_n = import_git_polygons_and_spawns(coll, git)

        kb = getattr(context.scene, "kb", None)
        if kb is not None:
            kb.active_git_path = fp

        self.report(
            {"INFO"},
            f"Imported {total} GIT instance marker(s) + {geom_n} geometry helper(s) → '{coll_name}'.",
        )
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.git_instances")
        session = begin_import_operator_diag(log, "kb.git_import_instances", self, self.filepath or "")
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_git_import_instances_core(context)
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
                "kb.git_import_instances",
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
                "kb.git_import_instances",
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


class KB_OT_git_export_instances(bpy.types.Operator):
    """Apply linked empty transforms to the GIT on disk (reloads file, then writes)."""

    bl_idname = "kb.git_export_instances"
    bl_label = "Export GIT from Empties"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="GIT File",
        subtype="FILE_PATH",
        description="Target .git file (defaults to Scene → Active GIT path)",
        default="",
    )

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return is_pykotor_available()

    def _execute_git_export_instances_core(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available.")
            return {"CANCELLED"}

        kb = getattr(context.scene, "kb", None)
        path = (self.filepath or "").strip()
        if not path and kb is not None:
            path = str(getattr(kb, "active_git_path", "") or "").strip()
        if not path or not os.path.isfile(os.fsencode(path)):
            self.report({"ERROR"}, "Set Active GIT path or choose a valid .git file.")
            return {"CANCELLED"}

        git_obj = load_git_via_pykotor(path)
        if git_obj is None:
            self.report({"ERROR"}, f"Could not read GIT: {path}")
            return {"CANCELLED"}

        git: Any = git_obj
        updated = 0
        missing = 0

        for obj in bpy.data.objects:
            if obj.type != "EMPTY":
                continue
            okb = getattr(obj, "kb", None)
            if okb is None:
                continue
            section = getattr(okb, "git_instance_section", None)
            if not section or section == GitInstanceSection.NONE.value:
                continue
            idx = int(getattr(okb, "git_instance_index", 0))
            inst_list = getattr(git, str(section), None)
            if not isinstance(inst_list, list) or idx < 0 or idx >= len(inst_list):
                missing += 1
                continue
            instance = inst_list[idx]
            _apply_empty_to_git_instance(obj, str(section), instance)
            updated += 1

        hull_u, spawn_u = (0, 0)
        try:
            hull_u, spawn_u = sync_git_geometry_from_blender(git)
        except ImportError:
            self.report({"WARNING"}, "Encounter/trigger hull export skipped (utility.geometry / PyKotor missing).")

        if not save_git_via_pykotor(git, path, game_is_k2=_game_is_k2(context.scene)):
            self.report({"ERROR"}, f"Failed to write GIT: {path}")
            return {"CANCELLED"}

        msg = f"Updated {updated} GIT root(s), {hull_u} hull mesh(es), {spawn_u} spawn(s) → {path}"
        if missing:
            msg += f" ({missing} instance empties skipped — invalid index or list)"
        self.report({"INFO"}, msg)
        return {"FINISHED"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.git_instances")
        kb = getattr(context.scene, "kb", None)
        fp_diag = (self.filepath or "").strip()
        if not fp_diag and kb is not None:
            fp_diag = str(getattr(kb, "active_git_path", "") or "").strip()
        session = begin_import_operator_diag(log, "kb.git_export_instances", self, fp_diag)
        outcome = "FINISHED"
        work_done = False
        reason_code = LogReasonCode.OK
        ret: set[str] = {"CANCELLED"}
        try:
            ret = self._execute_git_export_instances_core(context)
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
                "kb.git_export_instances",
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
                "kb.git_export_instances",
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

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event):
        kb = getattr(context.scene, "kb", None)
        if kb is not None and not (self.filepath or "").strip():
            p = str(getattr(kb, "active_git_path", "") or "").strip()
            if p:
                self.filepath = p
        return context.window_manager.invoke_props_dialog(self)


class KB_OT_git_select_linked(bpy.types.Operator):
    """Select all objects that carry GIT linkage (instance markers, hulls, spawns)."""

    bl_idname = "kb.git_select_linked"
    bl_label = "Select GIT Objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.git_instances")

        def _body() -> set[str]:
            bpy.ops.object.select_all(action="DESELECT")
            n = 0
            for obj in context.scene.objects:
                kb = getattr(obj, "kb", None)
                if kb is None:
                    continue
                sec = getattr(kb, "git_instance_section", None)
                role = getattr(kb, "git_geometry_role", None)
                linked = (sec and sec != GitInstanceSection.NONE.value) or (
                    role and role != GitGeometryRole.NONE.value
                )
                if linked:
                    obj.select_set(True)
                    n += 1
            if n and context.view_layer.objects.active is None:
                for o in context.scene.objects:
                    if o.select_get():
                        context.view_layer.objects.active = o
                        break
            self.report({"INFO"}, f"Selected {n} GIT-linked object(s).")
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.git_select_linked", _body)


class KB_OT_git_frame_linked(bpy.types.Operator):
    """Frame selected GIT-linked objects in the active 3D View."""

    bl_idname = "kb.git_frame_linked"
    bl_label = "Frame GIT Selection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode == "OBJECT"

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.git_instances")

        def _body() -> set[str]:
            sel = [o for o in context.scene.objects if o.select_get()]
            if not sel:
                self.report({"WARNING"}, "No selection.")
                return {"CANCELLED"}
            win = context.window
            scr = win.screen
            for area in scr.areas:
                if area.type != "VIEW_3D":
                    continue
                region = None
                for reg in area.regions:
                    if reg.type == "WINDOW":
                        region = reg
                        break
                if region is None:
                    continue
                with context.temp_override(window=win, screen=scr, area=area, region=region):
                    bpy.ops.view3d.view_selected(use_all_regions=False)
                self.report({"INFO"}, "Framed selection in 3D View.")
                return {"FINISHED"}
            self.report({"WARNING"}, "No 3D View found.")
            return {"CANCELLED"}

        return run_simple_operator_logged(log, "kb.git_frame_linked", _body)
