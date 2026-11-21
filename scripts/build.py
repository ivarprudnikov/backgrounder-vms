#!/usr/bin/env python3
"""Build a pinned Backgrounder base disk."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import tempfile


UBUNTU_SUMS = {
    "amd64": "af34b3230db47ac2159b500adaef438b5cb4da875139997b8797f9643e1743d3",
    "arm64": "29b3ebd2a83dfbce0fb41a56eedefa384a72aaf576ebf9ebe77ca39ce0692b18",
}
DEBIAN_SUMS = {
    "amd64": "e53a93ef33f828ceed0e7278c2cc2753bdc7d5098fbfae15bd64b6d878db350ea3744247763a1c8ecb6b4019a0f623c38caf6038ad6f9c357fb4e01493ddf1a3",
    "arm64": "3d4655799e64ca93f51832da31101188f28e01cb14fec2164ac9a7a5f70f303b80f72e9632498dd9cb0099ad04b12c186bffe4f0cd50c5e739faa3ee85007eb0",
}
PROFILES = {
    "ubuntu": ("ubuntu-noble-minimal",
               "https://cloud-images.ubuntu.com/minimal/daily/noble/20261107/noble-minimal-cloudimg-{arch}.img",
               "sha256", UBUNTU_SUMS),
    "debian": ("debian-trixie-generic",
               "https://cloud.debian.org/images/cloud/trixie/20261116-2664/debian-13-generic-{arch}-20261116-2664.qcow2",
               "sha512", DEBIAN_SUMS),
}


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bake_blender(base, out):
    from smoke import boot, overlay
    with tempfile.TemporaryDirectory(dir=out.parent.resolve()) as tmp:
        work = Path(tmp)
        disk = overlay(base.resolve(), work, "8G")
        sample = Path(__file__).with_name("cube.py").read_text()
        script = """set -e
trap 'shutdown -P +1' EXIT
export DEBIAN_FRONTEND=noninteractive
apt-get -o Acquire::Retries=3 update --error-on=any
apt-get -o Acquire::Retries=3 install -y --no-install-recommends blender
blender --version
apt-get clean
rm -f /etc/ssh/ssh_host_* /var/lib/systemd/random-seed
cloud-init clean --logs --machine-id --seed
fstrim /
sync
echo BGVM_BOOT_OK > /dev/console"""
        userdata = {"write_files": [{"path": "/usr/local/share/backgrounder/cube.py", "content": sample}],
                    "runcmd": [["bash", "-c", script]]}
        boot(disk, work, userdata, network=True, timeout=3600)
        packed = work / out.name
        subprocess.run(["qemu-img", "convert", "-c", "-O", "qcow2", disk, packed], check=True)
        os.replace(packed, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    native = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())
    parser.add_argument("--arch", choices=("amd64", "arm64"), default=native)
    parser.add_argument("--profile", choices=(*PROFILES, "blender"), default="ubuntu")
    args = parser.parse_args()
    blender = args.profile == "blender"
    if blender and native != args.arch:
        parser.error("build Blender on a native-architecture host")
    prefix, source, algorithm, sums = PROFILES["ubuntu" if blender else args.profile]
    if args.arch not in sums:
        parser.error("unsupported host; specify --arch")
    name = f"{prefix}-{args.arch}.qcow2"
    out = Path("dist") / name
    out.parent.mkdir(exist_ok=True)
    expected = sums[args.arch]
    if not out.exists() or digest(out, algorithm) != expected:
        url = source.format(arch=args.arch)
        with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
            download = Path(tmp) / name
            subprocess.run(["curl", "-fLSs", "--retry", "3", "-o", download, url], check=True)
            if digest(download, algorithm) != expected:
                raise SystemExit(f"{algorithm} mismatch for {url}")
            os.replace(download, out)
    if blender:
        name = f"ubuntu-noble-blender-{args.arch}.qcow2"
        base, out = out, out.parent / name
        bake_blender(base, out)
    sha256 = expected if algorithm == "sha256" and not blender else digest(out, "sha256")
    (out.parent / (name + ".sha256")).write_text(f"{sha256}  {name}\n")
    print(f"Verified {out}: {sha256}")


if __name__ == "__main__":
    main()
