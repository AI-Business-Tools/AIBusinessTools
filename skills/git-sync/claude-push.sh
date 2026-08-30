#!/bin/bash
# claude-push.sh: commit the changes you just made to ~/.claude and send them
# to your private GitHub remote, so your other machine can pull them. Run this
# on the machine you just finished working on.
set -euo pipefail

REPO="$HOME/.claude"
BRANCH="main"

cd "$REPO"

# 1) Stage and commit anything new. If nothing changed, skip the commit.
git add -A
if git diff --cached --quiet; then
    echo "No new changes to commit."
else
    MSG="${1:-snapshot from $(hostname -s)}"
    git commit -m "$MSG"
    echo "Committed: $MSG"
fi

# 2) Merge in anything the other machine pushed since your last sync, then push.
#    Pulling first means non-conflicting divergence merges automatically instead
#    of the push being rejected. --no-rebase keeps a true merge, which is right
#    for two-machine editing where both sides commit independently. The pull is
#    guarded two ways: it is skipped when the remote branch does not exist yet
#    (so the very first push does not fail), and a real conflict stops with
#    instructions instead of leaving you stranded mid-merge.
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    if ! git pull --no-rebase --no-edit origin "$BRANCH"; then
        echo ""
        echo "Sync stopped on a merge conflict. Open the file(s) listed above, remove the"
        echo "<<<<<<< / ======= / >>>>>>> marker lines, keep the text you want, then run:"
        echo "    git -C \"$REPO\" add -A && git -C \"$REPO\" commit --no-edit"
        echo "and run claude-push again. Your committed work is safe."
        exit 1
    fi
fi
git push -u origin "$BRANCH"
echo ""
echo "Pushed to origin/$BRANCH."

# --- Optional: Claude Code shell hygiene (safe to delete these lines) ---
# Keeps claude-push / claude-pull resolving as real PATH commands whatever the
# shell has loaded. Idempotent. See setup.md, "Appendix," for why this helps.
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/.claude/claude-pull.sh" "$HOME/.local/bin/claude-pull"
ln -sf "$HOME/.claude/claude-push.sh" "$HOME/.local/bin/claude-push"
# DO NOT ADD A LINE HERE THAT DELETES ~/.claude/shell-snapshots/*.sh. This script
# carried one until 2026-08-21 and it was actively harmful. Every Claude Code
# session already running re-reads its own snapshot file on EVERY Bash call, so
# deleting it strips those sessions of whatever their shell config defined,
# including any safety wrapper around rm. It bought nothing in return: verified
# against the CLI at 2.1.238, a new session always writes a fresh snapshot from
# the current shell config and never reuses an existing one, and the CLI already
# handles retention itself (each session removes its own file at exit, and the
# cleanupPeriodDays sweep clears strays).
echo "Refreshed PATH links."
