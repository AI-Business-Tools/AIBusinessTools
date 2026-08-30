# Setup: Git Sync for Your Claude Code Environment

This recipe turns `~/.claude` into a Git repository and connects it to a private GitHub repository, so you have version history and can keep two machines in sync. Read `README.md` first if you want the why; this file is the how.

You can run every step yourself, or you can let Claude Code run them for you.

## Let Claude Code do it

Open Claude Code in any project and say:

> Read `git-sync/setup.md` and set up Git sync for my `~/.claude` environment, then tell me how to use it.

Claude Code will create the private repository (or get you through `gh auth login` first), write the `.gitignore`, scan for secrets, make the first commit and push, install the `claude-push` and `claude-pull` commands, and explain the daily routine. The rest of this file is the same recipe written out, for doing it by hand or for following along while Claude Code works.

## Prerequisites

- Git installed (`git --version`).
- **A Git identity on this machine.** Git refuses to make any commit until it knows who you are, and this is where a first-time setup usually stalls, with "Please tell me who you are." Set it once, per machine:

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

  Check it with `git config --get user.name` and `git config --get user.email`. Any name and any address work; they are recorded in your commits, and this repository is private. `claude-push` and `claude-pull` check for both before they commit and stop with these two commands if either is missing.
- A GitHub account.
- One of: the GitHub CLI (`gh`), or an SSH key added to your GitHub account. The steps below use `gh` as the primary path and note the SSH alternative where it differs.
- Optional but recommended: `jq` (`brew install jq`, or `apt install jq`). The scripts use it to keep `settings.json` and `settings.local.json` from producing cosmetic merge conflicts. Without it they skip that handling and everything else still works. See "settings.json: why the scripts sort it."

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

Copy `gitignore.sample` from this directory to `~/.claude/.gitignore`. It is shipped under that name so it does not take effect inside the recipe's own folder; once copied to `~/.claude/.gitignore` it becomes active for your environment. It uses an allowlist: it ignores everything, then re-includes only the authored paths (`CLAUDE.md`, `CLAUDE.local.md`, `settings.json`, `settings.local.json`, `keybindings.json`, `.mcp.json`, `skills/`, `agents/`, `commands/`, `output-styles/`, `scripts/`, `protocols/`, `changelog/`, `hooks/`, the two sync scripts, and `projects/*/memory/`). Open it and add a line for any other root-level file you author and want tracked.

## Step 3: Scan for secrets before the first commit

Even though the repository is private, do not commit keys or tokens. Check what is about to be tracked:

```
cd ~/.claude
git add -A
git status                          # review the file list
git diff --cached | grep -nEi 'api[_-]?key|secret|token|password|bearer|-----BEGIN' || echo "No obvious secrets found."
```

The scan flags candidates to review, not certain secrets. It will also match documentation that merely mentions a word like "token" or "key," which is fine; look at each hit and decide. If anything sensitive shows up, add its path or pattern to `.gitignore`, then run `git rm --cached <path>` and re-check. The sample already excludes `.env`, `*.pem`, `id_rsa`, `id_ed25519`, and `.credentials.json` everywhere.

This is a one-time, deliberately broad scan. `claude-push` and `claude-pull` also run a narrow version of it on every sync, so a credential added months from now does not go out unnoticed. See "The credential check on every sync" below for what it looks for and what it deliberately does not.

## Step 4: First commit and push

```
cd ~/.claude
git add -A
git commit -m "Baseline: authored Claude Code environment"
```

The `git add -A` repeats Step 3 on purpose. It is harmless if nothing has changed since, and it means the commit still works if you stopped after Step 3 and came back later.

Add the remote and push. The CLI may have set the remote when you created the repo; if `git remote -v` shows nothing, add it:

```
git remote add origin https://github.com/USERNAME/claude-env.git    # or git@github.com:USERNAME/claude-env.git for SSH
git push -u origin main
```

Your environment now has a history and a private copy on GitHub.

## Step 5: Install the two commands

The `cp` below copies out of this recipe's own directory, so start by changing into it. Replace the path with wherever you downloaded or cloned this recipe:

```
cd /path/to/git-sync                # the folder holding claude-push.sh and claude-pull.sh
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

You have two clean options. Read the warning at the end of this step first if you set up a second machine using an earlier version of this recipe.

**Option A, fresh start (simplest).** If the second machine has nothing in `~/.claude` you need to keep, back up whatever is there, then clone:

```
mv ~/.claude ~/claude-backup-$(date +%Y%m%d-%H%M%S)     # only if ~/.claude already exists
git clone https://github.com/USERNAME/claude-env.git ~/.claude
```

Then repeat Step 5 on this machine to install the commands.

**Option B, keep the second machine's existing files.** The shape that is safe is to bring the shared repository down into a *new* folder, which already contains the first machine's files, copy this machine's files on top of it, look at what changed, and only then commit. Nothing in that sequence removes a file, so it cannot delete the first machine's work.

```
# 1. Back up this machine's folder, and keep the backup until you are satisfied.
cp -R ~/.claude ~/claude-backup-$(date +%Y%m%d-%H%M%S)

# 2. Clone the shared repository into a new folder. This does not touch ~/.claude.
git clone https://github.com/USERNAME/claude-env.git ~/claude-env-new

# 3. Copy this machine's files on top of the clone, leaving the clone's .git alone.
#    The trailing slash on the source path matters.
rsync -a --exclude '.git/' ~/.claude/ ~/claude-env-new/

# 4. Look at what this would commit, BEFORE committing anything.
cd ~/claude-env-new
git status                    # what this machine adds or changes
git ls-files --deleted        # must print nothing: anything here would be deleted
                              # from the other machine on its next pull
git diff                      # line by line, for files that exist on both machines

# 5. Only if step 4's middle command printed something, put those files back:
git ls-files --deleted -z | xargs -0 git checkout --

# 6. Commit and push.
git add -A
git commit -m "Add the second machine's local state"
git push origin main

# 7. Swap the folders once you are happy with what you pushed.
mv ~/.claude ~/claude-old-$(date +%Y%m%d-%H%M%S)
mv ~/claude-env-new ~/.claude
```

Then repeat Step 5 on this machine to install the commands, and delete the two backup folders once you have worked normally for a few days.

No `rsync`? Use `(cd ~/.claude && tar --exclude .git -cf - .) | (cd ~/claude-env-new && tar -xf -)` for step 3 instead. Do not use a plain `cp -R` of `~/.claude/.` into the clone: it would copy your old `.git` over the clone's and undo the whole point of the step.

Where the same file exists on both machines with different contents, this machine's copy becomes the new shared version, because step 3 copies over it. Step 4's `git diff` is where you see exactly that and decide. To keep the first machine's version of a particular file instead, run `git checkout HEAD -- path/to/file` in `~/claude-env-new` before you commit.

**Do not use `git reset --mixed origin/main` for this, and here is what it did.** Earlier versions of this recipe told you to run `git init`, `git fetch`, then `git reset --mixed origin/main` inside the second machine's existing `~/.claude`. That adopts the shared history while the folder on disk still holds only the second machine's files, so every file the first machine had and this one does not looks to git like a deletion you made. The next `git add -A` stages those deletions, the commit records them, and the first machine's next `claude-pull` removes them from its disk. Running the documented steps, a repository of 8 tracked files became 6, and three of the first machine's files were deleted with no warning at any point. The warning that used to sit under those steps only covered files present on *both* machines, which is not this case at all.

If you already ran it, nothing is lost: the deletion is a commit like any other, and the files are in the history.

```
git -C ~/.claude log --oneline --name-status --diff-filter=D    # find the commit and the deleted paths
git -C ~/.claude checkout <commit>^ -- path/to/file             # restore one file
```

Then `claude-push` to send the restored files back.

This is exactly the kind of step Claude Code can run for you: point it at this file on the second machine and ask it to connect the machine to your existing repository.

## Day-to-day use

- Sitting down at a machine: `claude-pull` to get the other machine's latest edits.
- Finishing up: `claude-push "short note about what changed"` to commit and send them. The message is optional; the script supplies a default if you omit it.

`claude-push` pulls before it pushes, so if you forgot to pull at the start, or pushed out of order from the other machine, non-conflicting edits merge automatically. If the same lines were changed on both machines, the sync stops and asks you to resolve the conflict by hand (see the next section). On a single machine, `claude-push` alone is a fine commit-and-back-up habit.

## If a sync stops on a conflict

A conflict happens only when the same lines of the same file were changed on both machines before they synced. Git cannot guess which version you want, so the sync stops and leaves both versions in the file, marked like this:

```
<<<<<<< HEAD
your version on this machine
=======
the version from the other machine
>>>>>>> origin/main
```

**Every conflict stops the sync and is resolved by hand.** The scripts never pick a winner for you, in any file, including `settings.json`. That is a deliberate limit: an automatic resolution keeps or discards a whole file, so it can only be as good as its guess about which whole file you wanted.

To resolve it, open each file the stop message named, delete the `<<<<<<<`, `=======`, and `>>>>>>>` marker lines along with the version you do not want, keep the text you do want (it can be a blend of both), then run:

```
git -C ~/.claude add -A
git -C ~/.claude commit --no-edit
```

Then run `claude-push` to send the resolved version. If you would rather see the two versions separately before you edit:

```
git -C ~/.claude show :2:path/to/file    # this machine's version
git -C ~/.claude show :3:path/to/file    # the other machine's version
```

To abandon the merge entirely and go back to where you were, `git -C ~/.claude merge --abort`.

Your committed work is never lost in a conflict: the scripts commit local edits before they pull, so resolving is always an edit and a commit, never a recovery. Claude Code can do this for you if you ask it to open the files and remove the markers.

**Do not just run the command again.** Re-running `claude-push` or `claude-pull` while the merge is still open used to be actively destructive: `git add -A` marked the conflicted files resolved exactly as they sat on disk, the commit sealed the merge, and the push published files still containing `<<<<<<<` lines, under the message "Pushed to origin/main." The other machine then pulled them. Both scripts now refuse to stage or commit anything while a merge is unfinished, and refuse to stage any file that still contains conflict markers. If you see either refusal, finish the resolve above; the message tells you the same thing with your own paths filled in.

## settings.json: why the scripts sort it

`settings.json` is the one file in `~/.claude` that both machines rewrite constantly without you editing it, and it is the usual source of a conflict you did not cause.

Claude Code rewrites it on nearly every session, and it does not preserve the order of the keys. Open the file after a week and the same settings sit in a different order. That means each machine commits a differently ordered copy of what is often identical content. Git compares text, not meaning, so when the two histories merge it sees a file whose lines changed everywhere on both sides, and it reports a whole-file conflict over nothing.

Both scripts run `settings.json` through `jq -S`, which sorts the keys alphabetically, before anything is staged for commit. Every commit from either machine then records the file in the same order, so git can compare the two sides key by key. When the machines changed different settings, the merge succeeds silently and both changes survive. `settings.local.json` gets the same treatment, for the same reason: it is tracked, so leaving it unsorted would just move the cosmetic conflicts to that file.

This only rewrites the order. No value is added, removed, or altered. It is skipped entirely when `jq` is not installed, and it is written so it cannot damage the file: it works on a temporary copy in the same folder, requires `jq` to parse the file and produce non-empty output before anything is replaced, keeps the file's permissions, and swaps in the result with a single atomic move. If any step fails, the temporary copy is discarded and your settings file is left exactly as it was.

One case is skipped on purpose: if `settings.json` or `settings.local.json` is a symbolic link to a file somewhere else, it is left alone. Git stores the link itself rather than the JSON behind it, so sorting that content would not affect a single merge, while replacing the link with a sorted regular file would quietly change what the path means and what its permissions are.

When both machines really did change the same setting to different values, that is a genuine conflict and it comes to you like any other, handled the way the previous section describes.

## The credential check on every sync

`settings.json` can hold an `env` block and an `apiKeyHelper`, and `hooks/` holds shell scripts. All of it is tracked, so a token pasted into one of them months after setup would otherwise go to GitHub on the next push with nothing said.

So before committing, both scripts look at the lines about to be committed, not at the whole repository, and stop if one contains something shaped like a live credential: the recognizable prefixes used by Anthropic, OpenAI, GitHub, Slack, AWS, and Google keys, and the opening line of a private key file. The list is deliberately short. A check that fires on ordinary prose gets switched off, and then it protects nothing.

It is not a guarantee. It knows a handful of well-known prefixes and will not recognize a bare password, a database URL with credentials in it, or a token format it has not been told about. The durable protection is what you keep out of tracked files in the first place: put secrets in your shell environment or a password manager and read them from there, rather than writing them into `settings.json`, a hook, or a script.

If it stops on something you have checked and know is an example rather than a live key, run the command once with the check off:

```
CLAUDE_SYNC_SKIP_SECRET_SCAN=1 claude-push
```

## When a sync stops for another reason

Every stop prints what to do, with your own paths filled in. The four you are most likely to see:

- **GitHub could not be reached.** No network, an expired or missing login, or a wrong remote URL. Your work is committed locally either way. Check `git -C ~/.claude remote -v`, then `gh auth status` or `ssh -T git@github.com`.
- **Git does not know who you are.** Set `user.name` and `user.email` as in the Prerequisites.
- **A line looks like a credential.** See the section above.
- **The push was refused.** Usually the other machine pushed a moment earlier. Run `claude-pull`, then `claude-push`.

One thing is a note rather than a stop: if the other machine force-added a file that this machine's `.gitignore` excludes, the pull overwrites this machine's copy without asking, because git treats an ignored file as expendable. `claude-pull` and `claude-push` print the paths when that happens, so at least you know. An ignored file is not committed on this machine, so its previous contents are usually only in your backup.

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

Tracked: your authored text. `CLAUDE.md`, `CLAUDE.local.md`, settings, keybindings, `.mcp.json`, `skills/`, `agents/`, `commands/`, `output-styles/`, `scripts/`, `protocols/`, `changelog/`, `hooks/`, the two sync scripts, and per-project memory under `projects/*/memory/`.

Not tracked: everything else, by default. Session transcripts, caches, runtime state, downloaded plugins, and large binaries stay out. That keeps the repository small and free of noise, and it is why this is version control for your configuration, not a backup of your whole environment. Keep a separate full backup for recovery.
