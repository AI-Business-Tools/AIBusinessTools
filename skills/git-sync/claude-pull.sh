#!/bin/bash
# claude-pull.sh: bring down the latest ~/.claude edits from your private
# GitHub remote. Run this on the machine you are about to work on, before you
# start editing.
set -euo pipefail

REPO="$HOME/.claude"
BRANCH="main"

# Per-device settings.json keys: the ones each machine is meant to hold its own
# value for. A merge conflict confined to these can be settled by keeping this
# machine's copy of the file, and the resolver below is the only thing that ever
# does so. Edit this list to match how you work. Moving a key OUT of it is the
# conservative direction: a change to any key not listed here stops the sync for
# you to look at. Everything unlisted counts as shared, including keys a future
# Claude Code release adds. Shared keys are things like permissions, hooks, env,
# model, statusLine, apiKeyHelper, and includeCoAuthoredBy.
# Keep this list identical in claude-push.sh and claude-pull.sh.
PER_DEVICE_SETTINGS_KEYS='["agentPushNotifEnabled","autoMode","effortLevel","enabledPlugins","extraKnownMarketplaces","remoteControlAtStartup","skipAutoPermissionPrompt","skipDangerousModePermissionPrompt","skipWorkflowUsageWarning","theme","tui"]'

# Claude Code reserializes settings.json with a different key order on nearly
# every write. Committed as written, each machine records a differently ordered
# copy of the same content, and the next merge sees a whole-file conflict that is
# entirely cosmetic. Sorting the keys before every commit gives the file one
# stable committed form, so git's 3-way merge stays clean whenever the two
# machines changed different keys.
#
# The guards exist so this can never damage a working settings.json: it does
# nothing unless jq is installed and the file exists, it writes to a temp file in
# the same directory, it requires jq to parse the file and produce non-empty
# output before the file is touched at all, it carries the original mode over,
# and it swaps the files with a single atomic mv. On any failure the temp file is
# discarded and settings.json is left exactly as it was, so it cannot end up
# empty, truncated, or unparseable.
# Keep this function identical in claude-push.sh and claude-pull.sh.
normalize_settings() {
  local f="$REPO/settings.json" tmp mode
  command -v jq >/dev/null 2>&1 || return 0
  [[ -f "$f" ]] || return 0
  tmp="$(mktemp "${REPO}/.settings.json.XXXXXX")" || return 0
  if jq -S . "$f" >"$tmp" 2>/dev/null && [[ -s "$tmp" ]] && ! cmp -s "$f" "$tmp"; then
    mode="$(stat -f '%Lp' "$f" 2>/dev/null || stat -c '%a' "$f" 2>/dev/null || echo 644)"
    chmod "$mode" "$tmp" 2>/dev/null || true
    if mv "$tmp" "$f"; then return 0; fi
  fi
  rm -f "$tmp"
  return 0
}

# Print the names of the settings.json keys the OTHER machine changed relative to
# the merge base and that are not in PER_DEVICE_SETTINGS_KEYS. Empty output means
# the other machine touched nothing but per-device keys, so keeping this
# machine's whole file discards nothing shared. The comparison is theirs against
# the merge base (stages :1: and :3:), not theirs against ours, so a change made
# only on this machine never forces a stop. Any key the list does not name counts
# as shared, and every failure path (no jq, a missing merge stage, a jq error)
# returns a non-empty sentinel, so anything unreadable surfaces rather than
# resolving itself.
# Keep this function identical in claude-push.sh and claude-pull.sh.
settings_shared_keys_changed() {
  command -v jq >/dev/null 2>&1 || { echo "<jq-unavailable>"; return 0; }
  local base theirs out
  base="$(git show :1:settings.json 2>/dev/null || true)"
  theirs="$(git show :3:settings.json 2>/dev/null || true)"
  if [[ -z "$base" || -z "$theirs" ]]; then echo "<stage-missing>"; return 0; fi
  out="$(jq -nr --argjson tog "$PER_DEVICE_SETTINGS_KEYS" --argjson b "$base" --argjson t "$theirs" '
    ($b + $t | keys_unsorted | unique)[] as $k
    | select($b[$k] != $t[$k])
    | select(($tog | index($k)) | not)
    | $k' 2>/dev/null)" || { echo "<jq-error>"; return 0; }
  printf '%s' "$out"
}

# Settle a merge conflict, or stop and hand it to you. It settles exactly one
# case: settings.json is the ONLY conflicted file AND the other machine changed
# nothing outside PER_DEVICE_SETTINGS_KEYS. That is the routine cross-machine
# divergence, and hand-reconciling it every sync is pure friction. Anything else
# (a second conflicted file, a shared or unrecognized key, a pull that failed
# without a conflict at all) stops with the merge still in progress, so a real
# conflict is never hidden. The gate is narrow because the remedy is blunt:
# `git checkout --ours` keeps the whole file, so a shared change on the other
# side would go with it.
# Keep this function identical in claude-push.sh and claude-pull.sh.
resolve_settings_conflict_or_stop() {
  local conflicts shared
  conflicts="$(git diff --name-only --diff-filter=U)"
  if [[ -z "$conflicts" ]]; then
    echo "" >&2
    echo "Sync stopped: the pull failed without a merge conflict, so this is a network," >&2
    echo "authentication, or remote problem rather than an editing one. Your edits are" >&2
    echo "safe; they were committed before the pull. Read the git error above and run" >&2
    echo "claude-pull again." >&2
    git merge --abort 2>/dev/null || true
    exit 1
  fi
  if [[ "$conflicts" != "settings.json" ]]; then
    echo "" >&2
    echo "Sync stopped on a merge conflict in:" >&2
    echo "$conflicts" >&2
    echo "Open each file, remove the <<<<<<< / ======= / >>>>>>> marker lines, keep the" >&2
    echo "text you want, then run:" >&2
    echo "    git -C \"$REPO\" add -A && git -C \"$REPO\" commit --no-edit" >&2
    echo "Your edits are safe; they were committed before the pull." >&2
    exit 1
  fi
  shared="$(settings_shared_keys_changed)"
  if [[ -n "$shared" ]]; then
    echo "" >&2
    echo "Sync stopped on settings.json. The other machine changed keys that are not in" >&2
    echo "PER_DEVICE_SETTINGS_KEYS, so this script will not pick a winner for you:" >&2
    echo "  $shared" >&2
    echo "(A name in angle brackets means the comparison itself could not be made, so it" >&2
    echo "stopped rather than guess.) Resolve settings.json by hand, then run:" >&2
    echo "    git -C \"$REPO\" add -A && git -C \"$REPO\" commit --no-edit" >&2
    echo "Your edits are safe; they were committed before the pull." >&2
    exit 1
  fi
  echo "settings.json conflict: only per-device keys differ. Keeping this machine's values."
  echo "--- the other machine's settings.json changes, which are not being adopted ---"
  git --no-pager diff HEAD...MERGE_HEAD -- settings.json || true
  git checkout --ours -- settings.json \
    && git add settings.json \
    && git commit --no-edit \
    || { echo "ERROR: could not finish the settings.json resolve; merge left in progress." >&2; exit 1; }
  echo "settings.json conflict resolved automatically (per-device keys only)."
  echo "To see what was set aside: git -C \"$REPO\" diff HEAD^1...HEAD^2 -- settings.json"
}

cd "$REPO"

# Give settings.json a stable key order before it is staged, so this pull and the
# next one do not conflict over key order alone.
normalize_settings

# Commit any local edits first, so the merge can never clobber uncommitted work.
git add -A
if ! git diff --cached --quiet; then
    git commit -m "local snapshot before pull on $(hostname -s)"
    echo "Saved local changes first."
fi

# Pull the other machine's edits. Guarded two ways: skipped when the remote has
# no branch yet (nothing to pull), and a conflict goes to the resolver above,
# which settles a per-device settings.json difference and stops on everything
# else instead of leaving you stranded mid-merge.
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    if ! git pull --no-rebase --no-edit origin "$BRANCH"; then
        resolve_settings_conflict_or_stop
    fi
    echo "Pull complete."
else
    echo "Nothing to pull yet (the remote has no $BRANCH branch)."
fi

# --- Keep this note even if you delete the optional block below ---------------
# DO NOT ADD A LINE ANYWHERE IN THIS SCRIPT THAT DELETES
# ~/.claude/shell-snapshots/*.sh. See the same note in claude-push.sh. In short: a
# running Claude Code session re-reads its own snapshot on every Bash call, so
# deleting it strips that session of whatever its shell config defined, including
# any safety wrapper around rm, and it buys nothing, because a new session always
# writes a fresh one and the CLI handles retention.
# ------------------------------------------------------------------------------

# --- Optional: Claude Code shell hygiene --------------------------------------
# Everything from here to the "end of optional block" line is safe to delete.
# See claude-push.sh and setup.md, "Appendix," for what this does and why.
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/.claude/claude-pull.sh" "$HOME/.local/bin/claude-pull"
ln -sf "$HOME/.claude/claude-push.sh" "$HOME/.local/bin/claude-push"
echo "Refreshed PATH links."
# --- end of optional block ----------------------------------------------------
