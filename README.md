# zzCopilotAgents

A GitHub Copilot custom-agent workflow with six focused agents, a parent-side
delegation contract, and fail-closed implementer lifecycle hooks. The agent
profiles need no MCP server or local model service; the implementer hooks
require Python 3.10 or newer.

## What ships

| Role | Profile | Tools | Writes files |
|---|---|---|---|
| Factual scout | `.github/agents/zz-readagent.agent.md` | `read`, `search` | no |
| Options | `.github/agents/zz-brainstormer.agent.md` | `read`, `search` | no |
| Design | `.github/agents/zz-designplanner.agent.md` | `read`, `search` | no |
| Diagnosis | `.github/agents/zz-debugger.agent.md` | `read`, `search`, `execute` | no |
| Execution | `.github/agents/zz-implementer.agent.md` | `read`, `search`, `execute`, `edit` | **yes** |
| Challenge | `.github/agents/zz-vetter.agent.md` | `read`, `search`, `execute` | no |

The profiles are only part of the system:

- `.github/copilot-instructions.md` tells the parent when and how to delegate,
  keeps integration and git operations with the parent, and requires three
  independent `zz-vetter` lenses for high-value review.
- `AGENTS.md` exposes the same marked parent contract to tools that discover
  repository-root agent guidance. A test keeps the two copies synchronized.
- `.github/hooks/zz-implementer.json` enforces implementation-document
  immutability, append-only ledgers, and confidence consistency.

Every role grounds itself against the live tree with Copilot's native `search`
and `read` tools. `zz-readagent` is an optional isolated-context factual scout
and read planner that can reduce reads in the parent's context. It does not
replace direct self-grounding by the other specialized roles or each vetter's
own evidence inspection.

This native role uses only Copilot's `read` and `search` tools and needs no
local or network service or extra runtime. Its profile intentionally omits
`model`, and none of the profiles pins a model. In Copilot CLI, users can
select the active model with `/model` and configure default or per-agent
subagent models with `/subagents`. Model controls and selection semantics can
differ in other Copilot clients and cloud runtimes, so the absent field alone
is not a claim of identical inheritance everywhere.

Dispatch it with a required `Question:` and, when useful, optional `Paths:`,
`Symbols:`, `Search terms:`, `Line ranges:`, and `Output:` fields. It reports a
direct `## Answer`, compact subsystem map, focused read list, anchors, and
repository `path:line` citations. It refuses review, bug hunting, diagnosis,
design selection, and edit-strategy work. This contract is prompt-level and
model-mediated, so adherence can vary by selected model. Repository hooks
currently enforce only the implementer lifecycle; they do not enforce
`zz-readagent` reports.

## Requirements

- GitHub Copilot CLI or Copilot cloud agent with custom agents and repository
  hooks enabled.
- Python 3.10 or newer available as `python3` on Linux/macOS or `python` on
  Windows.

The hook verifier uses only Python's standard library and makes no network
calls. Cloud agent runs the `bash` command in its Linux environment; local
Copilot CLI chooses `bash` or `powershell` for the current operating system.

## Install in a repository

Use this only for a new installation where none of the destination package
paths already exist. If any are present, stop and inspect them; merge the
package changes into customized profiles, instructions, hooks, or `AGENTS.md`
instead of overwriting them.

```sh
source=/path/to/zzCopilotAgents
target=/path/to/target-repo

install_zz_copilot_agents() {
  for path in .github/agents .github/hooks \
    .github/copilot-instructions.md AGENTS.md
  do
    if [ -e "$target/$path" ] || [ -L "$target/$path" ]; then
      printf 'Refusing to overwrite %s; inspect and merge it instead.\n' \
        "$target/$path" >&2
      return 1
    fi
  done

  mkdir -p "$target/.github/agents" "$target/.github/hooks/scripts" &&
  cp "$source"/.github/agents/zz-*.agent.md "$target/.github/agents/" &&
  cp "$source/.github/hooks/zz-implementer.json" "$target/.github/hooks/" &&
  cp "$source/.github/hooks/scripts/verify-implementer.py" \
    "$target/.github/hooks/scripts/" &&
  cp "$source/.github/copilot-instructions.md" \
    "$target/.github/copilot-instructions.md" &&
  cp "$source/AGENTS.md" "$target/AGENTS.md"
}

install_zz_copilot_agents
```

The explicit file list copies the tracked package content without recursively
copying generated files from a used checkout, such as Python bytecode under a
hook `__pycache__`. Keep the `<!-- zz-copilot-agents:start -->` and
`<!-- zz-copilot-agents:end -->` markers around the parent contract so an
installer can update that block safely.

Restart Copilot CLI after installation or after editing a profile, then use a
fresh session before claiming the edited profile is loaded. An existing CLI
process may retain the prior custom-agent profile; custom agents, instructions,
and hook configuration are loaded when a session starts.

## Install agents for one user

Agent profiles can be made available across repositories. This command is only
for profiles that are not already installed. If a same-named profile exists,
it refuses to overwrite it; inspect and merge customized profiles instead.

```sh
source=/path/to/zzCopilotAgents
destination="$HOME/.copilot/agents"

install_zz_user_agents() {
  for profile in "$source"/.github/agents/zz-*.agent.md
  do
    installed="$destination/${profile##*/}"
    if [ -e "$installed" ] || [ -L "$installed" ]; then
      printf 'Refusing to overwrite %s; inspect and merge it instead.\n' \
        "$installed" >&2
      return 1
    fi
  done

  mkdir -p "$destination" &&
  cp "$source"/.github/agents/zz-*.agent.md "$destination/"
}

install_zz_user_agents
```

The parent contract and enforcement hooks are repository policy, so a complete
installation still needs `AGENTS.md`, `.github/copilot-instructions.md`, and
`.github/hooks/` in each repository.

## Verify

### Verify the source distribution

From the `zzCopilotAgents` source checkout, run the automated verifier tests:

```sh
python3 -m unittest discover -s tests/agents -p 'test_*.py'
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

### Verify the installed package

After installation, open the target repository and start a fresh Copilot CLI
session there:

1. Run `/agent` and confirm all six `zz-*` agents are listed.
2. Run `/env` and confirm the repository instructions and hook file are loaded.
3. Dispatch a factual question, a read-planning question, and a prohibited
   review request; inspect the report/citations and refusal.
4. Use `/model` to select another available model and repeat representative
   dispatches when practical. Use `/subagents` to inspect or configure the
   default and per-agent subagent model choices.

The three vetter lenses should be delegated as three parallel, independent
subagents. `zz-implementer` runs one bounded design piece at a time and maintains
an append-only ledger under `docs/artifacts/implementationdocs/ledgers/`.

## Enforcement model

At implementer start, the hook snapshots implementation documents and ledgers
outside the repository. Direct edits to implementation documents are denied
where the edit tool exposes a path. At implementer stop, the snapshot check
fails closed and blocks the handoff unless:

- implementation documents are byte-for-byte unchanged;
- the reported ledger is new or append-only;
- a cumulative ledger may contain multiple prior records, but the current
  run's appended suffix contains exactly one complete delimited record;
- exact baseline markers are properly ordered, and the new record's one
  positive decimal run ordinal equals the immutable baseline complete-record
  count plus one;
- progress consists only of contiguous, non-empty `step-N` notes beginning at
  `step-1`;
- response status and confidence match the ledger; and
- every confidence-checkpoint line parses, labels are ordered as `initial`,
  optional contiguous milestones, then `final`, and reported confidence is the
  minimum of all those checkpoints.

Physical append order plus that verifier-checked ordinal is authoritative
chronology. Ordinals are per ledger; they are separate from the
repository-global active marker that permits only one implementer at a time.
Orphaned, reversed, nested, or unterminated exact baseline markers fail closed,
as do invalid new ordinals or progress, when the implementer stops. Legacy
record bytes remain untouched, including any timestamps; those timestamps are
non-authoritative, and no wall clock is validated.

Confidence below 80% is accepted only as `blocked` with a reason and concrete
clarifications. Pre-tool denial is defense in depth because shell commands can
write indirectly. Private verifier state uses 0700 directories and 0600 files,
which protect it from other OS users and accidental exposure, not arbitrary
commands run by the same execution principal. An execute-capable hostile or
noncooperative implementer sharing that OS user can discover, alter, or remove
temporary state. Without a separately privileged principal or service, these
hooks are not a hostile-worker security boundary. They are fail-closed
mechanical lifecycle protection for cooperative agents and ordinary or
accidental contract violations; they do not certify implementation semantics or
replace parent review of diffs, tests, reports, and ledgers.

See [docs/copilot-native-agents.md](docs/copilot-native-agents.md) for the
design.
