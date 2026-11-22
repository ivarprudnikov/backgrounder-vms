"""Package the QEMU data needed by Backgrounder's headless q35/virt guests."""

import argparse
import hashlib
from pathlib import Path
import zipfile


FILES = {
    "amd64": ("bios.bin", "bios-256k.bin", "kvmvapic.bin", "efi-virtio.rom",
              "linuxboot_dma.bin", "multiboot_dma.bin", "pvh.bin"),
    "arm64": ("edk2-aarch64-code.fd", "edk2-licenses.txt", "efi-virtio.rom"),
}


def package(share, output, arch):
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"qemu-firmware-{arch}.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name in FILES[arch]:
            contents = (share / name).read_bytes()
            if not contents:
                raise ValueError(f"empty QEMU resource: {name}")
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
