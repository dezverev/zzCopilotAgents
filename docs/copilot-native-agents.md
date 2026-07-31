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

Native `zz-readagent` uses only Copilot's `read` and `search` tools and requires
no local service, network service, or extra runtime. Its profile deliberately
has no `model` field. It therefore does not pin a model; absence of that field
alone does not establish identical inheritance behavior in every Copilot
client or cloud runtime.

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
to a cumulative ledger. Physical append order plus a verifier-checked run
ordinal is the authoritative chronology. Ordinals are local to each ledger:
the expected ordinal is the immutable baseline's complete-record count plus
one. New progress sections contain only contiguous, non-empty `step-1` through
`step-N` notes. Repository hooks parse this mechanical lifecycle contract; they
do not establish that the implementation is semantically correct.

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
repository-level active marker preserves the single-active-implementer
invariant across the repository. That global concurrency check is distinct
from chronology ordinals, which are counted independently in each ledger.

### Tool use

While matching implementer state is active, `preToolUse` denies direct edit,
create, write, or patch operations that expose a path to an implementation
document. Ledger paths and unrelated source paths remain available.

This is defense in depth. Execute tools can write indirectly and tool argument
shapes can vary.

### Stop

`subagentStop` blocks completion unless:

1. Start state exists and matches the repository and session.
2. No implementation document was added, removed, or changed.
3. The reported ledger is strictly under the ledger directory.
4. An existing ledger is an exact byte prefix of the current ledger, or the
   ledger is new.
5. The appended suffix contains exactly one complete run record.
6. Exact baseline run markers are ordered correctly, and the new record has
   exactly one positive decimal ordinal equal to the baseline complete-record
   count plus one.
7. New progress is a contiguous sequence of non-empty `step-N` notes beginning
   at `step-1`.
8. Response and ledger status and confidence agree.
9. Every confidence-checkpoint line parses; labels are ordered `initial`,
   optional contiguous `milestone-1` through `milestone-N`, then `final`; and
   the reported value equals the minimum of all checkpoints.
10. Confidence below 80% uses `blocked` with a non-empty reason and requested
   clarifications.

A baseline with orphaned, reversed, nested, or unterminated exact run markers
fails closed. Missing, duplicate, malformed, or incorrect new ordinals and
empty, malformed, duplicated, gapped, or reordered progress steps likewise
fail closed at stop. Existing legacy record bytes are not normalized or
rewritten: any timestamps in them remain non-authoritative annotations. The
verifier performs no wall-clock validation and makes no claim about historical
chronology beyond physical append order and checked ordinals.

A rejected stop retains its original baseline so a forced continuation is
checked against the same evidence. Accepted stops remove temporary state.

Temporary verifier state uses 0700 directories and 0600 files. These private
modes protect it from other OS users and accidental exposure, not arbitrary
commands running as the same execution principal. An execute-capable hostile
or noncooperative implementer sharing that OS user can discover, alter, or
remove the state. The hooks therefore are not a hostile-worker security
boundary without a separately privileged principal or service. They remain
fail-closed mechanical lifecycle protection for cooperative agents and
ordinary or accidental contract violations.

## Runtime and portability

The verifier uses Python 3.10 or newer, only its standard library, and no network. Copilot cloud
agent runs the hook's `bash` entry in Linux. Copilot CLI selects the `bash` or
`powershell` entry for the local operating system; the PowerShell entry invokes
the same Python verifier.

Hook failures are fail-closed for the implementer. Python 3 is therefore an
explicit installation prerequisite rather than an optional enhancement.
After editing an agent profile, restart Copilot CLI and use a fresh session
before claiming the new profile text is loaded; an already-running process may
retain the previous profile.

## Parent contract

`.github/copilot-instructions.md` is loaded as repository-wide Copilot guidance.
It defines role selection, requires explicit solution choice before design,
keeps implementation pieces bounded, preserves three-lens verification, and
leaves decomposition, sequencing, integration, final verification, and all git
operations with the parent.

The repository-root `AGENTS.md` carries the same marked contract for tools that
discover root agent guidance. The surrounding introductions may differ, but an
automated test requires the `zz-copilot-agents` blocks to remain byte-identical.
