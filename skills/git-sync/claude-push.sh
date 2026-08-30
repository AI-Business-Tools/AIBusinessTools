#!/bin/bash
# claude-push.sh: commit the changes you just made to ~/.claude and send them
# to your private GitHub remote, so your other machine can pull them. Run this
# on the machine you just finished working on.
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
    echo "authentication, or remote problem rather than an editing one. Your committed" >&2
    echo "work is safe. Read the git error above and run claude-push again." >&2
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
    echo "and run claude-push again. Your committed work is safe." >&2
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
    echo "and run claude-push again. Your committed work is safe." >&2
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

# 1) Give settings.json a stable key order before it is staged, so the next merge
#    does not conflict over key order alone.
normalize_settings

# 2) Stage and commit anything new. If nothing changed, skip the commit.
#    `git add -A` stages every pending change in ~/.claude, so the commit carries
#    whatever any other session or agent left in the folder as well, under a
#    message describing only your own change. The second -m says so on every
#    push, rather than leaving the message to imply a single edit.
git add -A
if git diff --cached --quiet; then
    echo "No new changes to commit."
else
    MSG="${1:-snapshot from $(hostname -s)}"
    git commit -m "$MSG" -m "claude-push snapshot: contains every pending change in ~/.claude at push time, from all sessions, not only the change described above."
    echo "Committed: $MSG"
fi

# 3) Merge in anything the other machine pushed since your last sync, then push.
#    Pulling first means non-conflicting divergence merges automatically instead
#    of the push being rejected. --no-rebase keeps a true merge, which is right
#    for two-machine editing where both sides commit independently. The pull is
#    guarded two ways: it is skipped when the remote branch does not exist yet
#    (so the very first push does not fail), and a conflict goes to the resolver
#    above, which settles a per-device settings.json difference and stops on
#    everything else instead of leaving you stranded mid-merge.
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    if ! git pull --no-rebase --no-edit origin "$BRANCH"; then
        resolve_settings_conflict_or_stop
    fi
fi
git push -u origin "$BRANCH"
echo ""
echo "Pushed to origin/$BRANCH."

# --- Keep this note even if you delete the optional block below ---------------
# DO NOT ADD A LINE ANYWHERE IN THIS SCRIPT THAT DELETES
# ~/.claude/shell-snapshots/*.sh. This script carried one until 2026-08-21 and it
# was actively harmful. Every Claude Code session already running re-reads its own
# snapshot file on EVERY Bash call, so deleting it strips those sessions of
# whatever their shell config defined, including any safety wrapper around rm. It
# bought nothing in return: verified against the CLI at 2.1.238, a new session
# always writes a fresh snapshot from the current shell config and never reuses an
# existing one, and the CLI already handles retention itself (each session removes
# its own file at exit, and the cleanupPeriodDays sweep clears strays).
# ------------------------------------------------------------------------------

# --- Optional: Claude Code shell hygiene --------------------------------------
# Everything from here to the "end of optional block" line is safe to delete.
# It keeps claude-push / claude-pull resolving as real PATH commands whatever the
# shell has loaded. Idempotent. See setup.md, "Appendix," for why this helps.
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/.claude/claude-pull.sh" "$HOME/.local/bin/claude-pull"
ln -sf "$HOME/.claude/claude-push.sh" "$HOME/.local/bin/claude-push"
echo "Refreshed PATH links."
# --- end of optional block ----------------------------------------------------
