import os
import shutil

import PyInstaller.__main__


def build_exe():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_path = os.path.join(base_dir, "server.py")

    print(f"Building EXE from: {server_path}")

    # Clean previous builds
    if os.path.exists(os.path.join(base_dir, "build")):
        shutil.rmtree(os.path.join(base_dir, "build"))
    if os.path.exists(os.path.join(base_dir, "dist")):
        shutil.rmtree(os.path.join(base_dir, "dist"))

    # PyInstaller arguments
    args = [
        server_path,
        "--name=LovecaSolo",
        "--onefile",
        "--noconsole",  # Hide console window (optional, maybe keep for debugging initially?)
        # Add data folders. Separator is ; on Windows
        "--add-data",
        f"web_ui{os.pathsep}web_ui",
        "--add-data",
        f"data{os.pathsep}data",
        # '--add-data', f'img{os.pathsep}img', # Use if you have local images
        # Hidden imports often needed for Flask/EngineIO
        "--hidden-import",
        "engineio.async_drivers.threading",
        "--hidden-import",
        "eventlet",
        "--hidden-import",
        "eventlet.hubs.epolls",
        "--hidden-import",
        "eventlet.hubs.kqueue",
        "--hidden-import",
        "eventlet.hubs.selects",
        "--hidden-import",
        "dns",  # often needed for eventlet
        # Optimization
        "--clean",
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    print("Build complete. Check dist/LovecaSolo.exe")


if __name__ == "__main__":
    build_exe()
