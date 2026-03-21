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

"""Lightweight module / install checks; writes ``Scene.kb.last_validation_report``."""

from __future__ import annotations

import os
from collections import Counter

import bpy

from ...vendor.pykotor_adapter import (
    is_pykotor_available,
    list_erf_mod_resources,
    resolve_game_install_path,
    try_list_bif_resources,
)


class KB_OT_validate_module(bpy.types.Operator):
    bl_idname = "kb.validate_module"
    bl_label = "Validate Module / Install"
    bl_description = (
        "Check game install markers, selected .mod readability, and optional BIF path; "
        "store a text report on the scene for the Module Designer panel"
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        kb = scene.kb
        lines: list[str] = []

        if not is_pykotor_available():
            msg = "PyKotor not available — validation skipped."
            kb.last_validation_report = msg
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        install = resolve_game_install_path(kb)
        if not install:
            report = "ERROR: Game installation path not set or not found.\nSet it in Scene properties → KotOR Game Installation."
            kb.last_validation_report = report
            self.report({"ERROR"}, "No game installation path.")
            return {"CANCELLED"}

        lines.append(f"Installation: {install}")
        chitin = os.path.join(install, "chitin.key")
        lines.append(f"chitin.key: {'OK' if os.path.isfile(chitin) else 'MISSING (override-only / partial tree?)'}")

        modules_dir = os.path.join(install, "modules")
        if os.path.isdir(modules_dir):
            n_mod = sum(1 for n in os.listdir(modules_dir) if n.lower().endswith(".mod"))
            lines.append(f"modules/: {n_mod} .mod file(s)")
        else:
            lines.append("WARN: modules/ folder missing")

        ovr = os.path.join(install, "override")
        lines.append(f"override/: {'OK' if os.path.isdir(ovr) else 'missing'}")

        # Selected module
        if kb.module_list and 0 <= kb.module_list_idx < len(kb.module_list):
            mod_name = kb.module_list[kb.module_list_idx].name
            mod_path = os.path.join(install, "modules", mod_name + ".mod")
            if not os.path.isfile(mod_path):
                lines.append(f"ERROR: Selected module file not found: {mod_path}")
            else:
                entries = list_erf_mod_resources(mod_path)
                if entries:
                    lines.append(f"Selected module: {mod_name} — {len(entries)} resource(s)")
                    ext_counts = Counter(ext.lower() for _rr, ext, _data in entries)
                    top = ", ".join(f"{k}:{v}" for k, v in sorted(ext_counts.items())[:24])
                    lines.append(f"Extensions: {top}")
                    if len(ext_counts) > 24:
                        lines.append(f"… +{len(ext_counts) - 24} more extension types")
                else:
                    lines.append(f"WARN: Selected module {mod_name} — no resources listed (empty or read failure)")
        else:
            lines.append("INFO: No module selected — skipped .mod contents check")

        # Optional BIF path (same property as Module Browser BIF tab)
        bif_path = (kb.active_bif_path or "").strip()
        if bif_path:
            if not os.path.isfile(bif_path):
                lines.append(f"ERROR: BIF path is not a file: {bif_path}")
            else:
                bif_entries = try_list_bif_resources(bif_path)
                lines.append(f"BIF: {os.path.basename(bif_path)} — {len(bif_entries)} entry name(s)")

        report = "\n".join(lines)
        if len(report) > 65000:
            report = report[:64900] + "\n… (truncated)"
        kb.last_validation_report = report
        self.report({"INFO"}, "Validation finished — see KotOR → Module Designer or Scene report field")
        return {"FINISHED"}
