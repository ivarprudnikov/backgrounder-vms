import tarfile

from guest import check_guest


def run(image, work, output_dir):
    transfer = work / "transfer.raw"
    with transfer.open("wb") as f:
        f.truncate(32 << 20)
    script = """
cd /tmp
blender --background --factory-startup --python-exit-code 1 --python /usr/local/share/backgrounder/cube.py -- /tmp
blender -b cube.blend --python-exit-code 1 --python-expr 'import bpy; assert len(bpy.data.objects["Cube"].data.vertices) == 8' -o //cube- -F PNG -f 1
tar -cf /dev/vdc cube.blend cube-0001.png
sync"""
    check_guest(image, work, "ubuntu:noble", script, size="8G", timeout=1800,
                extra=["-drive", f"file={transfer},if=virtio,format=raw"])
    output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(transfer) as archive:
        for src, dst in [("cube.blend", "cube.blend"), ("cube-0001.png", "cube.png")]:
            data = archive.extractfile(src).read()
            if not data.startswith(b"BLENDER" if dst.endswith(".blend") else b"\x89PNG\r\n\x1a\n"):
                raise ValueError(f"Invalid {src}")
            (output_dir / dst).write_bytes(data)
