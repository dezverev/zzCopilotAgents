# Copilot port record

This repository was migrated from an initial harness-specific source copy to a
GitHub Copilot-native distribution.

## Changed

- Agent discovery moved to `.github/agents/*.agent.md`.
- Profiles now use Copilot's portable `read`, `search`, `execute`, and `edit`
  tool aliases and pin no model.
- The parent contract moved to `.github/copilot-instructions.md` and a
  synchronized repository-root `AGENTS.md`.
- Delegation guidance now names registered custom agents and Copilot's parallel
  subagent capability rather than a harness-specific invocation API.
- Repository hooks under `.github/hooks/` now enforce implementer handoffs on
  Copilot CLI and Copilot cloud agent.
- Grounding uses native Copilot tools. The built-in Explore agent is an optional
  parent aid, not a required dependency.
- A sixth native profile, `zz-readagent`, provides optional isolated-context
  factual scouting and read planning with only `read` and `search`.

## Preserved

- The six roles: factual scouting, options, design, diagnosis, bounded
  execution, and challenge.
- Parent ownership of decomposition, sequencing, review, integration, final
  verification, and all git operations.
- One independently vettable piece per implementer run.
- Three blind, independent vetter lenses.
- Read-only boundaries for five roles and write access only for the implementer.
- Confidence checkpoints, minimum-confidence reporting, and the hard stop below
  80%.

## Strengthened

The source copy described implementation-document integrity and ledger
verification as advisory parent checks. Copilot's `subagentStart`,
`preToolUse`, and `subagentStop` hooks make them deterministic:

- implementation documents are snapshotted and checked byte-for-byte;
- ledgers must be new or append-only;
- physical append order plus a verifier-checked per-ledger run ordinal is the
  authoritative chronology: the expected ordinal is the immutable baseline
  complete-record count plus one;
- every new progress section is contiguous, non-empty `step-N` notes beginning
  at `step-1`;
- status and confidence must agree across the response and ledger;
- every checkpoint line is parsed in `initial`, optional contiguous milestones,
  `final` order and included in the reported minimum; and
- low-confidence or malformed completion claims are blocked.

The repository-global active marker enforces one active implementer, while run
ordinals are counted separately for each ledger. At stop, orphaned, reversed,
nested, or unterminated exact baseline markers fail closed, as do invalid new
ordinals or progress. Legacy records remain byte-identical; their timestamps,
if present, are non-authoritative annotations. No wall-clock validation is
performed, and these hooks verify mechanical lifecycle evidence rather than
semantic implementation correctness or historical chronology.

Verifier state uses private 0700 directories and 0600 files. Those modes
protect against other OS users and accidental exposure, but not arbitrary
commands running as the same OS user. An execute-capable hostile or
noncooperative implementer sharing the execution principal can discover,
alter, or remove temporary verifier state. Without a separately privileged
principal or service, hooks are not a hostile-worker security boundary; they
remain fail-closed mechanical lifecycle protection for cooperative agents and
ordinary or accidental contract violations.

The verifier requires Python 3.10 or newer but no packages, MCP server, local model, or
network access.

## Intentional differences

- Agent profiles do not pin model names. In Copilot CLI, `/model` selects the
  active model and `/subagents` configures default or per-agent subagent
  models. In particular, `zz-readagent` intentionally omits `model`; the
  availability and semantics of these controls can differ in other Copilot
  clients and cloud runtimes, so omission alone does not establish identical
  inheritance behavior everywhere.
- Native `zz-readagent` is not the Qwen-backed, local-model/MCP
  `readsubagent`. It uses only Copilot's `read` and `search` tools and needs no
  Qwen, MCP, local or network service, or extra runtime.
- The scout is optional and can reduce parent-context reads, but it does not
  replace direct self-grounding by specialized roles or a vetter's own evidence
  inspection.
- Its prompt-level, model-mediated contract requires a `Question:`, accepts
  optional scope fields, and returns a direct `## Answer`, subsystem map,
  focused read list, anchors, and `path:line` citations. It refuses review,
  bug, diagnosis, design, and edit-strategy work. Current hooks enforce only
  the implementer lifecycle, not this scout contract, so behavior is not
  claimed to be deterministic across models.
- Pre-tool path blocking is defense in depth. Stop-time snapshot verification
  catches ordinary or accidental indirect writes but cannot isolate its state
  from hostile same-principal execute tools.
- Agent profile edits may not be loaded by an already-running Copilot CLI
  process. Restart the CLI and use a fresh session before claiming an edited
  profile is active.
