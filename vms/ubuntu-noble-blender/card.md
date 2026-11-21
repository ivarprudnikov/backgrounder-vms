# Ubuntu 24.04 Blender (Noble)

Use this guest to create and edit `.blend` scenes and render still images
without a display. It includes Bash, Python 3, Blender's `blender` CLI,
the Blender Python API (`bpy` inside Blender), and the Cycles CPU renderer.
No GPU or network is needed for this example.

**Example (inside the guest):** save Blender's default cube scene in a
writable directory. No helper script is required.

```sh
blender -b --factory-startup --python-exit-code 1 \
  --python-expr 'import bpy, os; bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath("cube.blend"))'
```

Output: `cube.blend` (editable scene).
For a different design, supply your own Blender Python script to `--python`.
Use `blender --version` to inspect the installed version. A successful render
does not validate dimensions, printability, or architectural constraints.
