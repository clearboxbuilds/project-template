#!/usr/bin/env python3
"""Fill in a Clearbox Builds project from its templates.

Usage: setup_project.py --name "Project Name" --description "Project description"

Run from anywhere inside the project's git repo. Every check runs before any
file is touched, so a failure leaves the repo exactly as it was.
Exit code 0 on success, 1 on failure (reason printed to stderr).
"""
import argparse
import subprocess
import sys
from pathlib import Path

# (template, target) pairs, relative to the repo root.
FILES = [
    ("README.template.md", "README.md"),
    ("ai/plan-overview.template.md", "ai/plan-overview.md"),
]
# Targets that must not already exist. README.md is expected to exist and gets overwritten.
MUST_NOT_EXIST = ["ai/plan-overview.md"]
# Tools that only make sense inside project-template itself (they create new projects from it).
# Setup removes them from the new project, then removes bin/ too if nothing else is left in it.
TEMPLATE_ONLY_FILES = ["bin/clearbox-new-project", "bin/test_clearbox_new_project.py"]
# Name of the template repo itself. If the repo name resolves to this, the folder was copied
# from the template (keeping its .git) instead of created from it, so the name is wrong.
TEMPLATE_REPO = "project-template"


def fail(msg):
    print(f"FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def repo_slug(root):
    """Repo name from the origin remote (https or ssh form), else the repo folder name."""
    url = git("remote", "get-url", "origin", cwd=root)
    if url:
        name = url.rstrip("/").split("/")[-1].split(":")[-1]
        name = name[:-4] if name.endswith(".git") else name
        if name:
            return name, "origin remote"
    return Path(root).name, "repo folder name (no origin remote)"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--description", required=True)
    args = p.parse_args()
    name, description = args.name.strip(), args.description.strip()
    if not name or not description:
        fail("project name and description must both be non-empty.")

    root = git("rev-parse", "--show-toplevel", cwd=Path.cwd())
    if not root:
        fail(f"{Path.cwd()} is not inside a git repository.")
    root = Path(root)

    missing = [t for t, _ in FILES if not (root / t).is_file()]
    if missing:
        fail(f"template(s) not found: {', '.join(missing)}. Has setup already run?")
    existing = [t for t in MUST_NOT_EXIST if (root / t).exists()]
    if existing:
        fail(f"{', '.join(existing)} already exists. Has setup already run?")

    slug, source = repo_slug(root)
    # Refuse rather than guess: a copied folder also carries the template's history and would
    # push to the template repo, so the fix is re-provisioning, not picking a different name.
    if slug == TEMPLATE_REPO:
        fail(f"this folder is still linked to the template repo (repo name '{slug}' from {source}). "
             "Create the project with `bin/clearbox-new-project --name <name>` from the project-template "
             "folder (or fix the git remote), then run setup again.")
    values = {"<PROJECT:REPO>": slug, "<PROJECT:NAME>": name, "<PROJECT:DESCRIPTION>": description}

    rendered = {}
    for template, target in FILES:
        text = (root / template).read_text()
        for placeholder, value in values.items():
            text = text.replace(placeholder, value)
        if "<PROJECT:" in text:
            fail(f"{template} contains an unknown <PROJECT:...> placeholder; nothing was changed.")
        rendered[target] = text

    # Write every target before deleting any template, so an interrupted run never loses a template.
    for target, text in rendered.items():
        (root / target).write_text(text)
    for template, _ in FILES:
        (root / template).unlink()

    # Remove the template-only tools. Missing ones are fine (older projects never had them).
    removed = [f for f in TEMPLATE_ONLY_FILES if (root / f).is_file()]
    for f in removed:
        (root / f).unlink()
    bin_dir = root / "bin"
    if bin_dir.is_dir() and not any(bin_dir.iterdir()):
        bin_dir.rmdir()

    print(f"repo: {slug} (from {source})")
    for template, target in FILES:
        print(f"{template} -> {target}")
    for f in removed:
        print(f"removed {f} (template-only tool)")


if __name__ == "__main__":
    main()
