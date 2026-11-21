# Debian 13 generic (Trixie)

Use this base for jobs that require Debian stable: Bash scripts, data
transformation with `python3`, or Debian package inspection with `dpkg-query`.
`apt-get` manages dependencies and `cloud-init` provisions the guest. This is
a base OS, not a preloaded CAD workstation or compiler toolchain.

**Example (inside the guest):** create a tab-separated inventory of package
names and versions from the guest's package database.

```sh
dpkg-query -W -f='${binary:Package}\t${Version}\n' > packages.tsv
head -n 5 packages.tsv
```

The inventory needs no network or elevated privileges. Installing new
packages generally requires both privileges and access to an apt mirror.
