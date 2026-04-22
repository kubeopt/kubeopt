"""Allow running as: python -m kubeopt [command]

Example (from inside kubeopt/ directory):
    python -m kubeopt scan
    python -m kubeopt scan --cluster my-cluster --top 10 --json
"""

import sys
import os

# Ensure cli.py is importable whether running from kubeopt/ or parent dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import main

sys.exit(main())
