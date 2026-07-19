import os
os.environ.setdefault("LOCAL_DEV", "true")

import sys

# Add the parent of kubeopt/ to sys.path so that `from kubeopt.x import y` works
# when pytest is run from inside the kubeopt/ directory.
_kubeopt_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_parent = os.path.dirname(_kubeopt_root)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

