# The zz-* Copilot custom-agent set

The distribution maps six workflow roles onto repository custom agents while
keeping orchestration with the parent Copilot session.

## Design decisions

**Native custom agents.** Profiles live in `.github/agents/*.agent.md` and run
as isolated Copilot subagents. They use portable tool aliases rather than
runtime-specific concrete tool names and pin no model. In Copilot CLI, `/model`
selects the active model and `/subagents` configures default or per-agent
subagent models. Other Copilot clients and cloud runtimes may expose different
controls or semantics.

**Self-contained grounding.** Each role searches and reads the live repository
directly with Copilot's native tools. `zz-readagent` is an optional
isolated-context factual scout and read planner: it can absorb broad discovery
and reduce reads in the parent's context, but each other specialized role still
grounds itself directly and every vetter inspects its own evidence.

This role is distinct from the Qwen-backed, local-model/MCP `readsubagent` in
related implementations. Native `zz-readagent` uses only Copilot's `read` and
`search` tools and requires no Qwen, MCP, local service, network service, or
extra runtime. Its profile deliberately has no `model` field. It therefore
does not pin a model; absence of that field alone does not establish identical
inheritance behavior in every Copilot client or cloud runtime.

**Stable scout handoff.** A dispatch has a required `Question:` and may include
`Paths:`, `Symbols:`, `Search terms:`, `Line ranges:`, and `Output:`. The report
starts with a direct `## Answer`, then supplies a compact subsystem map,
focused read list, anchors, and `path:line` or `path:start-end` citations.
Review, bug hunting, diagnosis, design selection, and edit-strategy requests
are refused rather than converted into recommendations.

**One vetter profile, three independent runs.** The parent launches
`zz-vetter` three times in parallel with the `research-grounding`,
`feasibility-live-tree`, and `consistency-severity` lenses. Separate contexts
preserve deliberate blindness; the parent compares the reports.

**One bounded implementation piece.** An approved design is recorded under
`docs/artifacts/implementationdocs/`. The parent assigns one medium-to-small,
independently testable piece to `zz-implementer`, reviews its diff and ledger,
and validates it before assigning another piece. Parallel implementers are
prohibited even though Copilot supports parallel subagents.

**Markdown handoffs with a machine-checked ledger.** Human-readable reports use
stable Markdown sections. Each implementation run appends one delimited record
to a cumulative ledger. Repository hooks parse only the small stable contract:
status, reported confidence, confidence checkpoints, validation, and the ledger
path.

## Native tool boundaries

| Agent | Native aliases | Boundary |
|---|---|---|
| `zz-readagent` | `read`, `search` | factual scouting and read planning only |
| `zz-brainstormer` | `read`, `search` | options only |
| `zz-designplanner` | `read`, `search` | design only |
| `zz-debugger` | `read`, `search`, `execute` | read-only diagnosis |
| `zz-implementer` | `read`, `search`, `execute`, `edit` | one approved piece |
| `zz-vetter` | `read`, `search`, `execute` | read-only verification |

Prompt-level policies further constrain `execute` for debugger and vetter to
non-mutating inspection. No subagent performs git mutations. The scout's
dispatch, report, citation, and refusal contract is likewise prompt-level and
model-mediated; behavior can vary with the selected model.

## Lifecycle enforcement

`.github/hooks/zz-implementer.json` registers three hooks backed by the
standard-library Python verifier in
`.github/hooks/scripts/verify-implementer.py`.

These hooks enforce only the implementer lifecycle described below. There is
no hook enforcement of `zz-readagent` behavior or report formatting.

### Start

For `zz-implementer`, `subagentStart` snapshots all direct Markdown
implementation documents and existing ledgers. State is keyed by canonical
repository root and session ID in the platform temporary directory. A
repository-level active marker preserves the single-implementer invariant.

### Tool use

While matching implementer state is active, `preToolUse` denies direct edit,
create, write, or patch operations that expose a path to an implementation
document. Ledger paths and unrelated source paths remain available.

This is defense in depth, not the final integrity boundary. Execute tools can
write indirectly and tool argument shapes can vary.

### Stop

`subagentStop` blocks completion unless:

1. Start state exists and matches the repository and session.
2. No implementation document was added, removed, or changed.
3. The reported ledger is strictly under the ledger directory.
4. An existing ledger is an exact byte prefix of the current ledger, or the
   ledger is new.
5. The appended suffix contains exactly one complete run record.
6. Response and ledger status and confidence agree.
7. Initial and final confidence checkpoints exist and the reported value equals
   the run's minimum checkpoint.
8. Confidence below 80% uses `blocked` with a non-empty reason and requested
   clarifications.

A rejected stop retains its original baseline so a forced continuation is
checked against the same evidence. Accepted stops remove temporary state.

## Runtime and portability

The verifier uses Python 3.10 or newer, only its standard library, and no network. Copilot cloud
agent runs the hook's `bash` entry in Linux. Copilot CLI selects the `bash` or
`powershell` entry for the local operating system; the PowerShell entry invokes
the same Python verifier.

Hook failures are fail-closed for the implementer. Python 3 is therefore an
explicit installation prerequisite rather than an optional enhancement.

## Parent contract

`.github/copilot-instructions.md` is loaded as repository-wide Copilot guidance.
It defines role selection, requires explicit solution choice before design,
keeps implementation pieces bounded, preserves three-lens verification, and
leaves decomposition, sequencing, integration, final verification, and all git
operations with the parent.
