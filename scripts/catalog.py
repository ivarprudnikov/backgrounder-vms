"""Discover complete VM definitions. Directory names are release asset prefixes."""
import json
from pathlib import Path
import platform
import re

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
NATIVE = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())


def discover():
    result = {}
    for directory in sorted((ROOT / "vms").iterdir()):
        if not directory.is_dir() or directory.name.startswith((".", "_")):
            continue
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", directory.name):
            raise ValueError(f"Invalid VM directory name: {directory.name}")
        for filename in ("parameters.py", "card.md", "test.py"):
            if not (directory / filename).is_file():
                raise FileNotFoundError(directory / filename)
        result[directory.name] = directory
    if not result:
        raise ValueError("No VM definitions found")
    return result


if __name__ == "__main__":
    print(json.dumps(list(discover())))
