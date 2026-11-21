# Ubuntu 24.04 Blender (Noble)

Use this guest to create and edit `.blend` scenes and render still images
without a display. It includes Bash, Python 3, Blender's `blender` CLI,
the Blender Python API (`bpy` inside Blender), and the Cycles CPU renderer.
No GPU or network is needed for the bundled example.

**Example (inside the guest):** create an editable cube scene with a camera
and lights, then reopen it and render frame 1 in a writable directory.

```sh
blender -b --factory-startup --python-exit-code 1 \
  --python /usr/local/share/backgrounder/cube.py -- "$PWD"
blender -b cube.blend -o "$PWD/cube-" -F PNG -f 1
```

Outputs: `cube.blend` (editable scene) and `cube-0001.png` (480 x 360 preview).
For a different design, supply your own Blender Python script to `--python`.
Use `blender --version` to inspect the installed version. A successful render
does not validate dimensions, printability, or architectural constraints.
