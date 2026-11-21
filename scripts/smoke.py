#!/usr/bin/env python3
"""Boot a native-architecture disk with a disposable NoCloud seed and overlay."""
import argparse
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import tarfile
import json


def boot(disk, work, userdata, *, network=False, extra=(), timeout=600):
    seed = work / "seed"
    seed.mkdir()
    (seed / "meta-data").write_text("instance-id: smoke\nlocal-hostname: smoke\n")
    (seed / "user-data").write_text("#cloud-config\n" + json.dumps(userdata))
    iso = work / "cidata.iso"
    mac = platform.system() == "Darwin"
    if mac:
        mkiso = ["hdiutil", "makehybrid", "-iso", "-joliet", "-default-volume-name", "cidata", "-o", iso, seed]
    else:
        mkiso = ["genisoimage", "-quiet", "-J", "-R", "-V", "cidata", "-o", iso, seed]
    subprocess.run(mkiso, check=True)
    arm = platform.machine() in ("arm64", "aarch64")
    accel = "hvf" if mac else ("kvm" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "tcg")
    if arm:
        bios = "edk2-aarch64-code.fd" if mac else "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd"
        cmd = ["qemu-system-aarch64", "-machine", "virt", "-bios", bios]
    else:
        cmd = ["qemu-system-x86_64"]
    cmd += ["-accel", accel, "-cpu", "max" if accel == "tcg" else "host",
            "-m", "2048", "-smp", "2", "-display", "none", "-monitor", "none",
            "-serial", "stdio", "-no-reboot", "-netdev", "user,id=net0" + ("" if network else ",restrict=on"),
            "-device", "virtio-net-pci,netdev=net0,romfile=",
            "-drive", f"file={disk},if=virtio,format=qcow2,discard=unmap",
            "-drive", f"file={iso},if=virtio,format=raw,readonly=on", *extra]
    log = work / "serial.log"
    with log.open("wb") as stream:
        try:
            subprocess.run(cmd, check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        finally:
            output = log.read_text(errors="replace")
            print(output[-4000:])
    if "BGVM_BOOT_OK" not in output.splitlines():
        raise SystemExit("Guest did not report success:\n" + output[-20000:])


def config(script):
    return {"runcmd": [["bash", "-ec", script + "\necho BGVM_BOOT_OK > /dev/console"]],
            "power_state": {"mode": "poweroff", "delay": "now", "timeout": 60}}


def overlay(image, work, size):
    disk = work / "guest.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", image, disk, size], check=True)
    return disk


def smoke(image, work, profile, output_dir):
    os_release = {"ubuntu": "ubuntu:noble", "debian": "debian:trixie", "blender": "ubuntu:noble"}[profile]
    script = f'source /etc/os-release; test "$ID:$VERSION_CODENAME" = "{os_release}"; python3 -V'
    extra = []
    if profile == "blender":
        transfer = work / "transfer.raw"
        with transfer.open("wb") as f:
            f.truncate(32 << 20)
        extra = ["-drive", f"file={transfer},if=virtio,format=raw"]
        script += """
cd /tmp
blender --background --factory-startup --python-exit-code 1 --python /usr/local/share/backgrounder/cube.py -- /tmp
blender -b cube.blend --python-exit-code 1 --python-expr 'import bpy; assert len(bpy.data.objects["Cube"].data.vertices) == 8' -o //cube- -F PNG -f 1
tar -cf /dev/vdc cube.blend cube-0001.png
sync"""
    boot(overlay(image, work, "8G" if profile == "blender" else "6G"), work,
         config(script), extra=extra, timeout=1800 if profile == "blender" else 600)
    if profile == "blender":
        output_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(transfer) as archive:
            for src, dst in [("cube.blend", "cube.blend"), ("cube-0001.png", "cube.png")]:
                data = archive.extractfile(src).read()
                if not data.startswith(b"BLENDER" if dst.endswith(".blend") else b"\x89PNG\r\n\x1a\n"):
                    raise ValueError(f"Invalid {src}")
                (output_dir / dst).write_bytes(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--profile", choices=("ubuntu", "debian", "blender"), default="ubuntu")
    parser.add_argument("--output-dir", type=Path, default=Path("dist/preview"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        smoke(args.image.resolve(strict=True), Path(tmp), args.profile, args.output_dir)
