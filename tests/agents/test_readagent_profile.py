import ast
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = REPO_ROOT / ".github" / "agents" / "zz-readagent.agent.md"


def load_profile():
    text = PROFILE_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    if match is None:
        raise AssertionError("profile must have a delimited frontmatter block")

    frontmatter_text, prompt = match.groups()
    frontmatter = {}
    for line in frontmatter_text.splitlines():
        field = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if field:
            frontmatter[field.group(1)] = (field.group(2) or "").strip()
    return frontmatter, frontmatter_text, prompt


class ReadagentProfileContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontmatter, cls.frontmatter_text, cls.prompt = load_profile()
        cls.full_text = PROFILE_PATH.read_text(encoding="utf-8")

    def test_frontmatter_uses_portable_native_contract(self):
        self.assertEqual("zz-readagent", self.frontmatter["name"])
        self.assertEqual(["read", "search"], ast.literal_eval(self.frontmatter["tools"]))
        self.assertNotIn("model", self.frontmatter)

    def test_description_separates_specialist_ownership(self):
        description = self.frontmatter_text.lower()
        self.assertIn("isolated-context factual scout", description)
        self.assertIn("read-planning", description)
        for owner in ("zz-debugger", "zz-vetter", "zz-brainstormer", "zz-designplanner"):
            self.assertIn(owner, description)

    def test_dispatch_contract_has_one_required_question_and_optional_hints(self):
        self.assertIn("Only `Question:` is required", self.prompt)
        self.assertIn("bounded exploration", self.prompt)
        self.assertIn("knowledge ambiguity", self.prompt)
        self.assertIn("exact files and ranges", self.prompt)
        for field in (
            "Question:",
            "Paths:",
            "Symbols:",
            "Search terms:",
            "Line ranges:",
            "Output:",
        ):
            self.assertIn(field, self.prompt)
        self.assertIn("optional output scope", self.prompt)

    def test_report_contract_has_required_order_and_optional_sections(self):
        required = [
            "## Answer",
            "## Subsystem map",
            "## Focused read list",
            "## Anchors",
        ]
        positions = [self.prompt.index(heading) for heading in required]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("`## Answer` must be first", self.prompt)
        self.assertIn("are always required", self.prompt)
        for heading in ("## Avoid for now", "## Uncertainty", "## Out of scope"):
            self.assertIn(heading, self.prompt)
        self.assertIn("refusal-only `## Out of scope`", self.prompt)
        self.assertIn("primary handoff", self.prompt)
        self.assertIn("order them in the sequence the parent should", self.prompt)
        self.assertIn("state what each range establishes", self.prompt)
        self.assertIn("## Avoid for now", self.prompt)

    def test_citation_and_evidence_rules_are_explicit(self):
        self.assertRegex(
            self.prompt,
            r"every repository factual claim.*repository-relative citation",
        )
        self.assertIn("path:line", self.prompt)
        self.assertIn("path:start-end", self.prompt)
        self.assertIn("do not stop at the first matching file", self.prompt)
        for forbidden_output in (
            "invented citations",
            "whole-file dumps",
            "raw tool output",
            "speculative findings",
            "patches",
            "implementation advice",
        ):
            self.assertIn(forbidden_output, self.prompt)

    def test_specialist_judgments_are_refused(self):
        for boundary in (
            "correctness or safety judgments",
            "code review",
            "bug hunting",
            "root-cause diagnosis",
            "design selection",
            "recommendations about what to change",
            "edit or refactor strategy",
            "implementation planning",
        ):
            self.assertIn(boundary, self.prompt)
        self.assertIn("neutral inspected facts and locations", self.prompt)
        self.assertIn("Explicitly refuse requests for:", self.prompt)

    def test_no_mutating_or_external_runtime_capability(self):
        boundary_text = " ".join(self.prompt.lower().split())
        for boundary in (
            "never execute commands",
            "edit files",
            "mutate the filesystem",
            "git operations",
            "mcp",
            "qwen",
            "local-model service",
            "fixed model",
            "external runtime",
        ):
            self.assertIn(boundary, boundary_text)
        self.assertEqual({"name", "description", "tools"}, set(self.frontmatter))


if __name__ == "__main__":
    unittest.main()
