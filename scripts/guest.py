#!/usr/bin/env python3
"""Boot a native-architecture disk with a disposable NoCloud seed and overlay."""
import os
import platform
import subprocess
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


def check_guest(image, work, os_release, commands="", size="6G", **boot_options):
    script = f'source /etc/os-release; test "$ID:$VERSION_CODENAME" = "{os_release}"; python3 -V\n{commands}'
    boot(overlay(image, work, size), work, config(script), **boot_options)
