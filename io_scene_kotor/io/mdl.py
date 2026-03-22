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

"""
MDL load/save using io_scene_kotor's own readers and writers only.

- ASCII: AsciiMdlReader / AsciiMdlWriter (format/mdl/ascii_reader.py, ascii_writer.py).
- Binary: MdlReader / MdlWriter (format/mdl/reader.py, writer.py).

PyKotor is not used for MDL IO; get_use_pykotor_readers() does not affect this module.
"""

from __future__ import annotations

import os

import bpy

from ..constants import ANIM_FPS, ExportOptions, ImportOptions
from ..diagnostic_log import begin_io_file_span, end_io_file_span, sanitize_scene_context
from ..log_config import get_kb_logger
from ..format.bwm.reader import BwmReader
from ..format.bwm.writer import BwmWriter
from ..format.mdl.ascii_reader import AsciiMdlReader
from ..format.mdl.ascii_writer import AsciiMdlWriter
from ..format.mdl.reader import MdlReader
from ..format.mdl.writer import MdlWriter
from ..scene.model import Model
from ..scene.modelnode.aabb import AabbNode
from ..scene.walkmesh import Walkmesh
from ..utils import (
    find_objects,
    is_dwk_root,
    is_mdl_root,
    is_pwk_root,
    kotor_addon_preferences,
    semicolon_separated_to_absolute_paths,
)

from .mdl_validate import validate_mdl_export


def _is_ascii_mdl(filepath: str) -> bool:
    """Detect if a file is ASCII MDL format."""
    # Check extension
    if filepath.endswith(".mdl.ascii") or filepath.endswith(".ascii"):
        return True

    # Check file content - ASCII MDL files start with text keywords
    try:
        with open(filepath, encoding="utf-8") as f:
            first_line = f.readline().strip()
            # ASCII MDL files typically start with comments or "newmodel"
            if first_line.startswith("#") or first_line.startswith("newmodel"):
                return True
    except (OSError, UnicodeDecodeError):
        # If we can't read as text, it's likely binary
        pass

    return False


def load_mdl(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
    position: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    span = begin_io_file_span(get_kb_logger("io.mdl"), "load_mdl", filepath)
    err = False
    try:
        _load_mdl_body(operator, filepath, options, position)
    except BaseException:
        err = True
        raise
    finally:
        end_io_file_span(span, error=err)


def _load_mdl_body(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
    position: tuple[float, float, float],
) -> None:
    log = get_kb_logger("io.mdl")
    operator.report({"INFO"}, f"Loading model from '{filepath}'")
    is_ascii = _is_ascii_mdl(filepath)
    log.debug(
        "event=io_mdl fn=_load_mdl_body phase=start ascii=%s import_geometry=%s import_walkmeshes=%s import_animations=%s build_armature=%s tex_paths=%s lm_paths=%s",
        is_ascii,
        options.import_geometry,
        options.import_walkmeshes,
        options.import_animations,
        options.build_armature,
        len(options.texture_search_paths or []),
        len(options.lightmap_search_paths or []),
    )

    # Build texture/lightmap search paths from addon preferences if not already set
    if not options.texture_search_paths or not options.lightmap_search_paths:
        try:
            addon_preferences = kotor_addon_preferences()
            if addon_preferences is not None:
                working_dir = os.path.dirname(filepath)
                # semicolon_separated_to_absolute_paths coerces prefs (e.g. _PropertyDeferred)
                if not options.texture_search_paths:
                    options.texture_search_paths = semicolon_separated_to_absolute_paths(
                        addon_preferences.texture_search_paths,  # pyright: ignore[reportAttributeAccessIssue]
                        working_dir,
                    )
                if not options.lightmap_search_paths:
                    options.lightmap_search_paths = semicolon_separated_to_absolute_paths(
                        addon_preferences.lightmap_search_paths,  # pyright: ignore[reportAttributeAccessIssue]
                        working_dir,
                    )
        except Exception:
            # If preferences are unavailable (e.g. in tests), use empty lists
            if not options.texture_search_paths:
                options.texture_search_paths = []
            if not options.lightmap_search_paths:
                options.lightmap_search_paths = []

    # Detect format and use appropriate reader
    if is_ascii:
        operator.report({"INFO"}, "Detected ASCII MDL format")
        mdl = AsciiMdlReader(filepath)
        model = mdl.load()
    else:
        # Binary MDL - use existing reader
        mdl = MdlReader(filepath)
        model = mdl.load()

    pwk_walkmesh = None
    dwk_walkmesh1 = None
    dwk_walkmesh2 = None
    dwk_walkmesh3 = None

    if options.import_geometry and options.import_walkmeshes:
        wok_path = filepath[:-4] + ".wok"
        if os.path.exists(wok_path):
            wok = BwmReader(wok_path, model.name)
            walkmesh = wok.load()
            aabb = model.find_node(lambda n: isinstance(n, AabbNode))
            aabb_wok = walkmesh.find_node(lambda n: isinstance(n, AabbNode))
            if aabb and aabb_wok:
                aabb.roomlinks = aabb_wok.roomlinks
                aabb.compute_lyt_position(aabb_wok)

        pwk_path = filepath[:-4] + ".pwk"
        if os.path.exists(pwk_path):
            operator.report({"INFO"}, f"Loading walkmesh from '{pwk_path}'")
            pwk = BwmReader(pwk_path, model.name)
            pwk_walkmesh = pwk.load()

        dwk0_path = filepath[:-4] + "0.dwk"
        dwk1_path = filepath[:-4] + "1.dwk"
        dwk2_path = filepath[:-4] + "2.dwk"
        if os.path.exists(dwk0_path) and os.path.exists(dwk1_path) and os.path.exists(dwk2_path):
            operator.report({"INFO"}, f"Loading walkmesh from '{dwk0_path}'")
            dwk1 = BwmReader(dwk0_path, model.name)
            operator.report({"INFO"}, f"Loading walkmesh from '{dwk1_path}'")
            dwk2 = BwmReader(dwk1_path, model.name)
            operator.report({"INFO"}, f"Loading walkmesh from '{dwk2_path}'")
            dwk3 = BwmReader(dwk2_path, model.name)
            dwk_walkmesh1 = dwk1.load()
            dwk_walkmesh2 = dwk2.load()
            dwk_walkmesh3 = dwk3.load()

    wok_g = options.import_geometry and options.import_walkmeshes
    log.debug(
        "event=io_mdl fn=_load_mdl_body phase=sidecars wok=%s pwk=%s dwk012=%s",
        wok_g and os.path.exists(filepath[:-4] + ".wok"),
        wok_g and os.path.exists(filepath[:-4] + ".pwk"),
        wok_g
        and os.path.exists(filepath[:-4] + "0.dwk")
        and os.path.exists(filepath[:-4] + "1.dwk")
        and os.path.exists(filepath[:-4] + "2.dwk"),
    )

    collection = bpy.context.collection
    model_root = model.add_to_collection(collection, options, position)
    log.debug(
        "event=io_mdl fn=_load_mdl_body phase=collection_root name=%s",
        sanitize_scene_context(model_root.name),
    )

    if pwk_walkmesh:
        pwk_walkmesh.attach_to_collection(model_root, collection, options)
    if dwk_walkmesh1 and dwk_walkmesh2 and dwk_walkmesh3:
        dwk_walkmesh1.attach_to_collection(model_root, collection, options)
        dwk_walkmesh2.attach_to_collection(model_root, collection, options)
        dwk_walkmesh3.attach_to_collection(model_root, collection, options)

    bpy.context.scene.render.fps = ANIM_FPS

    # Reset Pose
    bpy.context.scene.frame_set(0)


def save_mdl(
    operator: bpy.types.Operator,
    filepath: str,
    options: ExportOptions,
) -> None:
    span = begin_io_file_span(get_kb_logger("io.mdl"), "save_mdl", filepath)
    err = False
    try:
        _save_mdl_body(operator, filepath, options)
    except BaseException:
        err = True
        raise
    finally:
        end_io_file_span(span, error=err)


def _save_mdl_body(
    operator: bpy.types.Operator,
    filepath: str,
    options: ExportOptions,
) -> None:
    log = get_kb_logger("io.mdl")
    # Reset pose
    bpy.context.scene.frame_set(0)

    # Find MDL root
    mdl_root = next(
        iter(obj for obj in bpy.context.selected_objects if is_mdl_root(obj)),
        None,
    )
    if not mdl_root:
        mdl_root = next(
            iter(obj for obj in bpy.context.collection.objects if is_mdl_root(obj)),
            None,
        )
    if not mdl_root:
        log.debug("event=io_mdl fn=_save_mdl_body outcome=no_mdl_root")
        return
    is_ascii = _is_ascii_mdl(filepath)
    log.debug(
        "event=io_mdl fn=_save_mdl_body phase=start root=%s ascii=%s export_walkmeshes=%s export_animations=%s export_tsl=%s export_xbox=%s",
        sanitize_scene_context(mdl_root.name),
        is_ascii,
        options.export_walkmeshes,
        options.export_animations,
        options.export_for_tsl,
        options.export_for_xbox,
    )

    # Ensure MDL root is selected and is in OBJECT mode
    mdl_root.select_set(True)
    bpy.context.view_layer.objects.active = mdl_root
    bpy.ops.object.mode_set(mode="OBJECT")

    validate_mdl_export(operator, mdl_root)

    # Export MDL
    model = Model.from_mdl_root(mdl_root, options)
    operator.report({"INFO"}, f"Saving model to '{filepath}'")

    # Detect format and use appropriate writer
    if is_ascii:
        operator.report({"INFO"}, "Detected ASCII MDL format")
        mdl = AsciiMdlWriter(filepath, model)
        mdl.save()
    else:
        # Binary MDL - use existing writer
        mdl = MdlWriter(
            filepath,
            model,
            options.export_for_tsl,
            options.export_for_xbox,
            options.compress_quaternions,
        )
        mdl.save()
    log.debug(
        "event=io_mdl fn=_save_mdl_body phase=mdl_written ascii=%s model_name=%s",
        is_ascii,
        sanitize_scene_context(model.name),
    )

    if options.export_walkmeshes:
        # Export WOK
        aabb_node = model.find_node(lambda node: isinstance(node, AabbNode))
        if aabb_node:
            base_path, _ = os.path.splitext(filepath)
            wok_path = base_path + ".wok"
            walkmesh = Walkmesh.from_aabb_node(aabb_node)
            operator.report({"INFO"}, f"Saving walkmesh to '{wok_path}'")
            bwm = BwmWriter(wok_path, walkmesh)
            bwm.save()

        # Export PWK or DWK
        xwk_roots = find_objects(mdl_root, lambda obj: is_pwk_root(obj) or is_dwk_root(obj))
        for xwk_root in xwk_roots:
            base_path, _ = os.path.splitext(filepath)
            if is_pwk_root(xwk_root):
                xwk_path = base_path + ".pwk"
            else:
                if xwk_root.name.endswith("open1"):
                    dwk_state = 1
                elif xwk_root.name.endswith("open2"):
                    dwk_state = 2
                elif xwk_root.name.endswith("closed"):
                    dwk_state = 0
                xwk_path = f"{base_path}{dwk_state}.dwk"
            walkmesh = Walkmesh.from_root_object(xwk_root, options)
            operator.report({"INFO"}, f"Saving walkmesh to '{xwk_path}'")
            bwm = BwmWriter(xwk_path, walkmesh)
            bwm.save()
    log.debug("event=io_mdl fn=_save_mdl_body phase=complete")
