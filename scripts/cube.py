"""Run inside Blender: --python cube.py -- OUTPUT_DIRECTORY."""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

out = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
cube = bpy.context.object
bevel = cube.modifiers.new("Soft edges", "BEVEL")
bevel.width, bevel.segments = 0.055, 4


def paint(obj, name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    obj.data.materials.append(mat)


def aim(obj):
    obj.rotation_euler = (Vector((0, 0, 0.95)) - obj.location).to_track_quat("-Z", "Y").to_euler()


paint(cube, "Glazed teal", (0.035, 0.42, 0.54))
bpy.ops.mesh.primitive_plane_add(size=200)
paint(bpy.context.object, "Slate", (0.09, 0.11, 0.16))
bpy.ops.object.camera_add(location=(4, -6, 4))
scene.camera = bpy.context.object
aim(scene.camera)
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 4.6
for pos, energy, size in [((-3, -4, 6), 520, 4), ((4, 2, 5), 330, 3)]:
    bpy.ops.object.light_add(type="AREA", location=pos)
    light = bpy.context.object
    light.data.energy, light.data.size = energy, size
    aim(light)
scene.world = bpy.data.worlds.new("Studio")
scene.world.color = (0.22, 0.22, 0.22)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.use_denoising = False
scene.cycles.samples = 12
scene.render.resolution_x, scene.render.resolution_y = 480, 360
scene.render.resolution_percentage = 100
bpy.ops.wm.save_as_mainfile(filepath=str(out / "cube.blend"), compress=False)
