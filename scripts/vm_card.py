"""Write a VM card for a disk from its release checksum and profile notes."""
import argparse
from pathlib import Path
import re


def write_card(checksum):
    disk = checksum.name.removesuffix(".sha256")
    sha, listed = checksum.read_text().strip().split()
    if not re.fullmatch(r"[0-9a-f]{64}", sha) or listed != disk:
        raise ValueError(f"Invalid checksum or disk name in {checksum}")
    match = re.fullmatch(r"([a-z0-9-]+)-(amd64|arm64)\.qcow2", disk)
    if not match:
        raise ValueError(f"Unexpected VM filename: {disk}")
    profile, arch = match.groups()
    notes = (Path(__file__).resolve().parents[1] / "cards" / f"{profile}.md").read_text()
    card = checksum.with_name(Path(disk).stem + ".md")
    card.write_text(f"""---
vm_card_version: 1
profile: {profile}
architecture: {arch}
image: {disk}
sha256: "{sha}"
---

{notes.rstrip()}

**Runtime:** Boot this QCOW2 as a read-only base with a per-job writable
overlay and cloud-init seed. Run the examples inside the guest, not on the
host. Copy outputs out before discarding the overlay. The host controls
network access, resource limits and which directories are shared.
""")
    return card


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checksum", type=Path, nargs="+")
    for path in parser.parse_args().checksum:
        print(write_card(path))
