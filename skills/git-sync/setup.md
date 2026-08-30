# Setup: Git Sync for Your Claude Code Environment

This recipe turns `~/.claude` into a Git repository and connects it to a private GitHub repository, so you have version history and can keep two machines in sync. Read `README.md` first if you want the why; this file is the how.

You can run every step yourself, or you can let Claude Code run them for you.

## Let Claude Code do it

Open Claude Code in any project and say:

> Read `git-sync/setup.md` and set up Git sync for my `~/.claude` environment, then tell me how to use it.

Claude Code will create the private repository (or get you through `gh auth login` first), write the `.gitignore`, scan for secrets, make the first commit and push, install the `claude-push` and `claude-pull` commands, and explain the daily routine. The rest of this file is the same recipe written out, for doing it by hand or for following along while Claude Code works.

## Prerequisites

- Git installed (`git --version`).
- A GitHub account.
- One of: the GitHub CLI (`gh`), or an SSH key added to your GitHub account. The steps below use `gh` as the primary path and note the SSH alternative where it differs.
- Optional but recommended: `jq` (`brew install jq`, or `apt install jq`). The scripts use it to keep `settings.json` from producing cosmetic merge conflicts. Without it they skip that handling and everything else still works. See "settings.json: key order and per-device keys."

Throughout, replace `USERNAME` with your GitHub username and `claude-env` with whatever you want to name the repository.

## Step 1: Create a private GitHub repository

**With the GitHub CLI (recommended).**

```
gh auth login            # once per machine, if you have not already
gh repo create claude-env --private --description "My Claude Code environment"
```

Do not initialize it with a README. You want it empty, so your first push defines the history.

**With SSH instead of the CLI.** Create an empty private repository in the GitHub web UI (no README, no `.gitignore`, no license). Make sure you have an SSH key on this machine that is added to your GitHub account; `ssh -T git@github.com` should greet you by username. You will use the `git@github.com:USERNAME/claude-env.git` remote URL in Step 4.

## Step 2: Initialize Git in ~/.claude and add the .gitignore

```
cd ~/.claude
git init -b main
```

Copy `gitignore.sample` from this directory to `~/.claude/.gitignore`. It is shipped under that name so it does not take effect inside the recipe's own folder; once copied to `~/.claude/.gitignore` it becomes active for your environment. It uses an allowlist: it ignores everything, then re-includes only the authored paths (`CLAUDE.md`, `CLAUDE.local.md`, `settings.json`, `settings.local.json`, `keybindings.json`, `skills/`, `scripts/`, `protocols/`, `changelog/`, `hooks/`, the two sync scripts, and `projects/*/memory/`). Open it and add a line for any other root-level file you author and want tracked.

## Step 3: Scan for secrets before the first commit

Even though the repository is private, do not commit keys or tokens. Check what is about to be tracked:

```
cd ~/.claude
git add -A
git status                          # review the file list
git diff --cached | grep -nEi 'api[_-]?key|secret|token|password|bearer|-----BEGIN' || echo "No obvious secrets found."
```

The scan flags candidates to review, not certain secrets. It will also match documentation that merely mentions a word like "token" or "key," which is fine; look at each hit and decide. If anything sensitive shows up, add its path or pattern to `.gitignore`, then run `git rm --cached <path>` and re-check. The sample already excludes `.env`, `*.key`, `*.pem`, and `.credentials.json` everywhere.

## Step 4: First commit and push

```
cd ~/.claude
git commit -m "Baseline: authored Claude Code environment"
```

Add the remote and push. The CLI may have set the remote when you created the repo; if `git remote -v` shows nothing, add it:

```
git remote add origin https://github.com/USERNAME/claude-env.git    # or git@github.com:USERNAME/claude-env.git for SSH
git push -u origin main
```

Your environment now has a history and a private copy on GitHub.

## Step 5: Install the two commands

Copy `claude-push.sh` and `claude-pull.sh` from this directory into `~/.claude`, make them executable, and put them on your PATH:

```
cp claude-push.sh claude-pull.sh ~/.claude/
chmod +x ~/.claude/claude-push.sh ~/.claude/claude-pull.sh
mkdir -p ~/.local/bin
ln -sf ~/.claude/claude-push.sh ~/.local/bin/claude-push
ln -sf ~/.claude/claude-pull.sh ~/.local/bin/claude-pull
```

Make sure `~/.local/bin` is on your PATH. If it is not, add `export PATH="$HOME/.local/bin:$PATH"` to your shell profile (`~/.zshrc` or `~/.bashrc`). Open a new terminal and confirm:

```
command -v claude-push && command -v claude-pull
```

## Step 6: Add a second machine (optional)

You have two clean options on the second machine.

**Fresh start (simplest).** If the second machine has nothing in `~/.claude` you need to keep, back up whatever is there, then clone:

```
mv ~/.claude ~/.claude.bak-$(date +%Y%m%d)            # only if ~/.claude already exists
git clone https://github.com/USERNAME/claude-env.git ~/.claude
```

Then repeat Step 5 on this machine to install the commands.

**Keep this machine's existing edits.** If the second machine already has a `~/.claude` you want to preserve, adopt the shared history in place:

```
cd ~/.claude
git init -b main
git remote add origin https://github.com/USERNAME/claude-env.git
git fetch origin
git reset --mixed origin/main          # adopt the remote history, keep your files on disk
git add -A
git commit -m "Local state on second machine"
git pull --no-rebase --no-edit origin main    # merge the two histories
git push origin main
```

Where the same file exists on both machines with different contents, this machine's copy becomes the new shared version on the push. If you want the first machine's version of a particular file instead, restore it with `git checkout origin/main -- path/to/file` before you commit.

This is exactly the kind of step Claude Code can run for you: point it at this file on the second machine and ask it to connect the machine to your existing repository.

## Day-to-day use

- Sitting down at a machine: `claude-pull` to get the other machine's latest edits.
- Finishing up: `claude-push "short note about what changed"` to commit and send them. The message is optional; the script supplies a default if you omit it.

`claude-push` pulls before it pushes, so if you forgot to pull at the start, or pushed out of order from the other machine, non-conflicting edits merge automatically. If the same lines were changed on both machines, the sync stops and asks you to resolve the conflict (see the next section). On a single machine, `claude-push` alone is a fine commit-and-back-up habit.

## If a sync stops on a conflict

A conflict happens only when the same lines of the same file were changed on both machines before they synced. Git cannot guess which version you want, so the sync stops and leaves both versions in the file, marked like this:

```
<<<<<<< HEAD
your version on this machine
=======
the version from the other machine
>>>>>>> origin/main
```

To resolve it, open the file, delete the `<<<<<<<`, `=======`, and `>>>>>>>` marker lines, keep the text you want (it can be a blend of both), then run:

```
git -C ~/.claude add -A
git -C ~/.claude commit --no-edit
```

Run `claude-push` again to send the resolved version. Your committed work is never lost in a conflict: the scripts commit local edits before they pull, so resolving is always just an edit and a commit, never a recovery. Claude Code can do this for you if you ask it to open the file and remove the markers.

One narrow case is settled for you instead of stopping the sync: a conflict in `settings.json` alone, where the only difference is a setting each machine is meant to hold its own value for. The next section explains that, and what the scripts will not decide on their own.

## settings.json: key order and per-device keys

`settings.json` is the one file in `~/.claude` that both machines rewrite constantly without you editing it, and it is the usual source of a conflict you did not cause. Two things in the scripts handle it.

### The problem

Claude Code rewrites `settings.json` on nearly every session, and it does not preserve the order of the keys. Open the file after a week and the same settings sit in a different order. That means each machine commits a differently ordered copy of what is often identical content. Git compares text, not meaning, so when the two histories merge it sees a file whose lines changed everywhere on both sides, and it reports a whole-file conflict over nothing.

On top of that, some settings are genuinely meant to differ between machines: the theme, the terminal interface preferences, the effort level, notification and prompt toggles. Those are real differences, not noise, but you do not want to hand-reconcile them every time you sync.

### Mechanism 1: one stable key order

Both scripts run `settings.json` through `jq -S`, which sorts the keys alphabetically, before anything is staged for commit. Every commit from either machine then records the file in the same order, so git can compare the two sides key by key. When the machines changed different settings, the merge succeeds silently and both changes survive.

This only rewrites the order. No value is added, removed, or altered. It is skipped entirely when `jq` is not installed, and it is written so it cannot damage the file: it works on a temporary copy in the same folder, requires `jq` to parse the file and produce non-empty output before anything is replaced, keeps the file's permissions, and swaps in the result with a single atomic move. If any step fails, the temporary copy is discarded and your `settings.json` is left exactly as it was.

### Mechanism 2: a narrow automatic conflict resolver

Sorting the keys removes the cosmetic conflicts. It does not remove the real ones, where both machines changed the same setting to different values, which for the per-device settings is the normal state of affairs rather than a mistake.

So both scripts will settle a conflict automatically in one case, and only this case:

- `settings.json` is the **only** conflicted file, **and**
- every key the other machine changed is in the per-device list.

When both hold, the script keeps this machine's `settings.json`, prints the other machine's changes so you can see what was not adopted, finishes the merge, and prints a command that recovers the discarded version from the merge commit later.

It will **not** decide anything else. Each of these stops the sync and leaves the merge in progress for you:

- Any other file is also conflicted.
- The other machine changed a key that is not in the per-device list, including any key you have not classified and any key a future Claude Code release adds.
- The comparison cannot be made at all: `jq` is missing, a merge stage is unreadable, or `jq` errors. The script prints a name in angle brackets, such as `<jq-unavailable>`, and stops.
- The pull failed for a reason that is not a conflict, such as a network or authentication problem.

The gate is deliberately narrow because the remedy is blunt. Keeping "this machine's `settings.json`" keeps the whole file, not the individual keys, so if the other machine had also changed something shared, that change would go with it. Restricting the automatic path to keys nobody expects to travel between machines is what makes a whole-file decision safe.

### Editing the key list

The list lives at the top of both `claude-push.sh` and `claude-pull.sh`, as a JSON array named `PER_DEVICE_SETTINGS_KEYS`. It ships with the settings that are normally machine-specific: `agentPushNotifEnabled`, `autoMode`, `effortLevel`, `enabledPlugins`, `extraKnownMarketplaces`, `remoteControlAtStartup`, `skipAutoPermissionPrompt`, `skipDangerousModePermissionPrompt`, `skipWorkflowUsageWarning`, `theme`, and `tui`.

Everything else counts as shared and will stop the sync rather than resolve: `permissions`, `hooks`, `env`, `model`, `statusLine`, `apiKeyHelper`, `includeCoAuthoredBy`, and anything else you or a future release put in the file.

Two rules for editing it:

1. Keep the two copies identical. The scripts do not read each other.
2. Removing a key from the list is the safe direction. It means more conflicts get handed to you, never fewer. Adding a key is the direction to think about, because it tells the script that a change to that key on the other machine can be discarded without asking.

The two most likely to want removing are `enabledPlugins` and `extraKnownMarketplaces`. They are listed as per-device because plugin sets often differ by machine. If instead you want your plugins to be the same everywhere, take them out of the list so a plugin change on the other machine stops the sync for you to look at.

If you do not have `jq` installed, both mechanisms switch themselves off and you get the plain behavior described in the previous section: every conflict, cosmetic or real, comes to you to resolve by hand.

## Running it from inside Claude Code

You do not need a separate terminal for the routine sync. `claude-push` and `claude-pull` are ordinary commands on your PATH, so Claude Code can run them through its Bash tool in the same session it does other work. Point Claude Code at this directory, let it install the commands, and it can run the pull and push for you from then on.

One thing does need a terminal, just once: interactive authentication. Claude Code's Bash tool runs a non-interactive shell, so it cannot answer a login or passphrase prompt. Do the one-time auth in a terminal yourself:

- `gh auth login` (browser or device-code flow), or
- add an SSH key to your agent and to GitHub, or
- enter the first HTTPS credential so your credential helper caches it.

After that, the credential is stored (keychain, SSH agent, or `gh`), the push becomes non-interactive, and Claude Code can run `claude-push` and `claude-pull` end to end. The case to avoid is a passphrase-protected SSH key with no agent loaded, or an uncached HTTPS login: either would stall a non-interactive run waiting for input. Get auth into a non-prompting state once, and the day-to-day stays inside Claude Code.

If Claude Code installs the commands and then cannot find `claude-push` in the same session, that is the shell-snapshot quirk described in the Appendix: the bare command has not been picked up yet. The scripts self-heal on the next run, or you can call the script by its full path, `~/.claude/claude-push.sh`, which always resolves.

## Rollback and revert

Because every machine holds the full shared history after a pull, you can undo a committed change from either machine:

- See history: `git -C ~/.claude log --oneline`
- Inspect a change: `git -C ~/.claude show <commit>`
- Undo one commit, keeping later work: `git -C ~/.claude revert <commit>`
- Restore one file to an earlier version: `git -C ~/.claude checkout <commit> -- path/to/file`

Then `claude-push` to send the revert to the other machine, which picks it up on its next `claude-pull`. The only change you cannot reach from the other machine is one you never committed or never pushed, so push when you finish.

## Appendix: Claude Code shell-snapshot hygiene (optional)

The bottom of each script has a short, clearly marked block you can delete if you do not want it. It exists because of one Claude Code quirk: Claude Code captures a snapshot of your shell once and replays it on every command it runs, instead of re-reading your shell profile each time. If you add a new command (like `claude-push`) and then ask Claude Code to run it in the same setup session, the cached snapshot may not know about it yet, and the command appears "not found."

The block fixes this in one idempotent step every time you push or pull: it re-creates the PATH symlinks for `claude-push` and `claude-pull` so they resolve as real files regardless of the snapshot. That does not touch your interactive terminal; it only makes the two commands findable. If you never run them through Claude Code, the block is harmless and you can remove it: delete from the "Optional" line down to the "end of optional block" line. The warning in the next paragraph sits above that block in both scripts, on purpose, so deleting the block leaves the warning in place.

**These scripts used to delete the snapshot as well, and that was removed on 2026-08-21 because it was actively harmful.** It read as routine housekeeping and it was not. Every Claude Code session already running re-reads its own snapshot file on *every* command it runs, so deleting the file strips those sessions of whatever your shell profile defined: functions, aliases, and in particular any safety wrapper you have put around `rm`. On the machine this was found on, that meant deletions inside a Claude Code session stopped going to the Trash and became permanent, silently, with nothing written to the log that was supposed to record them, and one file was lost that way.

It also bought nothing. Checked against Claude Code 2.1.238: a new session always writes a fresh snapshot from your current profile and never reads or reuses an existing one, so "the next session rebuilds it" was already true without deleting anything. Claude Code handles retention itself, removing each session's file when that session exits and sweeping strays on the `cleanupPeriodDays` schedule. And when the file is missing mid-session, Claude Code falls back to a login shell, which on zsh reads `.zshenv`, `.zprofile`, and `.zlogin` but not `.zshrc`, so the fallback does not reload a profile that lives in `.zshrc`. If you have copied an older version of these scripts, delete that line.

## What is tracked, and what is not

Tracked: your authored text. `CLAUDE.md`, `CLAUDE.local.md`, settings, keybindings, `skills/`, `scripts/`, `protocols/`, `changelog/`, `hooks/`, the two sync scripts, and per-project memory under `projects/*/memory/`.

Not tracked: everything else, by default. Session transcripts, caches, runtime state, downloaded plugins, and large binaries stay out. That keeps the repository small and free of noise, and it is why this is version control for your configuration, not a backup of your whole environment. Keep a separate full backup for recovery.
