# zzCopilotAgents

Six focused GitHub Copilot custom agents, a parent delegation contract, and
fail-closed implementer lifecycle hooks. Agent profiles need no MCP server or
local model service. The hooks require Python 3.10 or newer.

## Included agents

| Agent | Purpose | Writes files |
|---|---|---|
| `zz-readagent` | Focused repository research | no |
| `zz-brainstormer` | Solution options and tradeoffs | no |
| `zz-designplanner` | Implementation-ready designs | no |
| `zz-debugger` | Evidence-based diagnosis | no |
| `zz-implementer` | One bounded implementation piece | **yes** |
| `zz-vetter` | Independent adversarial review | no |

Repository policy lives in `AGENTS.md` and
`.github/copilot-instructions.md`. The files contain the same marked delegation
contract. `.github/hooks/zz-implementer.json` protects implementation documents
and append-only ledgers, checks status and confidence consistency, and permits
only one implementer at a time.

All agents use Copilot's native repository tools. Profiles do not pin a model;
use `/model` and `/subagents` in Copilot CLI to configure model selection.

## Requirements

- GitHub Copilot CLI or Copilot cloud agent with custom agents and repository
  hooks enabled
- Python 3.10 or newer (`python3` on Linux/macOS or `python` on Windows)

## Install

Copy the contents of this repository's `.github/` directory into your
repository's `.github/` directory, then restart Copilot.

## Test

Test the source package:

```sh
python3 -m unittest discover -s tests/agents -p 'test_*.py'
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

## Workflow rules

- The parent owns decomposition, sequencing, integration, final verification,
  and all git operations.
- Use `zz-brainstormer` before design when multiple approaches have meaningful
  tradeoffs, then explicitly select one.
- Use `zz-designplanner` for non-trivial selected approaches.
- Give `zz-implementer` one bounded piece from an implementation document under
  `docs/artifacts/implementationdocs/`.
- Review important artifacts with three independent `zz-vetter` lenses:
  research grounding, live-tree feasibility, and consistency/severity.

The implementer hook snapshots implementation documents and ledgers outside the
repository. It rejects changed implementation documents, malformed or
non-append-only ledgers, invalid run ordinals or progress records, inconsistent
status/confidence, and overlapping implementer runs. These checks enforce
workflow structure; they do not replace review or create a security boundary
against hostile processes running as the same OS user.

See [docs/copilot-native-agents.md](docs/copilot-native-agents.md) for the
design and full enforcement model.
