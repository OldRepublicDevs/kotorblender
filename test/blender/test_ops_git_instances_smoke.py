"""
test_ops_git_instances_smoke.py – GIT import/export empties (PyKotor)

Run with:
    blender --background --python test/blender/test_ops_git_instances_smoke.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

_OP_FINISHED = frozenset(("FINISHED",))


def _clear_scene_objects() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        if col != bpy.context.scene.collection:
            try:
                bpy.data.collections.remove(col)
            except Exception:
                pass


def test_git_import_export_roundtrip() -> bool:
    try:
        from pykotor.common.misc import Game, ResRef
        from pykotor.resource.generics.git import GIT, GITCreature, bytes_git, read_git
    except ImportError:
        print("  SKIP test_git_import_export_roundtrip (PyKotor not in Blender Python)")
        return True

    _clear_scene_objects()
    d = tempfile.mkdtemp(prefix="kb_git_")
    try:
        path = os.path.join(d, "test.git")
        g = GIT()
        c = GITCreature(10.0, 20.0, 30.0)
        c.resref = ResRef("testcreature")
        g.creatures.append(c)
        with open(path, "wb") as f:
            f.write(bytes_git(g, game=Game.K2))

        r_imp = bpy.ops.kb.git_import_instances(
            "EXEC_DEFAULT",
            filepath=path,
            replace_collection=True,
        )
        if r_imp != _OP_FINISHED:
            print(f"  FAIL import return {r_imp!r}")
            return False

        target = None
        for obj in bpy.data.objects:
            kb = getattr(obj, "kb", None)
            if kb is None:
                continue
            if kb.git_instance_section == "creatures" and kb.git_instance_index == 0:
                target = obj
                break
        if target is None:
            print("  FAIL no linked creature empty")
            return False

        target.location = (1.0, 2.0, 3.0)
        bpy.context.scene.kb.active_git_path = path
        r_exp = bpy.ops.kb.git_export_instances("EXEC_DEFAULT", filepath=path)
        if r_exp != _OP_FINISHED:
            print(f"  FAIL export return {r_exp!r}")
            return False

        g2 = read_git(path)
        if not g2.creatures:
            print("  FAIL empty creature list after export")
            return False
        p = g2.creatures[0].position
        ok = abs(float(p.x) - 1.0) < 1e-4 and abs(float(p.y) - 2.0) < 1e-4 and abs(float(p.z) - 3.0) < 1e-4
        print(f"  {'PASS' if ok else 'FAIL'} test_git_import_export_roundtrip")
        return ok
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_git_trigger_hull_roundtrip() -> bool:
    try:
        from pykotor.common.misc import Game, ResRef
        from pykotor.resource.generics.git import GIT, GITTrigger, bytes_git, read_git
        from utility.common.geometry import Vector3
    except ImportError:
        print("  SKIP test_git_trigger_hull_roundtrip (PyKotor / utility not in Blender Python)")
        return True

    _clear_scene_objects()
    d = tempfile.mkdtemp(prefix="kb_git_tr_")
    try:
        path = os.path.join(d, "trig.git")
        g = GIT()
        tr = GITTrigger(5.0, 6.0, 7.0)
        tr.resref = ResRef("tr1")
        tr.geometry.append(Vector3(0.0, 0.0, 0.0))
        tr.geometry.append(Vector3(2.0, 0.0, 0.0))
        tr.geometry.append(Vector3(0.0, 2.0, 0.0))
        g.triggers.append(tr)
        with open(path, "wb") as f:
            f.write(bytes_git(g, game=Game.K2))

        r_imp = bpy.ops.kb.git_import_instances(
            "EXEC_DEFAULT",
            filepath=path,
            replace_collection=True,
        )
        if r_imp != _OP_FINISHED:
            print(f"  FAIL trigger import {r_imp!r}")
            return False

        hull = None
        for obj in bpy.data.objects:
            kb = getattr(obj, "kb", None)
            if kb is None or obj.type != "MESH":
                continue
            if kb.git_geometry_role == "TRIGGER_HULL" and kb.git_instance_index == 0:
                hull = obj
                break
        if hull is None:
            print("  FAIL no TRIGGER_HULL mesh")
            return False

        mesh = hull.data
        mesh.vertices[0].co.x += 1.0
        mesh.update()

        bpy.context.scene.kb.active_git_path = path
        r_exp = bpy.ops.kb.git_export_instances("EXEC_DEFAULT", filepath=path)
        if r_exp != _OP_FINISHED:
            print(f"  FAIL trigger export {r_exp!r}")
            return False

        g2 = read_git(path)
        if not g2.triggers:
            print("  FAIL no triggers after export")
            return False
        p0 = g2.triggers[0].geometry[0]
        ok = abs(float(p0.x) - 1.0) < 0.02
        print(f"  {'PASS' if ok else 'FAIL'} test_git_trigger_hull_roundtrip")
        return ok
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run_tests() -> bool:
    print("\n=== test_ops_git_instances_smoke.py ===")
    a = test_git_import_export_roundtrip()
    b = test_git_trigger_hull_roundtrip()
    ok = a and b
    status = "OK" if ok else "FAIL"
    print(f"\n[{status}] {int(a) + int(b)}/2 in test_ops_git_instances_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
