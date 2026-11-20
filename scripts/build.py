#!/usr/bin/env python3
"""Build Backgrounder's pristine Ubuntu minimal base disk."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import tempfile


BUILD = "20261107"
SUMS = {
    "amd64": "af34b3230db47ac2159b500adaef438b5cb4da875139997b8797f9643e1743d3",
    "arm64": "29b3ebd2a83dfbce0fb41a56eedefa384a72aaf576ebf9ebe77ca39ce0692b18",
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    native = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())
    parser.add_argument("--arch", choices=SUMS, default=native)
    args = parser.parse_args()
    if args.arch not in SUMS:
        parser.error("unsupported host; specify --arch")
    name = f"ubuntu-noble-minimal-{args.arch}.qcow2"
    out = Path("dist") / name
    out.parent.mkdir(exist_ok=True)
    expected = SUMS[args.arch]
    if not out.exists() or digest(out) != expected:
        url = (f"https://cloud-images.ubuntu.com/minimal/daily/noble/{BUILD}/"
               f"noble-minimal-cloudimg-{args.arch}.img")
        with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
            download = Path(tmp) / name
            subprocess.run(["curl", "-fLSs", "--retry", "3", "-o", download, url], check=True)
            if digest(download) != expected:
                raise SystemExit(f"SHA256 mismatch for {url}")
            os.replace(download, out)
    (out.parent / (name + ".sha256")).write_text(f"{expected}  {name}\n")
    print(f"Verified {out}: {expected}")


if __name__ == "__main__":
    main()
