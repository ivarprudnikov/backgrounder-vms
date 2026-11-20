# Backgrounder VMs

Download a tested Ubuntu 24.04 (Noble) minimal **QCOW2** base disk from
[Releases](https://github.com/ivarprudnikov/backgrounder-vms/releases).
Use `amd64` for Intel/AMD hosts or `arm64` for Apple Silicon / 64-bit ARM.
Download the matching `.sha256` file into the same directory and verify:

```sh
shasum -a 256 -c ubuntu-noble-minimal-amd64.qcow2.sha256
```

Set Backgrounder's `tool_isolation.qemu.base_image` to the absolute path of
the verified disk. It is the same unmodified Canonical cloud image used by
Backgrounder's default builder, pinned rather than tracking `current`.
Keep the base disk pristine: each guest needs its own writable overlay and
cloud-init seed (Backgrounder supplies both). There is no shared password.

## Build and launch locally

From the repository root, with Python 3, curl, QEMU (`qemu-img` and the
native system emulator), and either macOS `hdiutil` or Linux `genisoimage`:

```sh
python3 scripts/build.py         # defaults to the host architecture
python3 scripts/smoke.py dist/ubuntu-noble-minimal-amd64.qcow2
```

On ARM, substitute `arm64` in the disk filename. Linux ARM also needs
`qemu-efi-aarch64`. The smoke test boots an overlay, runs Bash and Python
through cloud-init, verifies a guest success message on the serial console,
and shuts down. Its overlay and seed are temporary.

[The builder](scripts/build.py) records the dated Ubuntu minimal daily build
and its SHA-256 for each architecture; no Backgrounder checkout is required.
To refresh the image (or if Ubuntu rotates the daily build out), update the
build date and hashes from that build's Canonical `SHA256SUMS` together.
Previous release assets remain available independently of Ubuntu's retention.

## Publish

Push a new tag on a commit containing [the workflow](.github/workflows/release.yml),
for example `git tag v1.0.0 && git push origin v1.0.0`. Both native runners
build and boot-test their disk before either disk is published. Hyphenated
tags (e.g. `v1.0.0-test.1`) create public prereleases, not the latest release.
