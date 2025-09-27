#!/bin/bash

# Set the correct Python path to include virtual environment packages for Python 3.13
export PYTHONPATH="$(pwd)/.venv/lib/python3.13/site-packages:$PYTHONPATH"

# Use the Homebrew Python that can access the packages
exec /opt/homebrew/bin/python3 "$@"