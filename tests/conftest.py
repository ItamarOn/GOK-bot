# Add repository root to sys.path so tests can import project packages
import os
import sys

# tests/ is located at <repo_root>/tests; add repo root to sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

