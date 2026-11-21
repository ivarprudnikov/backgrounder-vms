# Backgrounder VMs

Download **QCOW2** base disk (VM) from
[Releases](https://github.com/ivarprudnikov/backgrounder-vms/releases). Each VM has a card describing what it is.

Download the matching `.sha256` file into the same directory and verify:

```sh
shasum -a 256 -c ubuntu-noble-minimal-amd64.qcow2.sha256
```

## Build and launch locally

From the repository root, with Python 3, curl, QEMU (`qemu-img` and the
native system emulator), and either macOS `hdiutil` or Linux `genisoimage`:

```sh
python3 scripts/build.py         # all VMs, host architecture
python3 scripts/test.py          # boot each disk and run its own tests
python3 scripts/build.py --vm debian-trixie-generic
python3 scripts/test.py --vm debian-trixie-generic
```

Linux ARM also needs
`qemu-efi-aarch64`. The smoke test boots an overlay, runs Bash and Python
through cloud-init, verifies a guest success message on the serial console,
and shuts down. Its overlay and seed are temporary.

## Repository layout

Each directory in [vms/](vms/) is one VM. Its name is the release filename
prefix; for example [ubuntu-noble-blender/](vms/ubuntu-noble-blender/) produces
`ubuntu-noble-blender-<arch>.qcow2`. To add a VM, create a directory containing:

| File | Responsibility |
| --- | --- |
| `card.md` | Describe tools, guest commands, expected outputs and limits. The builder adds the disk-specific metadata. |
| `parameters.py` | For an upstream disk, declare `URL` (with `{arch}`), `ALGORITHM`, and `DIGESTS` keyed by architecture. For a derived disk, declare `BASE` (another directory name) and `bake(base, output, work)` to write the standalone QCOW2. |
| `test.py` | Define `run(image, work, output_dir)` to validate the finished disk. Use `work` for temporary files and `output_dir` for publishable samples with unique filenames. Raise on failure. |

Keep VM-specific assets beside these files. The build resolves dependencies,
and the local test runner and tag workflow discover the same catalog; no VM
registry edit is needed. Release builds currently target both amd64 and arm64.

## Publish

Push a new tag on a commit containing [the workflow](.github/workflows/release.yml),
for example `git tag v1.0.0 && git push origin v1.0.0`. Distributions
are built and boot-tested on each architecture before publication. Hyphenated
tags (e.g. `v1.0.0-test.1`) create public prereleases, not the latest release.
