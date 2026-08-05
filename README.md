# zzCopilotAgents

Six focused GitHub Copilot custom agents, a parent delegation contract, and
fail-closed implementer lifecycle hooks. Agent profiles need no MCP server or
local model service. The hooks require Python 3.10 or newer.

## Included agents

| Agent | Purpose | Writes files |
|---|---|---|
| `zz-readagent` | Initial repository exploration and cited read plans | no |
| `zz-brainstormer` | Principal-level architecture options | no |
| `zz-designplanner` | SDD-style architecture designs | no |
| `zz-debugger` | Evidence-based diagnosis | no |
| `zz-implementer` | One bounded implementation piece | **yes** |
| `zz-vetter` | Independent adversarial review | no |

The brainstormer/designplanner prompts still need tuning. Sometimes they trigger a bit much and overscope. In my Pi setup I have their inclusion on a toggle. 

Repository policy lives in `AGENTS.md` and
`.github/copilot-instructions.md`. The files contain the same marked delegation
contract. `.github/hooks/zz-implementer.json` protects implementation documents
and append-only ledgers, requires one delimited run record, and permits only one
implementer at a time.

All agents use Copilot's native repository tools. Profiles do not pin a model;
use `/model` and `/subagents` in Copilot CLI to configure model selection.

## Requirements

- GitHub Copilot CLI or Copilot cloud agent with custom agents and repository
  hooks enabled
- Python 3.10 or newer (`python3` on Linux/macOS or `python` on Windows)

## Install

### 1. Verify the hook runtime

On Linux or macOS, run:

```sh
python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
```

On Windows, run in PowerShell:

```powershell
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
```

Do not proceed unless the command for your platform is found and exits
successfully. If it is missing or fails, install Python 3.10 or newer from
[python.org](https://www.python.org/downloads/) or your platform's package
manager, ensure `python3` (Linux/macOS) or `python` (Windows) is on `PATH`,
restart your shell, and rerun the check.

### 2. Copy the runtime files

After the check succeeds, copy the required contents of this repository's
`.github/` directory into your repository's `.github/` directory, then restart
Copilot. This runtime payload consists of the agent profiles, hook
configuration and scripts, and repository guidance under `.github/`. Project
development assets such as `tests/` and `docs/` are not part of installation;
end users should neither copy them nor run the repository tests to install the
agents.

Alternatively, give Copilot the
[repository URL](https://github.com/dezverev/zzCopilotAgents) and ask it to
verify Python 3.10 or newer with the platform-appropriate command above, stop
and provide install or `PATH` guidance if verification fails, and install only
the required runtime files from `.github/`.

## Contributor verification

These source-repository tests are for contributors. End users do not copy or
run them as part of installation.

```sh
python3 -m unittest discover -s tests/agents -p 'test_*.py'
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

## Workflow rules

- The parent owns decomposition, sequencing, integration, final verification,
  and all git operations.
- Use `zz-readagent` before exploratory parent reads whenever the exact files
  and ranges are not already known; it returns an ordered subsystem map and
  exact cited ranges for the parent to inspect.
- Use `zz-brainstormer` only when materially different architecture approaches
  require a principal-level decision, then explicitly select one.
- Use `zz-designplanner` when the selected architecture warrants an SDD-style
  implementation design.
- Keep localized design choices, implementation-step decisions, and small
  design-document updates with the parent. Re-engage architecture agents only
  for an overall redesign.
- Give `zz-implementer` one bounded piece from an implementation document under
  `docs/artifacts/implementationdocs/`.
- Review important artifacts with three independent `zz-vetter` lenses:
  research grounding, live-tree feasibility, and consistency/severity.

The implementer hook snapshots implementation documents and ledgers outside the
repository. It rejects changed implementation documents, rewritten ledger
history, missing, empty, or multiple appended run records, invalid status or
ledger handoff fields, and overlapping implementer runs. Run ordinal, progress,
confidence, and validation quality remain agent-direction and parent-review
responsibilities. These checks enforce workflow structure; they do not replace
review or create a security boundary against hostile processes running as the
same OS user.

See [docs/copilot-native-agents.md](docs/copilot-native-agents.md) for the
design and full enforcement model.
