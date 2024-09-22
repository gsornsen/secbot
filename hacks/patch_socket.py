#!/usr/bin/env python

import os
import shutil
import sys
from pathlib import Path


def find_site_packages():
    # Get the root directory of the git repo
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_path = os.path.join(root_dir, '.venv')

    for root, dirs, _ in os.walk(venv_path):
        if 'site-packages' in dirs:
            return os.path.join(root, 'site-packages')
    return None

def patch_socket():
    # Find the site-packages directory
    site_packages = find_site_packages()
    if not site_packages:
        print("Error: Could not find site-packages directory.")
        sys.exit(1)

    # Construct paths
    chainlit_socket_path = Path(site_packages) / "chainlit" / "socket.py"
    local_socket_path = Path("hacks") / "socket.py"

    # Check if files exist
    if not chainlit_socket_path.exists():
        print(f"Error: {chainlit_socket_path} does not exist.")
        sys.exit(1)
    if not local_socket_path.exists():
        print(f"Error: {local_socket_path} does not exist.")
        sys.exit(1)

    # Create a backup of the original file
    backup_path = chainlit_socket_path.with_suffix('.py.bak')
    shutil.copy2(chainlit_socket_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Copy the local socket.py to the chainlit package
    shutil.copy2(local_socket_path, chainlit_socket_path)
    print(f"Patched {chainlit_socket_path} with {local_socket_path}")

if __name__ == "__main__":
    patch_socket()
