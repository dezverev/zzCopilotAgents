import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"


class ReadmeInstallationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = README_PATH.read_text(encoding="utf-8")
        cls.install = cls.text.split("## Install\n", 1)[1].split(
            "## Contributor verification\n", 1
        )[0]
        cls.install_prose = " ".join(cls.install.split())

    def test_platform_preflights_check_supported_python_before_copying(self):
        linux_check = (
            'python3 -c "import sys; raise SystemExit('
            '0 if sys.version_info >= (3, 10) else 1)"'
        )
        windows_check = (
            'python -c "import sys; raise SystemExit('
            '0 if sys.version_info >= (3, 10) else 1)"'
        )
        copy_position = self.install.index("### 2. Copy the runtime files")
        for check in (linux_check, windows_check):
            self.assertIn(check, self.install)
            self.assertLess(self.install.index(check), copy_position)

    def test_failed_preflight_blocks_installation_with_actionable_guidance(self):
        for guidance in (
            "Do not proceed",
            "install Python 3.10 or newer",
            "python.org",
            "package manager",
            "on `PATH`",
            "rerun the check",
        ):
            self.assertIn(guidance, self.install_prose)

    def test_consumer_payload_excludes_development_assets(self):
        for runtime_content in (
            "agent profiles",
            "hook configuration and scripts",
            "repository guidance",
        ):
            self.assertIn(runtime_content, self.install_prose)
        self.assertIn("development assets", self.install_prose)
        self.assertIn(
            "neither copy them nor run the repository tests", self.install_prose
        )
        self.assertNotIn("unittest discover", self.install)

    def test_tests_are_preserved_as_contributor_only_verification(self):
        contributor_section = self.text.split(
            "## Contributor verification\n", 1
        )[1].split("## Workflow rules\n", 1)[0]
        self.assertIn("for contributors", contributor_section)
        self.assertIn("End users do not copy or", contributor_section)
        self.assertIn("tests/agents", contributor_section)
        self.assertIn("tests/hooks", contributor_section)

    def test_copilot_assisted_install_has_the_same_boundaries(self):
        alternative = self.install.split("Alternatively, give Copilot", 1)[1]
        self.assertIn("verify Python 3.10 or newer", alternative)
        self.assertIn("stop", alternative)
        self.assertIn("install only", alternative)
        self.assertIn("runtime files from `.github/`", alternative)


if __name__ == "__main__":
    unittest.main()
