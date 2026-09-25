"""Tests for clearbox-new-project. Run: python3 -m unittest discover -s bin -p 'test_*.py'

The real `gh` talks to GitHub, so these tests put a fake `gh` first on PATH. The fake logs
every call it receives and simulates `repo create` and `repo clone`. Each test runs a copy
of the script inside a throwaway "project-template" folder, so new projects land in a
throwaway parent folder and never touch the real one.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("clearbox-new-project")

# The fake gh. Behaviour is controlled by environment variables:
#   FAKE_GH_LOG          file to append each call's arguments to (one JSON list per line)
#   FAKE_GH_CREATE_EXIT  exit code for `gh repo create` (default 0)
#   FAKE_GH_EMPTY_CLONES how many clones should come back empty before one has a commit
FAKE_GH = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, subprocess, sys
    from pathlib import Path
    args = sys.argv[1:]
    log = Path(os.environ["FAKE_GH_LOG"])
    previous = log.read_text().splitlines() if log.exists() else []
    with log.open("a") as f:
        f.write(json.dumps(args) + "\\n")
    if args[:2] == ["repo", "create"]:
        sys.exit(int(os.environ.get("FAKE_GH_CREATE_EXIT", "0")))
    if args[:2] == ["repo", "clone"]:
        target = Path(args[3])
        earlier_clones = sum(1 for line in previous if json.loads(line)[:2] == ["repo", "clone"])
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        if earlier_clones >= int(os.environ.get("FAKE_GH_EMPTY_CLONES", "0")):
            (target / "README.template.md").write_text("template")
            subprocess.run(["git", "-C", str(target), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(target), "-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-qm", "init"], check=True)
""")

# The fake claude. Records its arguments and the folder it was started in, as JSON, to
# FAKE_CLAUDE_LOG, so tests can check the session is launched in the new project.
FAKE_CLAUDE = textwrap.dedent("""\
    #!/usr/bin/env python3
    import json, os, sys
    with open(os.environ["FAKE_CLAUDE_LOG"], "w") as f:
        json.dump({"args": sys.argv[1:], "cwd": os.getcwd()}, f)
""")


class NewProjectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # resolve(): on macOS the temp dir is under a symlink (/var -> /private/var), and the
        # script resolves its own location, so compare against the resolved path.
        self.parent = Path(self.tmp.name).resolve() / "clearboxbuilds"
        # A throwaway template folder with the script in bin/ and an origin remote.
        self.template = self.parent / "project-template"
        (self.template / "bin").mkdir(parents=True)
        shutil.copy(SCRIPT, self.template / "bin/clearbox-new-project")
        subprocess.run(["git", "init", "-q"], cwd=self.template, check=True)
        subprocess.run(["git", "remote", "add", "origin", "git@github.com:clearboxbuilds/project-template.git"],
                       cwd=self.template, check=True)
        # The fake gh, first on PATH.
        fake_bin = Path(self.tmp.name) / "fakebin"
        fake_bin.mkdir()
        (fake_bin / "gh").write_text(FAKE_GH)
        (fake_bin / "gh").chmod(0o755)
        (fake_bin / "claude").write_text(FAKE_CLAUDE)
        (fake_bin / "claude").chmod(0o755)
        self.fake_bin = fake_bin
        self.log = Path(self.tmp.name) / "gh.log"
        self.claude_log = Path(self.tmp.name) / "claude.json"
        self.env = {**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                    "FAKE_GH_LOG": str(self.log), "FAKE_CLAUDE_LOG": str(self.claude_log)}

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args, **env):
        # Run from an unrelated folder to prove the output location doesn't depend on the cwd.
        return subprocess.run([sys.executable, self.template / "bin/clearbox-new-project", *args],
                              cwd=self.tmp.name, env={**self.env, **env}, capture_output=True, text=True)

    def gh_calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_creates_from_template_and_clones_into_sibling_folder(self):
        # The whole point: a fresh GitHub repo made from the template (same owner), cloned
        # next to project-template, so it gets its own history and the right origin.
        r = self.run_script("--name", "pantry-pal")
        self.assertEqual(r.returncode, 0, r.stderr)
        target = self.parent / "pantry-pal"
        self.assertEqual(self.gh_calls(), [
            ["repo", "create", "clearboxbuilds/pantry-pal", "--template", "clearboxbuilds/project-template", "--private"],
            ["repo", "clone", "clearboxbuilds/pantry-pal", str(target)],
        ])
        self.assertTrue((target / "README.template.md").exists())

    def test_launches_named_claude_session_in_new_project_asking_for_setup(self):
        # The next step after cloning is always project-setup, run from inside the new
        # project. The session is named so it's easy to find among other Claude sessions.
        self.assertEqual(self.run_script("--name", "pantry-pal").returncode, 0)
        launched = json.loads(self.claude_log.read_text())
        self.assertEqual(launched["args"], ["-n", "Clearbox: pantry-pal", "set up this project"])
        self.assertEqual(launched["cwd"], str(self.parent / "pantry-pal"))

    def test_missing_claude_still_succeeds_with_next_steps(self):
        # By this point the repo exists on GitHub and locally, so a missing `claude` must not
        # report failure; it should print the manual next steps instead.
        only_gh = Path(self.tmp.name) / "only_gh"
        only_gh.mkdir()
        (only_gh / "gh").symlink_to(self.fake_bin / "gh")
        (only_gh / "git").symlink_to(shutil.which("git"))
        (only_gh / "python3").symlink_to(sys.executable)  # the fake gh runs via `env python3`
        r = self.run_script("--name", "pantry-pal", PATH=str(only_gh))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("cd ", r.stdout)
        self.assertFalse(self.claude_log.exists())

    def test_public_flag_makes_public_repo(self):
        # Private is the default because it's the reversible choice; --public must opt in.
        self.assertEqual(self.run_script("--name", "pantry-pal", "--public").returncode, 0)
        self.assertIn("--public", self.gh_calls()[0])
        self.assertNotIn("--private", self.gh_calls()[0])

    def test_retries_clone_until_github_has_filled_the_repo(self):
        # GitHub fills template repos asynchronously; an early clone is empty and must not be
        # accepted as the project (it would have no template files for project-setup to use).
        r = self.run_script("--name", "pantry-pal", FAKE_GH_EMPTY_CLONES="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([c[:2] for c in self.gh_calls()].count(["repo", "clone"]), 2)
        self.assertTrue((self.parent / "pantry-pal/README.template.md").exists())

    def test_existing_folder_is_never_touched_and_nothing_is_created(self):
        # Never overwrite local work, and check before creating anything on GitHub.
        (self.parent / "pantry-pal").mkdir()
        (self.parent / "pantry-pal/notes.txt").write_text("mine")
        r = self.run_script("--name", "pantry-pal")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)
        self.assertEqual(self.gh_calls(), [])
        self.assertEqual((self.parent / "pantry-pal/notes.txt").read_text(), "mine")
        self.assertFalse(self.claude_log.exists())

    def test_invalid_or_template_name_rejected_before_calling_github(self):
        # Bad names would fail on GitHub or, for the template's own name, recreate the problem
        # this script exists to avoid; either way nothing should be created.
        for bad in ("my project", "../escape", "project-template"):
            r = self.run_script("--name", bad)
            self.assertEqual(r.returncode, 1, bad)
        self.assertEqual(self.gh_calls(), [])

    def test_create_failure_stops_before_cloning(self):
        # If GitHub refused (e.g. the repo name is taken), there's nothing to clone.
        r = self.run_script("--name", "pantry-pal", FAKE_GH_CREATE_EXIT="1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("nothing was created", r.stderr)
        self.assertEqual(len(self.gh_calls()), 1)
        self.assertFalse((self.parent / "pantry-pal").exists())


if __name__ == "__main__":
    unittest.main()
