---
name: project-setup
description: Set up a new Clearbox Builds project from the project template — check the folder is a git repo, get the project name and description, and turn README.template.md and ai/plan-overview.template.md into README.md and ai/plan-overview.md with the repo name, project name, and description filled in. Use this whenever the user wants to set up, initialize, bootstrap, or name a new project created from the template — e.g. "set up this project", "let's set up the new build, it's called X", "initialize the repo from the template", "fill in the project name and description" — even if they don't say "setup" explicitly.
---

# Project Setup

A new Clearbox Builds repo starts as a copy of the project template. Setup turns the template files into the real project files:

| Template | Becomes | Placeholders filled |
|---|---|---|
| `README.template.md` | `README.md` (overwriting the template's generic README) | `<PROJECT:REPO>`, `<PROJECT:NAME>`, `<PROJECT:DESCRIPTION>` |
| `ai/plan-overview.template.md` | `ai/plan-overview.md` | same |

`<PROJECT:REPO>` is the repo name (e.g. `pantry-pal`, not `clearboxbuilds/pantry-pal`). It builds the project's URL at `clearboxbuilds.com/builds/<repo>`.

## Step 1: Check it's a git repo

Run `git rev-parse --show-toplevel`. If it fails, stop and tell the user that setup has to run inside the project's git repository. Don't `git init` for them. A project that isn't a repo probably wasn't created from the template the usual way, and they should know that.

(The script in step 3 checks this again, and also works out the repo name.)

## Step 2: Get a clear project name and description

Both are required. Don't proceed until you have both.

Look for them in the user's message first. Users rarely label them, so read for intent: "set up Pantry Pal, it's a little app that tracks my pantry and suggests recipes" gives you both. Then:

- **Both clear** → go ahead.
- **One missing or ambiguous** → ask only for what's missing, and repeat back what you did get so the user can correct it. For example: "Name: *Pantry Pal*. What's the one- or two-sentence description?"
- **Neither given** → ask for both in one message.

"Unclear" means you'd be guessing. Examples: two candidate names, a description that's only a few words ("an app"), or a request like "call it whatever" (ask them to pick; the name goes in public places). Use the user's own wording for the description. Tidy grammar or capitalization if needed, but don't add claims or marketing copy. It's their project, and it appears on the website and in the planning doc.

If you had to ask, confirm the final values in one line before running the script.

## Step 3: Run the setup script

```bash
python3 <this-skill-dir>/scripts/setup_project.py --name "<Project Name>" --description "<Project description>"
```

Run it from inside the repo. It does all the file work, so the result is identical every time:

- finds the repo root and gets the repo name from the `origin` remote (falling back to the repo folder name if there's no remote)
- refuses if the repo name comes out as `project-template`. That means the folder was copied from the template (and still has the template's git history and remote) instead of created from it with `bin/clearbox-new-project`. Don't work around this by passing a different name: the repo itself needs re-provisioning, or its next push would go to the template.
- checks that both templates exist and that `ai/plan-overview.md` doesn't exist yet; if either check fails, setup has probably already run
- fills in the placeholders and writes `README.md` and `ai/plan-overview.md`
- deletes the two template files, plus the template-only tools in `bin/` (`clearbox-new-project` and its tests, which only make sense inside project-template); `bin/` itself goes too if nothing else is in it

All checks run before any file changes, so if it fails (exit code 1, with the reason on stderr), nothing has been modified. Report the reason to the user as-is, and don't try to work around it by editing files by hand. If a template is missing or `plan-overview.md` already exists, the project has probably been set up already, and hand-editing would overwrite the user's work.

Pass the values through the script's arguments, not by editing files yourself. Quote them properly for the shell: descriptions often contain apostrophes, `&`, or `$`.

## Step 4: Report

Tell the user:
- the repo name that was used and where it came from (the script prints this). If it came from the folder name because there's no remote, say so, since the website URL depends on it.
- the files that were created, and that the templates were removed.
- the next step: fill in **Requirements** and **Outstanding questions and decisions** in `ai/plan-overview.md`, then start planning.

Don't commit. The user decides when to commit.
