"""Pytest configuration -- adds app/src to sys.path for imports."""

import os
import sys

# Add src/ to path so tests can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
