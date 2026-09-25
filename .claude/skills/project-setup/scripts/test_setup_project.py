"""Tests for setup_project.py. Run: python3 -m unittest discover -s <this dir>"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("setup_project.py")
README_T = "site: https://www.clearboxbuilds.com/builds/<PROJECT:REPO>\n# <PROJECT:NAME>\n\n<PROJECT:DESCRIPTION>\n"
OVERVIEW_T = "# <PROJECT:NAME>\n\n<PROJECT:DESCRIPTION>\n\n## Requirements\n"


class SetupProjectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "pantry-pal"
        (self.root / "ai").mkdir(parents=True)
        (self.root / "README.md").write_text("generic template readme\n")
        (self.root / "README.template.md").write_text(README_T)
        (self.root / "ai/plan-overview.template.md").write_text(OVERVIEW_T)

    def tearDown(self):
        self.tmp.cleanup()

    def git_init(self, origin=None):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        if origin:
            subprocess.run(["git", "remote", "add", "origin", origin], cwd=self.root, check=True)

    def run_setup(self, name="Pantry Pal", description="Tracks my pantry.", cwd=None):
        return subprocess.run([sys.executable, SCRIPT, "--name", name, "--description", description],
                              cwd=cwd or self.root, capture_output=True, text=True)

    def snapshot(self):
        return {p.relative_to(self.root): p.read_text() for p in self.root.rglob("*")
                if p.is_file() and ".git" not in p.parts}

    def test_fills_both_files_and_removes_templates(self):
        # The whole point of setup: real project files with no placeholders left, templates gone.
        self.git_init("https://github.com/clearboxbuilds/pantry-pal-app.git")
        r = self.run_setup()
        self.assertEqual(r.returncode, 0, r.stderr)
        readme = (self.root / "README.md").read_text()
        self.assertEqual(readme, "site: https://www.clearboxbuilds.com/builds/pantry-pal-app\n# Pantry Pal\n\nTracks my pantry.\n")
        self.assertEqual((self.root / "ai/plan-overview.md").read_text(), "# Pantry Pal\n\nTracks my pantry.\n\n## Requirements\n")
        self.assertFalse((self.root / "README.template.md").exists())
        self.assertFalse((self.root / "ai/plan-overview.template.md").exists())

    def test_removes_template_only_bin_tools(self):
        # bin/clearbox-new-project creates projects *from* the template; a new project has
        # no use for its own copy, so setup removes it (and bin/ if nothing else is in it).
        self.git_init("https://github.com/clearboxbuilds/pantry-pal.git")
        (self.root / "bin").mkdir()
        (self.root / "bin/clearbox-new-project").write_text("tool")
        (self.root / "bin/test_clearbox_new_project.py").write_text("tests")
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertFalse((self.root / "bin").exists())

    def test_keeps_bin_folder_when_it_has_other_files(self):
        # Only the template's own tools are removed; anything else in bin/ isn't ours to delete.
        self.git_init("https://github.com/clearboxbuilds/pantry-pal.git")
        (self.root / "bin").mkdir()
        (self.root / "bin/clearbox-new-project").write_text("tool")
        (self.root / "bin/my-script").write_text("mine")
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertFalse((self.root / "bin/clearbox-new-project").exists())
        self.assertEqual((self.root / "bin/my-script").read_text(), "mine")

    def test_setup_without_bin_folder_still_succeeds(self):
        # Projects created before bin/ existed (or with it already removed) must still set up.
        self.git_init("https://github.com/clearboxbuilds/pantry-pal.git")
        self.assertEqual(self.run_setup().returncode, 0)

    def test_repo_slug_is_bare_name_from_ssh_remote(self):
        # The website URL is /builds/<repo>, so the owner must be stripped and the remote
        # name (not the local folder name, which can differ) must win.
        self.git_init("git@github.com:clearboxbuilds/pantry-pal-app.git")
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertIn("/builds/pantry-pal-app\n", (self.root / "README.md").read_text())

    def test_no_remote_falls_back_to_repo_folder_name(self):
        # A fresh local repo has no origin yet; the folder name is the agreed fallback, and it
        # must be the repo root's name even when run from a subfolder.
        self.git_init()
        r = self.run_setup(cwd=self.root / "ai")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("/builds/pantry-pal\n", (self.root / "README.md").read_text())
        self.assertIn("no origin remote", r.stdout)

    def test_origin_still_pointing_at_template_fails_without_changes(self):
        # A folder copied from project-template keeps the template's .git, so origin says
        # "project-template". Using that name would point the website link at the template,
        # and the real fix is re-provisioning the repo, so setup must refuse rather than guess.
        self.git_init("https://github.com/clearboxbuilds/project-template.git")
        before = self.snapshot()
        r = self.run_setup()
        self.assertEqual(r.returncode, 1)
        self.assertIn("template repo", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_not_a_git_repo_fails_without_changes(self):
        before = self.snapshot()
        r = self.run_setup()
        self.assertEqual(r.returncode, 1)
        self.assertIn("not inside a git repository", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_rerun_after_setup_never_overwrites_the_humans_overview(self):
        # Once plan-overview.md exists the human has probably filled it in; losing it would be bad.
        self.git_init()
        (self.root / "ai/plan-overview.md").write_text("my requirements\n")
        before = self.snapshot()
        r = self.run_setup()
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_missing_template_fails_without_changes(self):
        self.git_init()
        (self.root / "README.template.md").unlink()
        before = self.snapshot()
        self.assertEqual(self.run_setup().returncode, 1)
        self.assertEqual(self.snapshot(), before)

    def test_description_is_inserted_verbatim(self):
        # Descriptions are free text; characters special to sed/regex/shell must survive untouched.
        self.git_init()
        desc = "Tracks food & drink / costs $0 — it's \\1 \"simple\".\nSecond line."
        self.assertEqual(self.run_setup(description=desc).returncode, 0)
        self.assertIn(desc, (self.root / "ai/plan-overview.md").read_text())

    def test_blank_name_or_description_is_rejected(self):
        # Both values are required; whitespace-only would produce an empty title or description.
        self.git_init()
        before = self.snapshot()
        self.assertEqual(self.run_setup(name="  ").returncode, 1)
        self.assertEqual(self.run_setup(description="").returncode, 1)
        self.assertEqual(self.snapshot(), before)

    def test_unknown_placeholder_fails_without_changes(self):
        # A new placeholder added to a template must not silently ship unfilled.
        self.git_init()
        (self.root / "README.template.md").write_text(README_T + "<PROJECT:EPISODE>\n")
        before = self.snapshot()
        r = self.run_setup()
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown", r.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
