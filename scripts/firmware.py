"""Package the QEMU data needed by Backgrounder's headless q35/virt guests."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


FILES = {
    "amd64": ("bios.bin", "bios-256k.bin", "kvmvapic.bin", "efi-virtio.rom",
              "linuxboot_dma.bin", "multiboot_dma.bin", "pvh.bin"),
    "arm64": ("edk2-aarch64-code.fd", "edk2-licenses.txt", "efi-virtio.rom"),
}

ROOT = Path(__file__).resolve().parents[1]


def entries(share, arch):
    keg = share.parent.parent
    sbom = keg / "sbom.spdx.json"
    if json.loads(sbom.read_bytes())["name"] != "SBOM-SPDX-qemu-11.0.1":
        raise ValueError(f"{sbom}: expected the Homebrew QEMU 11.0.1 distribution")
    for name in FILES[arch]:
        yield name, share / name
    yield "LICENSE", ROOT / "LICENSE"
    for name in ("LICENSE", "COPYING", "COPYING.LIB", "sbom.spdx.json", ".brew/qemu.rb"):
        yield f"notices/qemu/{Path(name).name}", keg / name
    names = ["ipxe/COPYING", "ipxe/COPYING.GPLv2", "ipxe/COPYING.UBDL"]
    if arch == "amd64":
        names.extend(["seabios/COPYING", "seabios/COPYING.LESSER", "optionrom/NOTICE"])
    for name in names:
        yield f"notices/{name}", ROOT / "notices" / name


def package(share, output, arch):
    data = {}
    for name, source in entries(share, arch):
        data[name] = source.read_bytes()
        if not data[name]:
            raise ValueError(f"empty firmware resource: {source}")
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"qemu-firmware-{arch}.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, contents in data.items():
            entry = zipfile.ZipInfo(name)
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, contents, compress_type=zipfile.ZIP_DEFLATED)
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(".zip.sha256").write_text(f"{checksum}  {path.name}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--share", type=Path, required=True)
    parser.add_argument("--arch", choices=FILES, required=True)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    package(args.share, args.output, args.arch)
