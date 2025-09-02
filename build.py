import os
import shutil

import PyInstaller.__main__
from PIL import Image

# Define paths
script_file = "main.py"
app_name = "Whisprly"
icon_path = "icon.ico"
dist_path = "dist"
build_path = "build"

# Convert PNG to ICO for the executable
png_icon_path = os.path.join("whisprly", "assets", "icon.png")
img = Image.open(png_icon_path)
img.save(icon_path)


try:
    # Run PyInstaller
    PyInstaller.__main__.run(
        [
            script_file,
            "--name",
            app_name,
            "--onefile",
            "--windowed",
            "--icon",
            os.path.abspath(icon_path),
            "--add-data",
            f"{os.path.abspath('whisprly/assets')}{os.pathsep}whisprly/assets",
            "--add-data",
            f"{os.path.abspath('settings.json')}{os.pathsep}.",
            "--hidden-import",
            "psutil",
            "--distpath",
            dist_path,
            "--workpath",
            build_path,
            "--specpath",
            build_path,
            "--clean",
        ]
    )

    # Clean up build files
    shutil.rmtree(build_path)
    print(f'\nSuccessfully created {app_name}.exe in the "{dist_path}" folder.')

except Exception as e:
    print(f"An error occurred during the build process: {e}")
