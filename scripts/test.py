#!/usr/bin/env python3
"""Run each discovered VM's tests against its native disk."""
import argparse
from pathlib import Path
import runpy
import tempfile

from catalog import DIST, NATIVE, discover


def main():
    vms = discover()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm", choices=vms, help="test one VM (default: all)")
    parser.add_argument("--output-dir", type=Path, default=DIST / "preview")
    args = parser.parse_args()
    for name in ([args.vm] if args.vm else vms):
        image = (DIST / f"{name}-{NATIVE}.qcow2").resolve(strict=True)
        with tempfile.TemporaryDirectory() as tmp:
            runpy.run_path(str(vms[name] / "test.py"))["run"](image, Path(tmp), args.output_dir)
        print(f"PASS {name} ({NATIVE})", flush=True)


if __name__ == "__main__":
    main()
