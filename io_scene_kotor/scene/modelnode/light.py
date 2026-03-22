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
from typing import TYPE_CHECKING, cast

import bpy

from ...constants import ExportOptions, ImportOptions, NodeType
from ...diagnostic_log import begin_scene_work_span, end_scene_work_span, sanitize_scene_context
from ...log_config import get_kb_logger

from .base import BaseNode, _log_modelnode

if TYPE_CHECKING:
    from ...ui.props.object import ObjectPropertyGroup


class FlareList:
    def __init__(self):
        self.textures: list[str] = []
        self.sizes: list[float] = []
        self.positions: list[float] = []
        self.colorshifts: list[tuple[float, float, float]] = []


class LightNode(BaseNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        BaseNode.__init__(self, name)
        self.nodetype: NodeType = NodeType.LIGHT

        self.shadow: bool = True
        self.radius: float = 5.0
        self.shadowradius: float = 0.0
        self.verticaldisplacement: float = 0.0
        self.multiplier: float = 1.0
        self.lightpriority: int = 5
        self.color: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.ambientonly: bool = True
        self.dynamictype: int = 0
        self.affectdynamic: bool = True
        self.fadinglight: bool = True
        self.lensflares: bool = False
        self.flareradius: float = 1.0

        self.flare_list: FlareList = FlareList()

    def add_to_collection(self, collection: bpy.types.Collection, options: ImportOptions) -> bpy.types.Object | None:
        log = get_kb_logger("scene.modelnode.light")
        span = begin_scene_work_span(
            log, "scene.modelnode.LightNode.add_to_collection", sanitize_scene_context(self.name)
        )
        err = False
        try:
            light: bpy.types.Light = self.create_light(self.name)
            obj: bpy.types.Object = bpy.data.objects.new(self.name, light)
            self.set_object_data(obj, options)
            collection.objects.link(obj)
            _log_modelnode("LightNode.add_to_collection", self)
            return obj  # pyright: ignore[reportReturnNone]
        except BaseException:
            err = True
            raise
        finally:
            end_scene_work_span(span, error=err)

    def create_light(self, name: str) -> bpy.types.Light:
        negative: bool = any([c < 0.0 for c in self.color])
        light: bpy.types.Light = bpy.data.lights.new(name, "POINT")
        light.color = [(-c if negative else c) for c in self.color]  # pyright: ignore[reportAttributeAccessIssue]
        light.use_shadow = self.shadow
        if self.shadow and bpy.app.version < (4, 3):
            light.use_contact_shadow = True
            light.contact_shadow_distance = self.radius
        return light

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        BaseNode.set_object_data(self, obj, options)

        kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.multiplier = self.multiplier
        kb.radius = self.radius
        kb.shadowradius = self.shadowradius
        kb.verticaldisplacement = self.verticaldisplacement
        kb.ambientonly = self.ambientonly >= 1
        kb.shadow = self.shadow >= 1
        kb.lightpriority = self.lightpriority
        kb.fadinglight = self.fadinglight >= 1
        kb.dynamictype = self.dynamictype
        kb.affectdynamic = self.affectdynamic >= 1
        kb.flareradius = self.flareradius
        kb.negativelight = any([c < 0.0 for c in self.color])

        if (self.flareradius > 0) or (self.lensflares >= 1):
            kb.lensflares = True
            num_flares = len(self.flare_list.textures)
            for i in range(num_flares):
                newItem = kb.flare_list.add()
                newItem.texture = self.flare_list.textures[i]
                newItem.colorshift = self.flare_list.colorshifts[i]
                newItem.size = self.flare_list.sizes[i]
                newItem.position = self.flare_list.positions[i]

        LightNode.calc_light_power(obj)

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ExportOptions,
    ) -> None:
        BaseNode.load_object_data(self, obj, eval_obj, options)

        kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        if not isinstance(eval_obj.data, bpy.types.Light):
            raise ValueError(f"Object [{eval_obj.name}] data is not a Light")
        self.color = cast("tuple[float, float, float]", tuple([(-c if kb.negativelight else c) for c in eval_obj.data.color]))
        self.multiplier = kb.multiplier
        self.radius = kb.radius
        self.shadowradius = kb.shadowradius
        self.verticaldisplacement = kb.verticaldisplacement
        self.ambientonly = bool(kb.ambientonly)
        self.shadow = bool(kb.shadow)
        self.lightpriority = kb.lightpriority
        self.fadinglight = bool(kb.fadinglight)
        self.dynamictype = kb.dynamictype
        self.affectdynamic = bool(kb.affectdynamic)
        self.flareradius = kb.flareradius
        self.negativelight = bool(kb.negativelight)

        if bool(kb.lensflares):
            self.lensflares = True
            for item in kb.flare_list:
                self.flare_list.textures.append(item.texture)
                self.flare_list.sizes.append(item.size)
                self.flare_list.positions.append(item.position)
                self.flare_list.colorshifts.append(item.colorshift)

    @classmethod
    def calc_light_power(cls, light: bpy.types.Object) -> None:
        if light.kb.negativelight:
            light.data.energy = 0
        else:
            light.data.energy = light.kb.multiplier * light.kb.radius * light.kb.radius
