import subprocess


def view_stp(full_path):  # adapt according to preferred viewer
    freecad = subprocess.Popen(['freecad', str(full_path), "--single-instance"])
    return freecad


def close_stp_viewer(viewer_process):
    viewer_process.kill()
