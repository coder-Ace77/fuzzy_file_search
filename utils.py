# textual_file_search/utils.py
import os
import sys
from pathlib import Path
import subprocess

def open_file_or_directory(path: Path):
    """
    Opens a file or directory using the default system application.
    Uses platform-specific commands.
    """
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return

    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", str(path)], check=True)
    except FileNotFoundError:
        print(f"Error: Could not find a suitable command to open {path}. "
              "Ensure 'xdg-open' (Linux), 'open' (macOS), or 'start' (Windows) is available.")
    except subprocess.CalledProcessError as e:
        print(f"Error opening {path}: Command failed with error code {e.returncode}")
        print(e.stderr.decode() if e.stderr else "No stderr output.")
    except Exception as e:
        print(f"An unexpected error occurred while opening {path}: {e}")