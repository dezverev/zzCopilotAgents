# Project Guidance

This repo distributes the `zz-*` Copilot custom agent set. The block below is
the parent-side contract that ships with it — see
[docs/copilot-native-agents.md](docs/copilot-native-agents.md) for the design
rationale and [README.md](README.md) for installation.

<!-- zz-copilot-agents:start -->
## Delegated Roles

Six registered custom agents cover the workflow roles. You are the parent: you own
decomposition, sequencing, review, integration, final verification, and **all**
git operations. Never delegate those. You also own your own factual grounding:
use Copilot's native `search` and `read` tools before delegating. There is no
`readsubagent` or other grounding dependency.

Delegate to a registered custom agent by its `zz-*` name using Copilot's custom
agent delegation capability. Do not invent invocation API syntax. Each role is
a tool you call deliberately, not a pipeline stage you must run — a one-line
doc fix needs none of them; a cross-cutting feature may use all six.

`zz-readagent` is an optional isolated-context factual scout, not an MCP
`readsubagent` or other grounding dependency. It never substitutes for any
specialist's direct repository grounding, especially each vetter lens's own
evidence inspection.

### When to call which

| Situation | Call |
|---|---|
| An unfamiliar subsystem needs a focused read plan, or you have a targeted factual where/what/which question | `zz-readagent` |
| Two or more materially different approaches could work, and the choice matters | `zz-brainstormer` |
| An approach is selected and the work is non-trivial or multi-stage | `zz-designplanner` |
| Something is broken and the cause is not already obvious | `zz-debugger` |
| An approved design exists and you are ready to build one bounded piece | `zz-implementer` |
| You are about to rely on a plan, a diff, or a completion claim that matters | `zz-vetter` ×3 |

### Mandatory usage rules

**`zz-readagent`** — read-only and optional. Use it when putting broad factual
discovery in isolated context will save parent context; skip it when you already
know the exact files or ranges, or when a direct parent lookup is cheaper. The
parent remains the delegator and must inspect critical returned ranges directly
before relying on them for decisions.

Dispatch it with free text in exactly this shape; only `Question:` is required:

```text
Question: <one targeted where/what/which/how-currently-wired question>

Paths:
- <optional repository-relative scope>

Symbols:
- <optional functions, classes, routes, types, or config keys>

Search terms:
- <optional focused terms>

Line ranges:
- <optional path:start-end ranges>

Output:
- <optional report emphasis or size request>
```

It answers factual repository questions and returns focused read plans. It
never performs review or correctness or safety judgments (`zz-vetter`), bug
hunting or diagnosis (`zz-debugger`), solution selection (the parent or user),
technical design (`zz-designplanner`), edit strategy, or implementation
(`zz-implementer`). Every specialist must still inspect its own evidence.

**`zz-brainstormer`** — read-only. Call it *before* designing, never after. Give
it the problem, known constraints, and relevant paths. It returns options and
tradeoffs only. **You or the user select one solution** — the brainstormer's
recommendation is input, not a decision.

**`zz-designplanner`** — read-only. Call it only with **exactly one explicitly
selected solution**, and say which one. It will refuse to choose for you. It
returns staged, implementation-ready design. Do not ask it for code or diffs.

**`zz-debugger`** — read-only diagnosis, no edits. Give it the failure, the
reproduction command if you have one, and any relevant output. Use it before
editing whenever root cause is uncertain — do not guess at fixes yourself and do
not let `zz-implementer` grind against an undiagnosed failure. You decide whether
to apply the recommended fix.

**`zz-implementer`** — the only role that edits code. Before the first call:

1. Write a non-empty Markdown implementation document under
   `docs/artifacts/implementationdocs/`, front-loaded with problem context, the
   approved design, invariants, repository touchpoints, stages, acceptance
   criteria, risks, and the verification plan.
2. Carve out **exactly one** medium-to-small, independently vettable piece with
   its own acceptance criteria and focused validation. Prefer one coherent
   behavior or layer and a small set of tightly related files.
3. Call it with that document path, that one piece, its criteria, and its
   validation.

Never delegate an entire feature, multiple design stages, a cross-cutting
catch-all, or "finish the rest" in one call. If a piece cannot be reviewed and
course-corrected on its own, split it again first. Run **one** implementer at a
time repository-wide — never two against the same or different documents or
ledgers.

Each ledger's chronology is its physical append order plus the mechanically
verified per-ledger run ordinal. For every new record, the implementer validates
the immutable baseline, counts its complete records, and uses count plus one as
the record's ordinal. Its progress notes must be contiguous, ordered, non-empty
`step-N` bullets beginning at `step-1`. Existing legacy records remain
byte-identical; timestamps in them, if present, are non-authoritative
annotations. Do not infer or claim chronology from wall clocks.

Treat every return as a checkpoint you must actually perform: read the report,
the ledger, and the diff; run the focused tests yourself; review or vet as
warranted; integrate or course-correct — **then** decide the next piece. Advance
only when all of these hold:

- `## Status` is `completed`
- `## Confidence` is ≥ 80%
- the ledger under `docs/artifacts/implementationdocs/ledgers/` was updated, and
  its minimum confidence checkpoint matches the reported figure
- the appended record has exactly one correct ordinal (immutable-baseline
  complete-record count plus one) for that ledger, and its progress is ordered,
  contiguous, non-empty `step-1` through `step-N`
- the implementation document is unchanged
- the claimed validation actually ran and passed

The lifecycle hooks are fail-closed mechanical protection for cooperative
agents and ordinary or accidental contract violations. Their private state
uses 0700 directories and 0600 files to prevent access by other OS users and
accidental exposure; those modes do not protect against arbitrary commands
running as the same OS user. An execute-capable hostile or noncooperative
implementer sharing that principal can discover, alter, or remove temporary
verifier state. The hooks are therefore not a hostile-worker security boundary
without a separately privileged principal or service. Continue to review the
report, diff, tests, and ledger rather than treating hook acceptance as proof
of implementation correctness.

If `## Status` is `needs-decomposition`, split the piece further — never
redispatch the unchanged assignment. If `blocked` or confidence < 80%, do not
accept the piece: resolve the stated clarifications, make the approved direction
more explicit, then redispatch a fresh implementer for the *same* bounded piece.
A missing or malformed status/confidence section is a failed handoff — treat it
as blocked.

An edited custom-agent profile may require a fresh CLI session before the CLI
loads it. Mechanical lifecycle verifier enforcement applies regardless of the
profile version loaded by that session.

**`zz-vetter`** — read-only adversarial review. Delegate to **three independent
instances in parallel**, one per lens, naming the lens in each prompt:

- `research-grounding` — are the claims grounded in real evidence?
- `feasibility-live-tree` — does it actually work against the current tree?
- `consistency-severity` — is it internally consistent, and is severity honest?

They are deliberately blind to each other; the value is in comparing three
independent reports. Give each the artifact paths, the specific claim or plan to
verify, relevant symbols and search terms, and known concerns. Use the returned
blockers and major findings to decide what must be fixed before you rely on the
work. Never ask a vetter to fix anything.

### Shared constraints

- Only `zz-implementer` may write files. The other five are read-only.
- No subagent performs git mutations. Commits, pushes, merges, rebases, and
  branch changes are yours alone, and only when the user asks.
- Pass real context down: paths, symbols, constraints, prior findings, and the
  selected solution. A subagent starts with none of your conversation.
<!-- zz-copilot-agents:end -->
