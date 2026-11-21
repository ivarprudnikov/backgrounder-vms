from guest import check_guest


def run(image, work, output_dir):
    check_guest(image, work, "ubuntu:noble", """echo '{"ok":true}' | python3 -m json.tool""")
