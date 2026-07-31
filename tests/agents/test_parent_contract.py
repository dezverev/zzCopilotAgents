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


class ParentContractTest(unittest.TestCase):
    def test_agents_and_copilot_instructions_share_parent_contract(self):
        agents_contract = marked_contract(REPO_ROOT / "AGENTS.md")
        copilot_contract = marked_contract(
            REPO_ROOT / ".github" / "copilot-instructions.md"
        )
        self.assertEqual(copilot_contract, agents_contract)


if __name__ == "__main__":
    unittest.main()
