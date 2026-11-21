# Backgrounder VMs

Download a tested **QCOW2** base disk from
[Releases](https://github.com/ivarprudnikov/backgrounder-vms/releases).
Choose **Ubuntu 24.04 minimal** for the original Backgrounder environment
or **Debian 13 generic** for a Debian stable environment with Bash, Python 3,
and apt. Both are unmodified upstream cloud images, not container layers.
Choose **Ubuntu 24.04 Blender** for headless 3D modeling and CPU rendering.
Use `amd64` for Intel/AMD hosts or `arm64` for Apple Silicon / 64-bit ARM.
Download the matching `.sha256` file into the same directory and verify:

```sh
shasum -a 256 -c ubuntu-noble-minimal-amd64.qcow2.sha256
```

Set Backgrounder's `tool_isolation.qemu.base_image` to the absolute path of
the verified disk. Ubuntu remains the default.
Keep the base disk pristine: each guest needs its own writable overlay and
cloud-init seed (Backgrounder supplies both). There is no shared password.

## VM cards for downloaders and agents

Starting with `v0.3.0-test.1`, every released disk has a Markdown capability
card in the **same release**. Replace `.qcow2` with `.md` to find it: for
`ubuntu-noble-blender-arm64.qcow2`, fetch `ubuntu-noble-blender-arm64.md`.
Local builds also write the card into `dist/`. YAML front matter identifies
the profile, architecture, exact disk filename, and disk SHA-256. Match these
to the selected disk, then pass the Markdown body to the agent as reference
material: it lists tools, guest commands, expected outputs and limits. The
card describes capabilities; it does not grant host permissions or network access.

## Why Debian as the second image?

| Agent sandbox | What its users start with | What that suggests for Backgrounder |
| --- | --- | --- |
| [Modal](https://modal.com/docs/guide/images) | Sandboxes default to Debian and Python; users layer apt and Python packages onto the base. | Ship a small-purpose base without choosing an agent SDK for everyone. |
| [E2B](https://docs.e2b.dev/template/base-image) | The default Debian-based template includes Python, Node.js, Git and build tools. Alpine and Fedora are supported choices, not the default. | Debian also works as a foundation for a fuller coding image if offline toolchains are needed. |
| [Daytona](https://www.daytona.io/docs/en/snapshots/) | Users choose prebuilt snapshots or define an environment from an image or Dockerfile; container and VM snapshots are distinct. | Keep the base reusable. A prepared workspace with dependencies is a separate deliverable. |

This comparison concerns guest software, not isolation guarantees or market
share. A container filesystem is not a bootable QEMU disk. We use Debian's
[generic cloud disk](https://cloud.debian.org/images/cloud/trixie/) with its
own kernel and cloud-init rather than converting a `debian:slim` container.
This is a Python/shell base, not a clone of E2B's preinstalled toolchain.

## Build and launch locally

From the repository root, with Python 3, curl, QEMU (`qemu-img` and the
native system emulator), and either macOS `hdiutil` or Linux `genisoimage`:

```sh
python3 scripts/build.py         # defaults to the host architecture
python3 scripts/smoke.py dist/ubuntu-noble-minimal-amd64.qcow2
python3 scripts/build.py --profile debian
python3 scripts/smoke.py --profile debian dist/debian-trixie-generic-amd64.qcow2
```

On ARM, substitute `arm64` in the disk filename. Linux ARM also needs
`qemu-efi-aarch64`. The smoke test boots an overlay, runs Bash and Python
through cloud-init, verifies a guest success message on the serial console,
and shuts down. Its overlay and seed are temporary.

[The builder](scripts/build.py) verifies dated upstream disks against pinned
digests (Ubuntu `SHA256SUMS`, Debian `SHA512SUMS`) and writes a `.sha256`
sidecar for every output. No Backgrounder checkout is required. To refresh a
profile, update its URL and both digest pins from that build's upstream manifest.

## Blender: create and render an editable cube

Build on the target architecture. Only the bake needs networking: it boots
Ubuntu and installs the Ubuntu archive's current `blender` package into a
standalone disk. Rendering requires neither a GPU nor network access.

```sh
python3 scripts/build.py --profile blender
python3 scripts/smoke.py --profile blender dist/ubuntu-noble-blender-amd64.qcow2
```

The test boots a fresh guest, creates a scene, then opens it in a second
Blender process, verifies the cube geometry and renders a PNG. Look in
`dist/preview/` for `cube.blend` and `cube.png`.
To do the same from a Backgrounder shell inside the Blender VM:

```sh
blender -b --factory-startup --python-exit-code 1 \
  --python /usr/local/share/backgrounder/cube.py -- "$PWD"
blender -b cube.blend -o "$PWD/cube-" -F PNG -f 1  # writes cube-0001.png
```

## Publish

Push a new tag on a commit containing [the workflow](.github/workflows/release.yml),
for example `git tag v1.0.0 && git push origin v1.0.0`. Both distributions
are built and boot-tested on each architecture before publication. Hyphenated
tags (e.g. `v1.0.0-test.1`) create public prereleases, not the latest release.
