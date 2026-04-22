#!/usr/bin/env bash
# install-kubectl-plugin.sh
# Installs the kubectl-kubeopt plugin to /usr/local/bin.
#
# Usage:
#   ./scripts/install-kubectl-plugin.sh
#
# The script must be run from inside the kubeopt source tree (or with
# KUBEOPT_SRC set to the repo root).
#
# Developer: Srinivas Kondepudi
# Organization: Nivaya Technologies PTY LTD

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve source root (repo root, where cli.py lives)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KUBEOPT_SRC="${KUBEOPT_SRC:-$(realpath "$SCRIPT_DIR/..")}"

PLUGIN_SRC="$SCRIPT_DIR/kubectl-kubeopt"
INSTALL_DIR="/usr/local/bin"
INSTALL_DEST="$INSTALL_DIR/kubectl-kubeopt"

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
if [[ ! -f "$PLUGIN_SRC" ]]; then
    echo "ERROR: Plugin script not found at $PLUGIN_SRC" >&2
    echo "       Run this install script from the kubeopt source tree." >&2
    exit 1
fi

if [[ ! -f "$KUBEOPT_SRC/cli.py" ]]; then
    echo "WARNING: cli.py not found at $KUBEOPT_SRC/cli.py" >&2
    echo "         The plugin will still be installed, but scans will fail" >&2
    echo "         until cli.py is present. Set \$KUBEOPT_SRC to override." >&2
fi

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
echo ""
echo "Installing kubectl-kubeopt..."
echo "  Source : $PLUGIN_SRC"
echo "  Dest   : $INSTALL_DEST"
echo "  KUBEOPT_HOME will be set to: $KUBEOPT_SRC"
echo ""

# Copy the plugin script
if [[ -w "$INSTALL_DIR" ]]; then
    cp "$PLUGIN_SRC" "$INSTALL_DEST"
    chmod +x "$INSTALL_DEST"
else
    echo "  (requires sudo to write to $INSTALL_DIR)"
    sudo cp "$PLUGIN_SRC" "$INSTALL_DEST"
    sudo chmod +x "$INSTALL_DEST"
fi

# ---------------------------------------------------------------------------
# Emit a shell profile snippet so KUBEOPT_HOME is always set
# ---------------------------------------------------------------------------
PROFILE_SNIPPET="export KUBEOPT_HOME=\"$KUBEOPT_SRC\""
PROFILE_COMMENT="# KubeOpt kubectl plugin — installation path"

echo ""
echo "----------------------------------------------------------------------"
echo "Add the following line to your shell profile (~/.zshrc, ~/.bashrc, …):"
echo ""
echo "  $PROFILE_COMMENT"
echo "  $PROFILE_SNIPPET"
echo ""
echo "Or run this one-liner now:"
echo ""
echo "  echo '$PROFILE_COMMENT' >> ~/.zshrc && echo '$PROFILE_SNIPPET' >> ~/.zshrc"
echo "----------------------------------------------------------------------"
echo ""

# ---------------------------------------------------------------------------
# Verify kubectl can see the plugin
# ---------------------------------------------------------------------------
if command -v kubectl &>/dev/null; then
    if kubectl plugin list 2>/dev/null | grep -q "kubectl-kubeopt"; then
        echo "kubectl detects the plugin:"
        kubectl plugin list 2>/dev/null | grep "kubectl-kubeopt" || true
    else
        echo "NOTE: kubectl plugin list does not yet show kubectl-kubeopt."
        echo "      Make sure $INSTALL_DIR is on your \$PATH."
    fi
else
    echo "NOTE: kubectl not found on \$PATH — install kubectl to use this plugin."
fi

echo ""
echo "Installation complete."
echo ""
echo "Example usage:"
echo "  kubectl kubeopt scan"
echo "  kubectl kubeopt scan --cluster my-aks-prod"
echo "  kubectl kubeopt scan --top 5"
echo "  kubectl kubeopt scan --cluster my-eks-dev --top 10 --json"
echo "  kubectl kubeopt version"
echo ""
