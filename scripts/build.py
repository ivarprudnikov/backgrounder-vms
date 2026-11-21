#!/usr/bin/env python3
"""Build discovered VMs and their release sidecars."""
import argparse
import hashlib
import runpy
import subprocess
import tempfile
from pathlib import Path

from catalog import DIST, NATIVE, discover
from vm_card import write_card


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    vms = discover()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm", choices=vms, help="build one VM and its dependencies (default: all)")
    parser.add_argument("--arch", choices=("amd64", "arm64"), default=NATIVE)
    args = parser.parse_args()
    DIST.mkdir(exist_ok=True)
    built = {}

    def build(name, parents=()):
        if name in built:
            return built[name]
        if name in parents:
            raise ValueError("Cyclic VM dependency: " + " -> ".join((*parents, name)))
        params = runpy.run_path(str(vms[name] / "parameters.py"))
        disk = DIST / f"{name}-{args.arch}.qcow2"
        with tempfile.TemporaryDirectory(dir=DIST) as tmp:
            work = Path(tmp)
            staged = work / disk.name
            if "BASE" in params:
                if NATIVE != args.arch:
                    parser.error(f"build {name} on a native {args.arch} host")
                base = build(params["BASE"], (*parents, name))
                params["bake"](base, staged, work)
                staged.replace(disk)
            else:
                algorithm = params["ALGORITHM"]
                expected = params["DIGESTS"][args.arch]
                if not disk.exists() or digest(disk, algorithm) != expected:
                    url = params["URL"].format(arch=args.arch)
                    subprocess.run(["curl", "-fLSs", "--retry", "3", "-o", staged, url], check=True)
                    if digest(staged, algorithm) != expected:
                        raise ValueError(f"{algorithm} mismatch for {url}")
                    staged.replace(disk)
        sha256 = digest(disk, "sha256")
        checksum = disk.with_suffix(".qcow2.sha256")
        checksum.write_text(f"{sha256}  {disk.name}\n")
        write_card(checksum)
        print(f"Verified {disk}: {sha256}", flush=True)
        built[name] = disk
        return disk

    for name in ([args.vm] if args.vm else vms):
        build(name)


if __name__ == "__main__":
    main()
