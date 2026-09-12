"""Production entry point for PythonAnywhere, Render, and other hosts."""

import os
import sys

# Folder where this project lives on the server
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DATA_DIR", project_home)
os.environ.setdefault("BEHIND_PROXY", "1")

from app import app as application  # noqa: E402