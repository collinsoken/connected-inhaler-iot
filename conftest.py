"""
Ensures the repo root is on sys.path, so `from fog_node.x import y` and
`from simulator.x import y` resolve correctly no matter how pytest is
invoked (plain `pytest`, `python -m pytest`, or from CI).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
