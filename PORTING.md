# Copilot port record

This repository was migrated from an initial harness-specific source copy to a
GitHub Copilot-native distribution.

## Changed

- Agent discovery moved to `.github/agents/*.agent.md`.
- Profiles now use Copilot's portable `read`, `search`, `execute`, and `edit`
  tool aliases and pin no model.
- The parent contract moved to `.github/copilot-instructions.md`.
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
- status and confidence must agree across the response and ledger; and
- low-confidence or malformed completion claims are blocked.

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
  remains authoritative because execute tools may write files indirectly.
