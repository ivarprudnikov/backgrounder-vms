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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    native = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())
    parser.add_argument("--arch", choices=("amd64", "arm64"), default=native)
    parser.add_argument("--profile", choices=PROFILES, default="ubuntu")
    args = parser.parse_args()
    prefix, source, algorithm, sums = PROFILES[args.profile]
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
    sha256 = expected if algorithm == "sha256" else digest(out, "sha256")
    (out.parent / (name + ".sha256")).write_text(f"{sha256}  {name}\n")
    print(f"Verified {out}: {sha256}")


if __name__ == "__main__":
    main()
