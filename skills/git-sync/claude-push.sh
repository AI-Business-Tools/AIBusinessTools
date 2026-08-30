#!/bin/bash
# claude-push.sh: commit the changes you just made to ~/.claude and send them
# to your private GitHub remote, so your other machine can pull them. Run this
# on the machine you just finished working on.
set -euo pipefail

REPO="$HOME/.claude"
BRANCH="main"
SELF_CMD="claude-push"

# Set CLAUDE_SYNC_SKIP_SECRET_SCAN=1 for a single run whose only
# credential-shaped lines are ones you have looked at and know are examples.
SKIP_SECRET_SCAN="${CLAUDE_SYNC_SKIP_SECRET_SCAN:-0}"

# Credential prefixes that are almost never anything else. The list is short on
# purpose: a check that fires on ordinary prose gets ignored or switched off, and
# then it is protecting nothing.
CRED_PATTERN='sk-ant-|sk-proj-|ghp_|gho_|ghu_|ghs_|github_pat_|xoxb-|xoxp-|xoxa-|xoxr-|AKIA[A-Z0-9]|ASIA[A-Z0-9]|AIza[A-Za-z0-9]|PRIVATE KEY-----'

# --- shared helpers -----------------------------------------------------------
# Everything down to "end of shared helpers" is byte-identical in claude-push.sh
# and claude-pull.sh. The scripts do not read each other, so if you edit one,
# paste the same block into the other. Anything that has to name the command the
# user typed uses $SELF_CMD, which is set above.

# Claude Code reserializes settings.json with a different key order on nearly
# every write. Committed as written, each machine records a differently ordered
# copy of the same content, and the next merge sees a whole-file conflict that is
# entirely cosmetic. Sorting the keys before every commit gives each file one
# stable committed form, so git's 3-way merge stays clean whenever the two
# machines changed different keys. settings.local.json gets the same treatment
# for the same reason.
#
# The guards exist so this can never damage a working settings file: it does
# nothing unless jq is installed and the file exists, it writes to a temp file in
# the same directory, it requires jq to parse the file and produce non-empty
# output before the file is touched at all, it carries the original mode over,
# and it swaps the files with a single atomic mv. On any failure the temp file is
# discarded and the settings file is left exactly as it was, so it cannot end up
# empty, truncated, or unparseable.
#
# A symlinked settings file is skipped rather than followed. Git stores the link
# itself, not the JSON behind it, so normalizing that content would not change a
# single merge, while the mv below would replace the link with a regular file
# and, because macOS `stat` reads the link's own mode rather than the target's,
# would leave it at 755.
normalize_settings() {
  local f tmp mode
  command -v jq >/dev/null 2>&1 || return 0
  for f in "$REPO/settings.json" "$REPO/settings.local.json"; do
    if [[ -L "$f" ]]; then continue; fi
    [[ -f "$f" ]] || continue
    tmp="$(mktemp "${REPO}/.settings-normalize.XXXXXX")" || continue
    if jq -S . "$f" >"$tmp" 2>/dev/null && [[ -s "$tmp" ]] && ! cmp -s "$f" "$tmp"; then
      mode="$(stat -f '%Lp' "$f" 2>/dev/null || stat -c '%a' "$f" 2>/dev/null || echo 644)"
      chmod "$mode" "$tmp" 2>/dev/null || true
      if mv "$tmp" "$f"; then continue; fi
    fi
    rm -f "$tmp"
  done
  return 0
}

# Refuse to touch the index while a merge is unfinished. Without this, running
# either script again after a stopped conflict is silently destructive: `git add
# -A` marks the conflicted paths resolved exactly as they sit on disk, the commit
# seals the merge, and the push publishes files that still contain the marker
# lines. The other machine then fast-forwards onto them.
stop_if_merge_in_progress() {
  local unresolved
  unresolved="$(git diff --name-only --diff-filter=U 2>/dev/null || true)"
  if [[ -f "$(git rev-parse --git-path MERGE_HEAD)" || -n "$unresolved" ]]; then
    cat >&2 <<EOF

Sync stopped: an earlier merge in ~/.claude was never finished, so nothing here
will stage or commit until it is. Committing now would publish half-merged files
to the other machine.

Unfinished files:
$(printf '%s\n' "$unresolved" | sed 's/^/  /')

Finish it, in this order:

  1. Open each file above and delete the marker lines git left in it (the lines
     starting with seven angle brackets or seven equals signs), along with the
     version you do not want. What you keep can be a blend of both machines.
  2. git -C "$REPO" add -A
  3. git -C "$REPO" commit --no-edit
  4. claude-push

To see one file's two versions before you choose:
  git -C "$REPO" show :2:PATH    # this machine
  git -C "$REPO" show :3:PATH    # the other machine

To throw the whole merge away and go back to where you were:
  git -C "$REPO" merge --abort
EOF
    exit 1
  fi
}

# Second line of defence: a file can carry conflict markers with no merge in
# progress, if one was staged or committed by hand. A file counts only when it
# holds both an opening and a closing marker, so prose that happens to start a
# line with equals signs does not trip it.
stop_if_conflict_markers() {
  local p flagged=""
  while IFS= read -r -d '' p; do
    if [[ -f "$p" && ! -L "$p" ]]; then
      if grep -qI -e '^<<<<<<< ' -- "$p" 2>/dev/null \
         && grep -qI -e '^>>>>>>> ' -- "$p" 2>/dev/null; then
        flagged="${flagged}  ${p}"$'\n'
      fi
    fi
  done < <( { git ls-files -mo --exclude-standard -z; \
              git diff --cached --name-only -z --diff-filter=ACM; } 2>/dev/null )
  if [[ -n "$flagged" ]]; then
    cat >&2 <<EOF

Sync stopped: these files still contain merge conflict markers, so they are not
finished text and will not be committed.

$(printf '%s' "$flagged" | sort -u)

Open each one, delete the marker lines (seven angle brackets or seven equals
signs at the start of a line) and the version you do not want, then run
$SELF_CMD again.
EOF
    exit 1
  fi
}

# Look at the lines about to be committed rather than at the whole repository, so
# this reports something just introduced instead of re-reporting the same file on
# every sync. It skips the two sync scripts, whose own pattern list above would
# otherwise match them.
stop_if_new_credentials() {
  if [[ "$SKIP_SECRET_SCAN" == "1" ]]; then return 0; fi
  local hits
  hits="$(git diff --cached --unified=0 --no-color | awk -v pat="$CRED_PATTERN" '
    /^\+\+\+ b\// { file = substr($0, 7); next }
    /^\+/ { if (file !~ /claude-(push|pull)\.sh$/ && $0 ~ pat) print "  " file }
  ' | sort -u || true)"
  if [[ -n "$hits" ]]; then
    cat >&2 <<EOF

Sync stopped: a line about to be committed looks like a live API key, token, or
private key. GitHub is the wrong place for one even in a private repository.

$hits

Look at each file. If it holds a real credential, take the value out of the file
and keep it in your shell environment or a password manager instead. If the file
should never have been tracked at all, add its path to ~/.claude/.gitignore and
run:
  git -C "$REPO" rm --cached PATH
Then run $SELF_CMD again.

If you have looked and it is an example rather than a live credential, run:
  CLAUDE_SYNC_SKIP_SECRET_SCAN=1 $SELF_CMD
EOF
    exit 1
  fi
}

# A pull fails in two quite different ways, so tell them apart by whether git
# actually left a conflict behind, and give each its own advice.
stop_on_failed_pull() {
  local conflicts
  conflicts="$(git diff --name-only --diff-filter=U 2>/dev/null || true)"
  if [[ -z "$conflicts" ]]; then
    git merge --abort 2>/dev/null || true
    cat >&2 <<EOF

Sync stopped: the pull failed without a merge conflict, so this is a network,
authentication, or remote problem rather than an editing one. Your work is
committed here and nothing is lost. Read the git error above, then run $SELF_CMD
again once the connection or the login is working.
EOF
    exit 1
  fi
  cat >&2 <<EOF

Sync stopped: git could not merge these files on its own, because the same lines
were edited on both machines.

$(printf '%s\n' "$conflicts" | sed 's/^/  /')

Nothing is lost: your own edits were committed before the merge started. Do not
simply run the command again. Both scripts now refuse to run while this merge is
open, because running them again used to commit the half-merged files and push
them to the other machine.

Resolve it, in this order:

  1. Open each file above. Git has put both versions in it, wrapped in marker
     lines starting with seven angle brackets or seven equals signs. Delete those
     lines and the version you do not want. What you keep can be a blend of both.
  2. git -C "$REPO" add -A
  3. git -C "$REPO" commit --no-edit
  4. claude-push

To see one file's two versions first:
  git -C "$REPO" show :2:PATH    # this machine
  git -C "$REPO" show :3:PATH    # the other machine

To throw the merge away and go back to where you were:
  git -C "$REPO" merge --abort
EOF
  exit 1
}

# A file this machine ignores can still arrive from the other machine, if it was
# force-added there. Git overwrites an ignored file during a merge without
# asking, so say what happened.
warn_ignored_incoming() {
  local before="$1" incoming ignored
  [[ -n "$before" ]] || return 0
  incoming="$(git diff --name-only -z "$before" HEAD 2>/dev/null || true)"
  [[ -n "$incoming" ]] || return 0
  ignored="$(printf '%s' "$incoming" | git check-ignore --no-index -z --stdin 2>/dev/null | tr '\0' '\n' || true)"
  if [[ -n "$ignored" ]]; then
    cat <<EOF

Note: the pull brought in files that this machine's .gitignore excludes. They
were force-added on the other machine, so this machine's copy of each has just
been overwritten without a prompt:

$(printf '%s' "$ignored" | sed 's/^/  /')

If one of them held something only this machine wanted, git may not have kept a
copy, since a file this machine ignores is not committed here. Try:
  git -C "$REPO" show ${before}:PATH
If that says the path does not exist, the old contents are only in your backup.
EOF
  fi
}

require_remote() {
  if ! git remote get-url origin >/dev/null 2>&1; then
    cat >&2 <<EOF

Sync stopped: ~/.claude has no 'origin' remote, so there is nowhere to send
anything. Follow setup.md Step 4 to add one:
  git -C "$REPO" remote add origin https://github.com/USERNAME/REPO-NAME.git
EOF
    exit 1
  fi
}

# Probing reachability on its own is what makes the message below reachable at
# all. `git ls-remote --exit-code --heads origin main` also returns non-zero for
# a remote that simply has no branch yet, so a single check cannot tell an
# unreachable remote from a brand-new one, and the real failure surfaces later as
# a raw git error.
require_reachable_remote() {
  if ! git ls-remote --heads origin >/dev/null 2>&1; then
    cat >&2 <<EOF

Sync stopped: GitHub could not be reached. Your work is committed here and
nothing is lost.

Usual causes, in order: no network; the login has expired or was never done on
this machine; the remote URL is wrong or the repository was renamed.

Check with:
  git -C "$REPO" remote -v
  gh auth status                 # if you set this up with the GitHub CLI
  ssh -T git@github.com          # if you set this up with an SSH key

Then run $SELF_CMD again.
EOF
    exit 1
  fi
}

require_git_identity() {
  if [[ -z "$(git config user.name || true)" || -z "$(git config user.email || true)" ]]; then
    cat >&2 <<EOF

Sync stopped: git does not know who you are, so it cannot make a commit. Set it
once on this machine:
  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"

Then run $SELF_CMD again.
EOF
    exit 1
  fi
}

# --- end of shared helpers ----------------------------------------------------

cd "$REPO"

# 1) Refuse to touch the index while an earlier merge is unfinished.
stop_if_merge_in_progress

# 2) Give the settings files a stable key order before they are staged, so the
#    next merge does not conflict over key order alone.
normalize_settings

# 3) Refuse to stage a file that still holds conflict markers.
stop_if_conflict_markers

require_remote

# 4) Stage and commit anything new. If nothing changed, skip the commit.
#    `git add -A` stages every pending change in ~/.claude, so the commit carries
#    whatever any other session or agent left in the folder as well, under a
#    message describing only your own change. The second -m says so on every
#    push, rather than leaving the message to imply a single edit.
git add -A
if git diff --cached --quiet; then
    echo "No new changes to commit."
else
    stop_if_new_credentials
    require_git_identity
    MSG="${1:-snapshot from $(hostname -s)}"
    git commit -m "$MSG" -m "claude-push snapshot: contains every pending change in ~/.claude at push time, from all sessions, not only the change described above."
    echo "Committed: $MSG"
fi

# 5) Merge in anything the other machine pushed since your last sync, then push.
#    Pulling first means non-conflicting divergence merges automatically instead
#    of the push being rejected. --no-rebase keeps a true merge, which is right
#    for two-machine editing where both sides commit independently. The pull is
#    skipped when the remote branch does not exist yet, so the very first push
#    does not fail. Any conflict stops the sync with the merge still in progress,
#    to be resolved by hand: nothing here picks a winner for you.
require_reachable_remote
BEFORE_PULL="$(git rev-parse HEAD 2>/dev/null || echo "")"
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    if ! git pull --no-rebase --no-edit origin "$BRANCH"; then
        stop_on_failed_pull
    fi
    warn_ignored_incoming "$BEFORE_PULL"
fi

if ! git push -u origin "$BRANCH"; then
    cat >&2 <<EOF

Sync stopped: the push was refused. Your work is committed here and nothing is
lost. Read the git error above. The two common causes are a rejected push,
meaning the other machine pushed something in the last few seconds (run
claude-pull, then claude-push), and a login that has expired.
EOF
    exit 1
fi
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
