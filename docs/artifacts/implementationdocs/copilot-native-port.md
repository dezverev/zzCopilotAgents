# Copilot-native agent port

## Problem context

This repository is a verbatim Claude Code agent distribution. Its discovery
paths, profile frontmatter, parent instructions, invocation language, model
names, and documentation are Claude-specific. `PORTING.md` also identifies two
lost upstream guarantees that should be restored when the target harness
supports hooks: implementation documents must remain unchanged, and implementer
handoffs must have a valid updated ledger whose minimum confidence agrees with
the report.

The selected solution is a wholesale Copilot-native port with fail-closed
lifecycle enforcement. No Claude compatibility layer will remain.

## Approved design

### Native distribution

- Move the five profiles to `.github/agents/zz-*.agent.md`.
- Use Copilot's portable tool aliases:
  - brainstormer and design planner: `read`, `search`
  - debugger and vetter: `read`, `search`, `execute`
  - implementer: `read`, `search`, `execute`, `edit`
- Omit Claude model tiers and do not guess a Copilot model identifier.
- Move the parent contract to `.github/copilot-instructions.md`.
- Refer to registered agents by name rather than Claude's
  `Agent(subagent_type=...)` syntax.
- Preserve three independent, parallel `zz-vetter` runs.

### Native grounding

There is no `readsubagent`, local-model MCP server, or other required grounding
dependency. Every role uses Copilot's native `search` and `read` tools to inspect
the live tree. Roles with `execute` may use read-only shell inspection where
their prompt permits it. Copilot's built-in Explore agent may be used by the
parent for isolated factual discovery when useful, but it is optional and never
replaces a role's own grounding. In particular, a vetter must inspect evidence
itself.

### Hook enforcement

Register repository hooks from `.github/hooks/zz-implementer.json` for
`subagentStart`, `preToolUse`, and `subagentStop`. Use one Python 3
standard-library verifier, invoked as `python3` on Unix and `python` from
PowerShell. Python 3 is the only hook runtime prerequisite; no packages, `jq`,
or network access are allowed.

The verifier acts only on `zz-implementer` lifecycle events:

1. On start, correlate state by canonical repository root plus `sessionId`.
   Snapshot every direct Markdown implementation document under
   `docs/artifacts/implementationdocs/`, excluding `ledgers/`, and every existing
   ledger. Store state outside the repository in the platform temporary
   directory. Reject a concurrent start for the same repository. The lack of
   `agentId` in `subagentStart` is intentional; the single-active-implementer
   invariant makes repository plus session sufficient.
2. Before edit/create tools, deny paths that resolve to implementation documents
   while allowing the `ledgers/` subtree. This is defense in depth only.
3. On stop, parse the implementer's response and the named ledger. Require
   unique `## Status`, `## Confidence`, and `## Ledger` sections; an allowed
   status; confidence from 0 through 100; and a ledger path strictly beneath
   `docs/artifacts/implementationdocs/ledgers/`.
4. Require all implementation documents to be byte-identical to the start
   snapshot with no additions or deletions.
5. Require the ledger to be new or append-only relative to its baseline and to
   append exactly one delimited run record. The record contains status,
   reported confidence, initial and final confidence checkpoints, and the
   existing progress/validation fields. Response status and confidence must
   match the record, and response confidence must equal the minimum checkpoint
   in that run.
6. Confidence below 80 is valid only with status `blocked` and non-empty
   low-confidence reason and clarification sections. `completed` below 80 is
   always rejected.
7. Return `{"decision":"block","reason":"..."}` for malformed or unverifiable
   handoffs. Keep baseline state across a blocked continuation. Return
   `{"decision":"allow"}` and remove state only after acceptance.

The implementation ledger record markers are:

```text
<!-- zz-implementer-run:start -->
...
<!-- zz-implementer-run:end -->
```

The latest run suffix must contain exactly one complete pair. Existing ledger
bytes must be an exact prefix of the updated ledger.

## Invariants

- The parent owns decomposition, sequencing, review, integration, final
  verification, and all git operations.
- Only `zz-implementer` can edit files.
- One implementer run handles exactly one bounded, independently vettable piece.
- Only one implementer runs at a time.
- Read-only agents do not mutate files, install dependencies, or mutate git.
- The implementation document is authoritative and read-only.
- Handoff verification fails closed when state or evidence is missing.
- The five agents are self-grounding and have no `readsubagent` dependency.
- Agent prompts remain below Copilot's 30,000-character limit.

## Repository touchpoints

- Replace `.claude/agents/*.md` with `.github/agents/*.agent.md`.
- Replace `CLAUDE.md` with `.github/copilot-instructions.md`.
- Add `.github/hooks/zz-implementer.json`.
- Add `.github/hooks/scripts/verify-implementer.py`.
- Add focused verifier tests under `tests/hooks/`.
- Rewrite `README.md`, `PORTING.md`, and
  `docs/claude-native-subagents.md` for Copilot.

## Stages

### Stage 1 - Lifecycle verifier

Implement the Python verifier and focused tests. Do not activate the hook JSON
or migrate agent profiles yet.

Acceptance criteria:

- Start state snapshots documents and ledgers outside the repository.
- Non-implementer events are no-ops.
- Stop accepts valid new and append-only ledgers.
- Stop rejects missing state, document changes, invalid ledger paths,
  non-append-only ledgers, malformed/duplicate report headings, status or
  confidence disagreement, missing checkpoints, and confidence policy
  violations.
- A blocked stop retains state; an accepted stop removes it.
- Pre-tool checks deny implementation-document edits and allow ledgers and
  unrelated files.
- Tests use only Python's standard library.

Focused validation:

```sh
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

### Stage 2 - Copilot-native profiles and parent contract

Create all five Copilot profiles and the repository-wide Copilot instructions.
Update the implementer ledger protocol to match Stage 1. Remove all Claude
profiles and `CLAUDE.md` in the same piece.

Acceptance criteria:

- All five profiles use `.agent.md`, portable Copilot aliases, and no Claude
  model names.
- Only the implementer has `edit`.
- Native grounding and optional Explore usage are explicit; no readsubagent is
  required or assumed.
- Parent instructions preserve role selection, bounded implementation, parallel
  three-lens vetting, handoff review, and parent-owned git.
- The implementer emits the delimited ledger record Stage 1 verifies.
- No `.claude/agents` files or root `CLAUDE.md` remain.

Focused validation:

```sh
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

### Stage 3 - Activate hooks and rewrite distribution documentation

Add hook registration and rewrite the public documentation for the shipped
Copilot behavior. `PORTING.md` becomes a completed port record rather than an
instruction to future porters.

Acceptance criteria:

- Hook JSON is valid and registers start, pre-tool, and stop scripts for Unix
  and PowerShell.
- README installation and verification use Copilot paths and commands.
- Design documentation accurately distinguishes native tools, optional Explore,
  and deterministic hook enforcement.
- Active files contain no stale Claude discovery paths, model tiers, or
  delegation syntax except historical comparison in `PORTING.md`.

Focused validation:

```sh
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
python3 -m json.tool .github/hooks/zz-implementer.json >/dev/null
```

## Risks

- Python 3 must exist in the hook environment. The README must state this
  prerequisite and hook failure must deny rather than silently accept.
- Tool argument shapes vary; pre-tool protection is defense in depth. Snapshot
  verification remains authoritative.
- Byte-level snapshots intentionally reject concurrent edits, newline
  normalization, and unrelated implementation-document changes.
- Forced continuations are runtime-capped, so block reasons must be concise and
  actionable.

## Verification plan

Run the focused verifier suite after every stage. After migration, validate all
frontmatter, prompt sizes, JSON syntax, stale Claude references, and git diff.
Then run three independent vetter lenses over the completed port.

## Whole-port acceptance criteria

- Copilot discovers five repository custom agents and repository instructions.
- The distribution requires no `readsubagent`, MCP server, or package install.
- Hooks deterministically enforce document immutability, ledger updates, and
  confidence consistency.
- CLI and cloud-compatible repository paths and hook events are documented.
- The repository contains one coherent Copilot-native distribution.
