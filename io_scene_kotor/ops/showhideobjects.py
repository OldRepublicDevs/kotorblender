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

from collections.abc import Callable
from inspect import getattr_static

import bpy

from ..constants import Classification, LogReasonCode, MeshType
from ..diagnostic_log import begin_simple_operator_diag, end_import_operator_diag
from ..log_config import get_kb_logger
from ..utils import find_mdl_root_of, is_aabb_mesh, is_char_bone, is_char_dummy, is_mdl_root, is_mesh_type, is_null, is_skin_mesh

_SHOWHIDE_LOG = get_kb_logger("ops.showhideobjects")


def _operator_bl_idname(op: bpy.types.Operator) -> str:
    """Stable ``kb.*`` id string; instance ``bl_idname`` may be RNA-style on some Blender versions."""
    v = getattr_static(type(op), "bl_idname", "")
    return v if isinstance(v, str) else ""


def _run_showhide_logged(
    operator_id: str,
    context: bpy.types.Context,
    body: Callable[[bpy.types.Context], None],
) -> set[str]:
    """Wrap scene visibility work with ``op_start`` / ``op_end``; always ``FINISHED``."""
    session = begin_simple_operator_diag(_SHOWHIDE_LOG, operator_id)
    work_done = False
    reason_code = LogReasonCode.INTERNAL_ERROR
    outcome = "FINISHED"
    try:
        body(context)
        work_done = True
        reason_code = LogReasonCode.OK
    except Exception:
        outcome = "ERROR"
        _SHOWHIDE_LOG.exception(
            "event=op_error operator_id=%s run_id=%s reason_code=%s",
            operator_id,
            session.run_id,
            reason_code.value,
            exc_info=True,
        )
    finally:
        end_import_operator_diag(
            session,
            outcome=outcome,
            work_done=work_done,
            reason_code=reason_code,
        )
    return {"FINISHED"}


class KB_OT_hide_walkmeshes(bpy.types.Operator):
    bl_idname = "kb.hide_walkmeshes"
    bl_label = "Hide Walkmeshes"
    bl_description = "Hides all walkmeshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_aabb_mesh(obj):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_untextured(bpy.types.Operator):
    bl_idname = "kb.hide_untextured"
    bl_label = "Hide Untextured"
    bl_description = "Hides all untextured trimeshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_mesh_type(obj, MeshType.TRIMESH) and is_null(obj.kb.bitmap) and is_null(obj.kb.bitmap2):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_unlightmapped(bpy.types.Operator):
    bl_idname = "kb.hide_unlightmapped"
    bl_label = "Hide Unlightmapped"
    bl_description = "Hides all unlightmapped meshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if obj.type == "MESH" and (not obj.kb.lightmapped or is_null(obj.kb.bitmap2)):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_lights(bpy.types.Operator):
    bl_idname = "kb.hide_lights"
    bl_label = "Hide Lights"
    bl_description = "Hides all lights in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if obj.type == "LIGHT":
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_emitters(bpy.types.Operator):
    bl_idname = "kb.hide_emitters"
    bl_label = "Hide Emitters"
    bl_description = "Hides all emitters in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_mesh_type(obj, MeshType.EMITTER):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_blockers(bpy.types.Operator):
    bl_idname = "kb.hide_blockers"
    bl_label = "Hide Blockers"
    bl_description = "Hides all untextured blocker trimeshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_mesh_type(obj, MeshType.TRIMESH) and not is_skin_mesh(obj) and obj.kb.render == 1 and is_null(obj.kb.bitmap) and is_null(obj.kb.bitmap2):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_char_bones(bpy.types.Operator):
    bl_idname = "kb.hide_char_bones"
    bl_label = "Hide Character Bones"
    bl_description = "Hides all humanoid rig bones in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_char_bone(obj):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_char_dummies(bpy.types.Operator):
    bl_idname = "kb.hide_char_dummies"
    bl_label = "Hide Character Dummies"
    bl_description = "Hides all humanoid rig dummy/null objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_char_dummy(obj):
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_walkmeshes(bpy.types.Operator):
    bl_idname = "kb.show_walkmeshes"
    bl_label = "Show Walkmeshes"
    bl_description = "Reveals all walkmeshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_aabb_mesh(obj):
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_untextured(bpy.types.Operator):
    bl_idname = "kb.show_untextured"
    bl_label = "Show Untextured"
    bl_description = "Reveals all untextured trimeshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_mesh_type(obj, MeshType.TRIMESH) and is_null(obj.kb.bitmap) and is_null(obj.kb.bitmap2):
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_unlightmapped(bpy.types.Operator):
    bl_idname = "kb.show_unlightmapped"
    bl_label = "Show Unlightmapped"
    bl_description = "Reveals all unlightmapped meshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if obj.type == "MESH" and (not obj.kb.lightmapped or is_null(obj.kb.bitmap2)):
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_lights(bpy.types.Operator):
    bl_idname = "kb.show_lights"
    bl_label = "Show Lights"
    bl_description = "Reveals all lights in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if obj.type == "LIGHT":
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_emitters(bpy.types.Operator):
    bl_idname = "kb.show_emitters"
    bl_label = "Show Emitters"
    bl_description = "Reveals all emitters in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_mesh_type(obj, MeshType.EMITTER):
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_blockers(bpy.types.Operator):
    bl_idname = "kb.show_blockers"
    bl_label = "Show Blockers"
    bl_description = "Reveals all untextured blocker trimeshes in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_mesh_type(obj, MeshType.TRIMESH) and not is_skin_mesh(obj) and obj.kb.render == 1 and is_null(obj.kb.bitmap) and is_null(obj.kb.bitmap2):
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_char_bones(bpy.types.Operator):
    bl_idname = "kb.show_char_bones"
    bl_label = "Show Character Bones"
    bl_description = "Reveals all humanoid rig bones in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        bpy.ops.object.select_all(action="DESELECT")

        for obj in context.scene.objects:
            if is_char_bone(obj):
                obj.hide_viewport = False
                obj.hide_render = False

        return {"FINISHED"}


class KB_OT_show_char_dummies(bpy.types.Operator):
    bl_idname = "kb.show_char_dummies"
    bl_label = "Show Character Dummies"
    bl_description = "Reveals all humanoid rig dummy/null objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")

            for obj in ctx.scene.objects:
                if is_char_dummy(obj):
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_characters(bpy.types.Operator):
    bl_idname = "kb.show_characters"
    bl_label = "Show Characters"
    bl_description = "Reveals all character (UTC) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # Filter by MDL root classification (CHARACTER = creature)
            for obj in ctx.scene.objects:
                root = find_mdl_root_of(obj)
                if root is not None and is_mdl_root(root) and root.kb.classification == Classification.CHARACTER:
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_characters(bpy.types.Operator):
    bl_idname = "kb.hide_characters"
    bl_label = "Hide Characters"
    bl_description = "Hides all character (UTC) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # Filter by MDL root classification (CHARACTER = creature)
            for obj in ctx.scene.objects:
                root = find_mdl_root_of(obj)
                if root is not None and is_mdl_root(root) and root.kb.classification == Classification.CHARACTER:
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_placeables(bpy.types.Operator):
    bl_idname = "kb.show_placeables"
    bl_label = "Show Placeables"
    bl_description = "Reveals all placeable (UTP) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # Filter by MDL root classification (PLACEABLE)
            for obj in ctx.scene.objects:
                root = find_mdl_root_of(obj)
                if root is not None and is_mdl_root(root) and root.kb.classification == Classification.PLACEABLE:
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_placeables(bpy.types.Operator):
    bl_idname = "kb.hide_placeables"
    bl_label = "Hide Placeables"
    bl_description = "Hides all placeable (UTP) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # Filter by MDL root classification (PLACEABLE)
            for obj in ctx.scene.objects:
                root = find_mdl_root_of(obj)
                if root is not None and is_mdl_root(root) and root.kb.classification == Classification.PLACEABLE:
                    obj.hide_viewport = True
                    obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_doors(bpy.types.Operator):
    bl_idname = "kb.show_doors"
    bl_label = "Show Doors"
    bl_description = "Reveals all door (UTD) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # Filter by MDL root classification (DOOR)
            for obj in ctx.scene.objects:
                root = find_mdl_root_of(obj)
                if root is not None and is_mdl_root(root) and root.kb.classification == Classification.DOOR:
                    obj.hide_viewport = False
                    obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_doors(bpy.types.Operator):
    bl_idname = "kb.hide_doors"
    bl_label = "Hide Doors"
    bl_description = "Hides all door (UTD) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        bpy.ops.object.select_all(action="DESELECT")
        # Filter by MDL root classification (DOOR)
        for obj in context.scene.objects:
            root = find_mdl_root_of(obj)
            if root is not None and is_mdl_root(root) and root.kb.classification == Classification.DOOR:
                obj.hide_viewport = True
                obj.hide_render = True
        return {"FINISHED"}


class KB_OT_show_items(bpy.types.Operator):
    bl_idname = "kb.show_items"
    bl_label = "Show Items"
    bl_description = "Reveals all item (UTI) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # NOTE: Items (UTI) do not have MDL classifications. This operator requires
            # resource binding to identify UTI objects. Until resource binding is implemented,
            # this will show all objects. To filter properly, check obj.kb.resource_type == "UTI"
            # or similar when resource binding is available.
            for obj in ctx.scene.objects:
                obj.hide_viewport = False
                obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_items(bpy.types.Operator):
    bl_idname = "kb.hide_items"
    bl_label = "Hide Items"
    bl_description = "Hides all item (UTI) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # NOTE: Items (UTI) do not have MDL classifications. This operator requires
            # resource binding to identify UTI objects. Until resource binding is implemented,
            # this will hide all objects. To filter properly, check obj.kb.resource_type == "UTI"
            # or similar when resource binding is available.
            for obj in ctx.scene.objects:
                obj.hide_viewport = True
                obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_triggers(bpy.types.Operator):
    bl_idname = "kb.show_triggers"
    bl_label = "Show Triggers"
    bl_description = "Reveals all trigger (UTT) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # NOTE: Triggers (UTT) do not have MDL classifications. This operator requires
            # resource binding to identify UTT objects. Until resource binding is implemented,
            # this will show all objects. To filter properly, check obj.kb.resource_type == "UTT"
            # or similar when resource binding is available.
            for obj in ctx.scene.objects:
                obj.hide_viewport = False
                obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_triggers(bpy.types.Operator):
    bl_idname = "kb.hide_triggers"
    bl_label = "Hide Triggers"
    bl_description = "Hides all trigger (UTT) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # NOTE: Triggers (UTT) do not have MDL classifications. This operator requires
            # resource binding to identify UTT objects. Until resource binding is implemented,
            # this will hide all objects. To filter properly, check obj.kb.resource_type == "UTT"
            # or similar when resource binding is available.
            for obj in ctx.scene.objects:
                obj.hide_viewport = True
                obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_show_waypoints(bpy.types.Operator):
    bl_idname = "kb.show_waypoints"
    bl_label = "Show Waypoints"
    bl_description = "Reveals all waypoint (UTW) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # NOTE: Waypoints (UTW) do not have MDL classifications. This operator requires
            # resource binding to identify UTW objects. Until resource binding is implemented,
            # this will show all objects. To filter properly, check obj.kb.resource_type == "UTW"
            # or similar when resource binding is available.
            for obj in ctx.scene.objects:
                obj.hide_viewport = False
                obj.hide_render = False

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)


class KB_OT_hide_waypoints(bpy.types.Operator):
    bl_idname = "kb.hide_waypoints"
    bl_label = "Hide Waypoints"
    bl_description = "Hides all waypoint (UTW) objects in the scene"

    def execute(self, context: bpy.types.Context) -> set[str]:
        def _body(ctx: bpy.types.Context) -> None:
            bpy.ops.object.select_all(action="DESELECT")
            # NOTE: Waypoints (UTW) do not have MDL classifications. This operator requires
            # resource binding to identify UTW objects. Until resource binding is implemented,
            # this will hide all objects. To filter properly, check obj.kb.resource_type == "UTW"
            # or similar when resource binding is available.
            for obj in ctx.scene.objects:
                obj.hide_viewport = True
                obj.hide_render = True

        return _run_showhide_logged(_operator_bl_idname(self), context, _body)
