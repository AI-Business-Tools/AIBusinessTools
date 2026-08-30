#!/bin/bash
# claude-pull.sh: bring down the latest ~/.claude edits from your private
# GitHub remote. Run this on the machine you are about to work on, before you
# start editing.
set -euo pipefail

REPO="$HOME/.claude"
BRANCH="main"

cd "$REPO"

# Commit any local edits first, so the merge can never clobber uncommitted work.
git add -A
if ! git diff --cached --quiet; then
    git commit -m "local snapshot before pull on $(hostname -s)"
    echo "Saved local changes first."
fi

# Pull the other machine's edits. Guarded two ways: skipped when the remote has
# no branch yet (nothing to pull), and a real conflict stops with instructions
# instead of leaving you stranded mid-merge.
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    if ! git pull --no-rebase --no-edit origin "$BRANCH"; then
        echo ""
        echo "Sync stopped on a merge conflict. Open the file(s) listed above, remove the"
        echo "<<<<<<< / ======= / >>>>>>> marker lines, keep the text you want, then run:"
        echo "    git -C \"$REPO\" add -A && git -C \"$REPO\" commit --no-edit"
        echo "Your edits are safe; they were committed before the pull."
        exit 1
    fi
    echo "Pull complete."
else
    echo "Nothing to pull yet (the remote has no $BRANCH branch)."
fi

# --- Optional: Claude Code shell hygiene (safe to delete these lines) ---
# See claude-push.sh and setup.md, "Appendix," for what this does and why.
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/.claude/claude-pull.sh" "$HOME/.local/bin/claude-pull"
ln -sf "$HOME/.claude/claude-push.sh" "$HOME/.local/bin/claude-push"
# DO NOT ADD A LINE HERE THAT DELETES ~/.claude/shell-snapshots/*.sh. See the same
# note in claude-push.sh. In short: a running Claude Code session re-reads its own
# snapshot on every Bash call, so deleting it strips that session of whatever its
# shell config defined, including any safety wrapper around rm, and it buys nothing,
# because a new session always writes a fresh one and the CLI handles retention.
echo "Refreshed PATH links."
