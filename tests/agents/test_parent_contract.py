import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
START = "<!-- zz-copilot-agents:start -->"
END = "<!-- zz-copilot-agents:end -->"


def marked_contract(path):
    text = path.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise AssertionError(f"{path} must contain exactly one marked contract")
    start = text.index(START)
    end = text.index(END, start) + len(END)
    return text[start:end]


def normalized(text):
    return " ".join(text.split())


class ParentContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = marked_contract(REPO_ROOT / "AGENTS.md")
        self.normalized_contract = normalized(self.contract)

    def test_agents_and_copilot_instructions_share_parent_contract(self):
        copilot_contract = marked_contract(
            REPO_ROOT / ".github" / "copilot-instructions.md"
        )
        self.assertEqual(copilot_contract, self.contract)

    def test_parent_can_edit_but_only_implementer_is_write_capable_delegate(self):
        for authority in (
            "parent handles",
            "may write files directly",
            "small, localized, low-risk changes",
            "focused follow-up fixes from vetter",
            "sole write-capable delegated specialist",
            "not the sole writer including the parent",
            "implementation-document and ledger ceremony",
        ):
            self.assertIn(authority, self.normalized_contract)

        self.assertNotIn(
            "zz-implementer is the only agent that edits files",
            self.contract,
        )
        self.assertNotIn("Only `zz-implementer` may write files", self.contract)

    def test_read_only_roles_and_parent_ownership_are_preserved(self):
        read_only_rule = (
            "`zz-readagent`, `zz-brainstormer`, `zz-designplanner`, "
            "`zz-debugger`, and `zz-vetter` remain read-only"
        )
        self.assertIn(read_only_rule, self.normalized_contract)
        self.assertIn(
            "The parent owns decomposition, sequencing, review, integration, "
            "final verification, and **all git operations**",
            self.normalized_contract,
        )

    def test_parent_requires_user_approval_for_material_scope_expansion(self):
        for boundary in (
            "original user ask is the scope baseline",
            "Small, directly coupled correctness changes may remain in scope",
            "behavior or features",
            "affected subsystems",
            "dependencies",
            "migrations",
            "risk",
            "delivery effort",
            "user's clarification or permission before proceeding",
            "ask when the boundary is ambiguous",
        ):
            self.assertIn(boundary, self.normalized_contract)

    def test_delegated_scope_boundary_rule_applies_only_to_implementer(self):
        shared_rules = self.normalized_contract.split(
            "### Shared constraints", 1
        )[1]
        for invariant in (
            "`zz-implementer`",
            "stops and escalates",
            "material boundary",
            "original ask",
        ):
            self.assertIn(invariant, shared_rules)
        self.assertNotIn(
            "Every delegated agent stops and escalates",
            shared_rules,
        )

    def test_implementer_profile_blocks_at_new_material_scope(self):
        profile = (
            REPO_ROOT / ".github" / "agents" / "zz-implementer.agent.md"
        ).read_text(encoding="utf-8")
        normalized_profile = normalized(profile)
        scope_guard = normalized_profile.split(
            "The original user ask remains the scope baseline", 1
        )[1].split("## Working loop", 1)[0]
        for boundary in (
            "Original user ask and scope baseline",
            "continually be checked",
            "Small, directly coupled correctness changes",
            "materially expand",
            "affected subsystems",
            "dependencies",
            "migrations",
            "risk",
            "delivery effort",
            "parent to take to the user",
            "User clarification or permission",
        ):
            self.assertIn(boundary, normalized_profile)
        for blocked_invariant in (
            "materially expand",
            "record confidence below 80%",
            "return `blocked`",
            "needed clarification",
        ):
            self.assertIn(blocked_invariant, scope_guard)

        clarifications_rule = normalized_profile.split(
            "## Clarifications needed", 1
        )[1].split("## Escalations", 1)[0]
        self.assertIn("Required when confidence < 80%", clarifications_rule)
        self.assertIn("Omit above 80%", clarifications_rule)
        self.assertNotIn("material or ambiguous", clarifications_rule)


if __name__ == "__main__":
    unittest.main()
