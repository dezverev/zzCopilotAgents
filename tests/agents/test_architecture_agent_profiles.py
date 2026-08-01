import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = REPO_ROOT / ".github" / "agents"


class ArchitectureAgentProfileTest(unittest.TestCase):
    def test_brainstormer_is_reserved_for_architecture_decisions(self):
        text = (AGENT_ROOT / "zz-brainstormer.agent.md").read_text(
            encoding="utf-8"
        )
        for boundary in (
            "principal-level",
            "architecture-level",
            "implementation-step decisions",
            "small updates to an existing design",
            "overall redesign",
            "## Out of scope",
        ):
            self.assertIn(boundary, text)

    def test_designplanner_is_reserved_for_sdd_style_design(self):
        text = (AGENT_ROOT / "zz-designplanner.agent.md").read_text(
            encoding="utf-8"
        )
        for boundary in (
            "SDD-style",
            "implementation-step",
            "small design-document correction",
            "overall redesign",
            "## Out of scope",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
