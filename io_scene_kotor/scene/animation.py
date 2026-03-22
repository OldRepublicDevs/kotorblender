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

import math
import re
from typing import Any

import bpy

from ..constants import ANIM_PADDING, NULL, DummyType
from ..diagnostic_log import begin_scene_work_span, end_scene_work_span, sanitize_scene_context
from ..log_config import get_kb_logger
from ..utils import find_object, frame_to_time, time_to_frame
from .animnode import AnimationNode


class Animation:
    def __init__(self, name: str = "UNNAMED") -> None:
        self.name: str = name
        self.length: float = 1.0
        self.transtime: float = 0.25
        self.animroot: str = NULL
        self.root_node: AnimationNode | None = None

        self.events: list[tuple[float, str]] = []

    def add_to_objects(self, mdl_root: bpy.types.Object, animscale: float) -> None:
        log = get_kb_logger("scene.animation")
        ctx = sanitize_scene_context(f"{mdl_root.name}:{self.name}")
        span = begin_scene_work_span(log, "scene.animation.Animation.add_to_objects", ctx)
        err = False
        try:
            log.debug(
                "event=scene_animation fn=Animation.add_to_objects_begin events=%s has_root_node=%s animscale=%s",
                len(self.events),
                self.root_node is not None,
                animscale,
            )
            list_anim = Animation.append_to_object(
                mdl_root, self.name, self.length, self.transtime, self.animroot
            )
            for time, name in self.events:
                Animation.append_event_to_object_anim(list_anim, name, time)

            self.add_nodes_to_objects(list_anim, self.root_node, mdl_root, animscale)
        except BaseException:
            err = True
            raise
        finally:
            end_scene_work_span(span, error=err)

    def add_nodes_to_objects(
        self,
        anim: Any,
        node: AnimationNode | None,
        mdl_root: bpy.types.Object,
        animscale: float,
        below_animroot: bool = False,
    ) -> None:
        if node is None:
            return

        def _match_node(o: bpy.types.Object) -> bool:
            kb = getattr(o, "kb", None)
            return kb is not None and kb.node_number == node.node_number

        obj = find_object(mdl_root, _match_node)
        if obj is None:
            get_kb_logger("scene.animation").debug(
                "event=scene_animation fn=add_nodes_to_objects miss node_num=%s below_animroot=%s mdl_root=%s",
                node.node_number,
                below_animroot,
                sanitize_scene_context(mdl_root.name),
            )
        if obj is not None:
            mdl_kb = getattr(mdl_root, "kb", None)
            if (
                not below_animroot
                and mdl_kb is not None
                and obj.name.lower() == mdl_kb.animroot.lower()
            ):
                below_animroot = True
            if below_animroot:
                node.add_keyframes_to_object(anim, obj, mdl_root.name, animscale)

        for child in node.children:
            self.add_nodes_to_objects(anim, child, mdl_root, animscale, below_animroot)

    @classmethod
    def append_to_object(
        cls,
        mdl_root: bpy.types.Object,
        name: str,
        length: float = 0.0,
        transtime: float = 0.25,
        animroot: str = NULL,
    ) -> Any:
        kb = getattr(mdl_root, "kb", None)
        if kb is None:
            raise ValueError(f"Object '{mdl_root.name}' has no kb attribute")
        anim = kb.anim_list.add()
        anim.name = name
        anim.root = animroot
        anim.transtime = transtime
        anim.frame_start = Animation.get_next_frame(mdl_root)
        anim.frame_end = anim.frame_start + time_to_frame(length)
        get_kb_logger("scene.animation").debug(
            "event=scene_animation fn=append_to_object name=%s mdl_root=%s frame_start=%s frame_end=%s transtime=%s animroot=%s",
            sanitize_scene_context(name),
            sanitize_scene_context(mdl_root.name),
            anim.frame_start,
            anim.frame_end,
            transtime,
            sanitize_scene_context(str(animroot)),
        )
        return anim

    @classmethod
    def append_event_to_object_anim(cls, list_anim: Any, name: str, time: float) -> None:
        event = list_anim.event_list.add()
        event.name = name
        event.frame = list_anim.frame_start + time_to_frame(time)
        get_kb_logger("scene.animation").debug(
            "event=scene_animation fn=append_event_to_object_anim anim=%s name=%s frame=%s",
            sanitize_scene_context(list_anim.name),
            sanitize_scene_context(name),
            event.frame,
        )

    @classmethod
    def get_next_frame(cls, mdl_root: bpy.types.Object) -> int:
        kb = getattr(mdl_root, "kb", None)
        if kb is None:
            raise ValueError(f"Object '{mdl_root.name}' has no kb attribute")
        ends = [a.frame_end for a in kb.anim_list]
        get_kb_logger("scene.animation").debug(
            "event=scene_animation fn=get_next_frame mdl_root=%s anim_count=%s max_frame_end=%s",
            sanitize_scene_context(mdl_root.name),
            len(ends),
            max(ends) if ends else None,
        )
        last_frame = max(ends)
        nxt = int(math.ceil((last_frame + ANIM_PADDING) / 10.0)) * 10
        get_kb_logger("scene.animation").debug(
            "event=scene_animation fn=get_next_frame_result next_frame=%s padding=%s",
            nxt,
            ANIM_PADDING,
        )
        return nxt

    @classmethod
    def from_list_anim(cls, list_anim: Any, mdl_root: bpy.types.Object) -> Animation:
        log = get_kb_logger("scene.animation")
        log.debug(
            "event=scene_animation fn=from_list_anim_begin anim=%s mdl_root=%s frame_start=%s frame_end=%s events_src=%s",
            sanitize_scene_context(list_anim.name),
            sanitize_scene_context(mdl_root.name),
            getattr(list_anim, "frame_start", None),
            getattr(list_anim, "frame_end", None),
            len(getattr(list_anim, "event_list", []) or []),
        )
        anim = Animation(list_anim.name)
        anim.length = frame_to_time(list_anim.frame_end - list_anim.frame_start)
        anim.transtime = list_anim.transtime
        anim.animroot = list_anim.root
        anim.root_node = Animation.animation_node_from_object(list_anim, mdl_root)

        for event in list_anim.event_list:
            time = frame_to_time(event.frame - list_anim.frame_start)
            name = event.name
            anim.events.append((time, name))

        log.debug(
            "event=scene_animation fn=from_list_anim_done events=%s has_root_node=%s animroot=%s length=%s",
            len(anim.events),
            anim.root_node is not None,
            sanitize_scene_context(str(anim.animroot)),
            anim.length,
        )
        return anim

    @classmethod
    def animation_node_from_object(
        cls,
        anim: Any,
        obj: bpy.types.Object,
        parent: AnimationNode | None = None,
    ) -> AnimationNode:
        name = obj.name
        if re.match(r".+\.\d{3}$", name):
            name = name[:-4]

        node = AnimationNode(name)
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object '{obj.name}' has no kb attribute")
        node.node_number = kb.node_number
        if node is None:
            raise ValueError(f"Object '{obj.name}' has no kb attribute")
        node.parent = parent  # pyright: ignore[reportAttributeAccessIssue]

        get_kb_logger("scene.animation").debug(
            "event=scene_animation fn=animation_node_from_object obj=%s node_num=%s parent=%s raw_children=%s type=%s",
            sanitize_scene_context(obj.name),
            node.node_number,
            sanitize_scene_context(parent.name) if parent is not None else "",
            len(obj.children),
            obj.type,
        )

        node.load_keyframes_from_object(anim, obj)
        if obj.type == "LIGHT":
            node.load_keyframes_from_object(anim, obj.data)
        node.animated = bool(node.keyframes)

        def _match_child(o: bpy.types.Object) -> bool:
            kb = getattr(o, "kb", None)
            return kb is not None and kb.export_order != 0

        for child_obj in sorted(obj.children, key=_match_child):
            child_kb = getattr(child_obj, "kb", None)
            if child_kb is None:
                raise ValueError(f"Object '{child_obj.name}' has no kb attribute")
            if child_obj.type == "EMPTY" and child_kb.dummytype in [
                DummyType.PWKROOT,
                DummyType.DWKROOT,
            ]:
                continue
            child = Animation.animation_node_from_object(anim, child_obj, node)
            if not node.animated and child.animated:
                node.animated = True
            node.children.append(child)

        return node
