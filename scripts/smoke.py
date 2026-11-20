#!/usr/bin/env python3
"""Boot a native-architecture disk with a disposable NoCloud seed and overlay."""
import argparse
import os
from pathlib import Path
import platform
import subprocess
import tempfile


def smoke(image, work):
    seed = work / "seed"
    seed.mkdir()
    (seed / "meta-data").write_text("instance-id: smoke\nlocal-hostname: smoke\n")
    (seed / "user-data").write_text("""#cloud-config
runcmd:
  - [bash, -ec, 'source /etc/os-release; test "$VERSION_CODENAME" = noble; python3 -V; echo BGVM_BOOT_OK > /dev/console']
power_state:
  mode: poweroff
  timeout: 60
  delay: now
""")
    iso = work / "cidata.iso"
    mac = platform.system() == "Darwin"
    if mac:
        mkiso = ["hdiutil", "makehybrid", "-iso", "-joliet", "-default-volume-name", "cidata", "-o", iso, seed]
    else:
        mkiso = ["genisoimage", "-quiet", "-J", "-R", "-V", "cidata", "-o", iso, seed]
    subprocess.run(mkiso, check=True)
    overlay = work / "guest.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", image, overlay, "6G"], check=True)
    arm = platform.machine() in ("arm64", "aarch64")
    accel = "hvf" if mac else ("kvm" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "tcg")
    if arm:
        bios = "edk2-aarch64-code.fd" if mac else "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd"
        cmd = ["qemu-system-aarch64", "-machine", "virt", "-bios", bios]
    else:
        cmd = ["qemu-system-x86_64"]
    cmd += ["-accel", accel, "-cpu", "max" if accel == "tcg" else "host",
            "-m", "1536", "-smp", "2", "-display", "none", "-monitor", "none",
            "-serial", "stdio", "-no-reboot", "-nic", "user,model=virtio-net-pci,restrict=on",
            "-drive", f"file={overlay},if=virtio,format=qcow2",
            "-drive", f"file={iso},if=virtio,format=raw,readonly=on"]
    log = work / "serial.log"
    with log.open("wb") as stream:
        try:
            subprocess.run(cmd, check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
        finally:
            output = log.read_text(errors="replace")
            print(output[-4000:])
    if "BGVM_BOOT_OK" not in output.splitlines():
        raise SystemExit("Guest did not confirm Ubuntu Noble, Bash and Python via cloud-init")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    with tempfile.TemporaryDirectory() as tmp:
        smoke(parser.parse_args().image.resolve(strict=True), Path(tmp))
