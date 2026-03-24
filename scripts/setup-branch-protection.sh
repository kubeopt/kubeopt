#!/bin/bash
# Run this after making the repo public
# Usage: ./scripts/setup-branch-protection.sh

set -e

REPO="kubeopt/kubeopt"

echo "Setting up branch protection for $REPO..."

# Main branch protection
gh api repos/$REPO/branches/main/protection \
  -X PUT \
  --input - << 'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true
}
EOF

echo "[ok] Branch protection enabled on main"

# Disable direct pushes (require PRs)
gh api repos/$REPO/branches/main/protection/restrictions \
  -X PUT \
  --input - << 'EOF'
{
  "users": [],
  "teams": []
}
EOF

echo "[ok] Direct pushes restricted"
echo ""
echo "Rules applied:"
echo "  - PRs required (no direct push to main)"
echo "  - 1 approval required"
echo "  - Stale reviews dismissed on new pushes"
echo "  - CODEOWNERS review required"
echo "  - Linear history enforced (no merge commits)"
echo "  - Force pushes blocked"
echo "  - Branch deletion blocked"
echo "  - Conversations must be resolved before merge"
echo "  - Enforced for admins too"
