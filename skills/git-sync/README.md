# Git Sync for Your Claude Code Environment

Version your `~/.claude` directory with Git, and keep two machines in sync through a private GitHub repository.

## What this is

A short recipe, not a skill you trigger. It turns the folder Claude Code keeps its configuration in (`~/.claude`: your `CLAUDE.md`, skills, memory, scripts, hooks, and settings) into a Git repository, and uses a private GitHub repository as the meeting point between your machines. You get version history, line-level diffs, one-command revert, and clean two-machine sync.

## Why bother

Your `~/.claude` directory is hand-built. You write a `CLAUDE.md`, add skills, tune settings, and accumulate memory over weeks. That is real authored work, and most people keep exactly one copy of it with no history.

Without version control:

- A bad edit to a skill or to `CLAUDE.md` is hard to undo precisely. You can retype the old text if you remember it, but there is no diff and no revert.
- You cannot see what changed between last week and today.
- Keeping a second machine in sync means copying files around by hand and hoping you copied the right ones in the right direction.

Plain file-sync (Dropbox, iCloud, Drive) does not solve this. Syncing a live `.git` folder through a file-sync client risks corrupting the repository, and file-sync gives you no commit history of the text you authored.

This recipe keeps `.git` local on each machine and pushes to a private GitHub repository. Git handles history and merges; GitHub is just the place the two machines meet.

## What you get

- History, diffs, and surgical revert on your skills, `CLAUDE.md`, scripts, hooks, and memory.
- Two-machine sync in two commands: pull when you sit down, push when you finish.
- An allowlist `.gitignore` that tracks only authored text and ignores caches, transcripts, and runtime folders by default, so nothing sensitive or noisy is committed by accident.

Two boundaries worth stating up front:

- This versions authored text, not large binaries or your content files. Office documents and the like are better left to ordinary backup.
- This is not a backup. A private repo on GitHub is a second copy, but you should still keep a separate full-environment backup.

## Let Claude Code set it up for you

The fastest path: point Claude Code at this directory and let it do the work.

Open Claude Code and say something like:

> Read `git-sync/setup.md` and set up Git sync for my `~/.claude` environment. Create the private GitHub repo, add the `.gitignore`, run the secret scan, make the first commit and push, and install the `claude-push` and `claude-pull` commands. Then tell me how to use them day to day.

Claude Code can run the whole recipe in your own environment: create the private repository (or walk you through `gh auth login` first), write the allowlist `.gitignore`, scan for secrets before the first commit, push the baseline, install the two commands on your PATH, and explain the daily routine. If you add a second machine later, point Claude Code at the same `setup.md` there and ask it to connect that machine to the existing repository.

The routine syncs run inside Claude Code too, not just the setup. `claude-push` and `claude-pull` are commands on your PATH, so Claude Code runs them through its Bash tool with no separate terminal. The one step that needs a terminal is the first-time authentication (`gh auth login`, an SSH key, or your first HTTPS credential), because Claude Code's shell cannot answer an interactive prompt. After that one-time step, the day-to-day pull and push stay inside Claude Code. See "Running it from inside Claude Code" in `setup.md`.

Prefer to do it yourself? `setup.md` has the full manual recipe.

## What is in this directory

- `setup.md`: the step-by-step recipe (install on one machine, add a second, daily use, rollback).
- `claude-push.sh`: commit your edits and push them to the private remote.
- `claude-pull.sh`: pull the other machine's latest edits before you start.
- `gitignore.sample`: the allowlist to copy to `~/.claude/.gitignore`; it tracks only authored text.

## Day to day

Once it is installed:

- `claude-pull` when you sit down at a machine, to get the other machine's latest edits.
- `claude-push "what you changed"` when you finish, to commit and send them.

On a single machine, `claude-push` on its own is a good commit-and-back-up-to-GitHub habit; you can ignore `claude-pull` until you add a second machine.

## Design rationale

**Why a private GitHub remote instead of syncing `.git` over a file-sync client?** A live `.git` directory is many small files that Git updates together. A file-sync client copying them mid-write can corrupt the repository. Pushing to a remote moves a consistent snapshot over Git's own protocol, which is exactly what Git is built for. The repository is private, so your configuration and memory are not public.

**Why `.git` stays local on each machine.** Each machine has its own `.git`. Nothing inside `.git` ever transits a file-sync folder, so there is no corruption risk. The machines exchange commits only through the remote.

**Why an allowlist `.gitignore`.** The default is to ignore everything, then re-include only the authored paths. Any new runtime folder, cache, or transcript directory Claude Code creates later is ignored automatically and cannot be committed by accident. You opt files in; you never have to remember to opt new noise out.

**Why merge, not rebase.** If you edit on two machines, their histories diverge. A merge keeps both lines of work and records the join. The scripts use `--no-rebase`, so an out-of-order push or a forgotten pull merges automatically when the edits do not overlap. If the same lines were changed on both machines, the sync stops and asks you to resolve the conflict, rather than rewriting history or guessing. There is one narrow exception, described in `setup.md`: when `settings.json` is the only conflicted file and the other machine changed nothing but a per-device toggle, the scripts keep this machine's copy and carry on. Anything else, including any key not on that list, still stops.

**Why this is not a backup.** Git gives you history and revert on authored text. It does not capture the binaries, caches, or content files the `.gitignore` excludes, and a single private repo is one copy. Keep a separate full backup of your environment for recovery.

## Installation

See `setup.md`. The short version: create a private GitHub repo, run `git init` in `~/.claude`, add the `.gitignore`, scan for secrets, make the first commit and push, then drop `claude-push.sh` and `claude-pull.sh` into `~/.claude` and symlink them onto your PATH.
