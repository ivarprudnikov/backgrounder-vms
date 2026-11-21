from guest import check_guest


def run(image, work, output_dir):
    check_guest(image, work, "debian:trixie", "dpkg-query -W bash")
