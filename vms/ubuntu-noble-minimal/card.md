# Ubuntu 24.04 minimal (Noble)

Use this base for isolated shell commands, file processing, and Python
standard-library tasks. Bash runs shell scripts; `python3` handles structured
data; `apt-get` manages Ubuntu packages. `cloud-init` provisions each guest.
Choose the Blender profile instead for preinstalled 3D modeling tools.

**Example (inside the guest):** format a JSON job result without installing
anything. The output is `result.json` in the current writable directory.

```sh
printf '%s\n' '{"job":42,"complete":true}' | python3 -m json.tool > result.json
cat result.json
```

This example needs no network. Installing additional packages generally
requires elevated privileges and access to an apt mirror.
