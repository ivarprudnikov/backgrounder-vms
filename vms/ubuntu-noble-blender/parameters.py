import subprocess

from guest import boot, overlay

BASE = "ubuntu-noble-minimal"


def bake(base, output, work):
    disk = overlay(base, work, "8G")
    script = """set -e
trap 'shutdown -P +1' EXIT
export DEBIAN_FRONTEND=noninteractive
apt-get -o Acquire::Retries=3 update --error-on=any
apt-get -o Acquire::Retries=3 install -y --no-install-recommends blender
blender --version
apt-get clean
rm -f /etc/ssh/ssh_host_* /var/lib/systemd/random-seed
cloud-init clean --logs --machine-id --seed
fstrim /
sync
echo BGVM_BOOT_OK > /dev/console"""
    userdata = {"runcmd": [["bash", "-c", script]]}
    boot(disk, work, userdata, network=True, timeout=3600)
    subprocess.run(["qemu-img", "convert", "-c", "-O", "qcow2", disk, output], check=True)
