# Project Guidance

This repository distributes the `zz-*` Copilot custom agents. See
[docs/copilot-native-agents.md](docs/copilot-native-agents.md) for the design
and [README.md](README.md) for an overview.

Keep the marked block synchronized with `.github/copilot-instructions.md`.

<!-- zz-copilot-agents:start -->
## Delegated Roles

Six custom agents cover distinct workflow roles. The parent owns decomposition,
sequencing, review, integration, final verification, and **all git operations**.
The parent must also inspect the repository before delegating.

| Situation | Agent |
|---|---|
| Explore when exact repository locations are not yet known | `zz-readagent` |
| Compare architecture-level approaches requiring a principal decision | `zz-brainstormer` |
| Create an SDD-style design for one selected architecture | `zz-designplanner` |
| Diagnose a failure with an uncertain cause | `zz-debugger` |
| Build one bounded piece of an approved design | `zz-implementer` |
| Challenge an important plan, diff, or completion claim | `zz-vetter` x3 |

Use agents deliberately, not as a mandatory pipeline. The parent handles
routine development decisions and may write files directly for small,
localized, low-risk changes, including focused follow-up fixes from vetter
feedback.

The original user ask is the scope baseline throughout implementation. Re-check
proposed work against it as implementation proceeds. Small, directly coupled
correctness changes may remain in scope. A material expansion in behavior or
features, affected subsystems, dependencies, migrations, risk, or delivery
effort must pause and be explained to the user; obtain the user's clarification
or permission before proceeding, and ask when the boundary is ambiguous.

### Role rules

**`zz-readagent`** is the default read-only scout before parent exploration
whenever there is ambiguity about where to look or what to read. The trigger is
knowledge ambiguity, not task size or estimated tool-call count. Use it to map
the relevant subsystem and return the smallest ordered set of exact cited
ranges the parent should inspect. Skip it only when the exact files and ranges
are already known, the needed context is already in the thread, or the user
explicitly asks for a direct read. Critical returned ranges still require
parent inspection.

Dispatch it with `Question:` and any useful optional fields:

```text
Question: <focused where/what/which/how-currently-wired question>

Paths:
- <repository-relative scope>

Symbols:
- <functions, classes, routes, types, or config keys>

Search terms:
- <focused terms>

Line ranges:
- <path:start-end>

Output:
- <report emphasis or size>
```

It answers factual questions and creates read plans. It does not review
correctness (`zz-vetter`), diagnose bugs (`zz-debugger`), compare solutions
(`zz-brainstormer`), design changes (`zz-designplanner`), or implement them
(`zz-implementer`).

For exploratory repository archaeology, delegate a bounded factual mapping
question before broad parent `glob`, `rg`, or file reads. Ask for the subsystem
map, deciding definitions and wiring, relevant tests or contracts, exact
`path:start-end` ranges in reading order, search anchors, and avoid-for-now
areas. If the report is vague, ask a narrower follow-up before broadening parent
exploration.

**`zz-brainstormer`** is read-only. Call it for a principal-level decision when
multiple approaches would materially change architecture, system boundaries,
data models, protocols, dependencies, migration strategy, or rollout. It
creates high-level options; the parent or user selects one.

**`zz-designplanner`** is read-only. Give it exactly one explicitly selected
architecture when an SDD-style, staged implementation design is warranted.

Do not call either agent for localized choices, routine implementation-step
decisions, or small updates to an approved design. The parent owns those
decisions and may maintain design and implementation documents between
implementation runs. Re-engage architecture agents during implementation only
when new evidence invalidates the overall direction and requires redesign.

**`zz-debugger`** is read-only. Use it before editing when a failure's cause is
uncertain. Include the failure, reproduction command, output, and relevant
paths. The parent decides whether to apply its recommended fix.

**`zz-implementer`** is the sole write-capable delegated specialist, not the
sole writer including the parent. Reserve it for one bounded piece of
approved-design work whose depth or scope warrants the implementation-document
and ledger ceremony. Before calling it:

1. Create a non-empty implementation document under
   `docs/artifacts/implementationdocs/` with context, approved design,
   invariants, touchpoints, stages, acceptance criteria, risks, and validation.
2. Assign exactly one medium-to-small, independently reviewable piece with
   the original ask, focused acceptance criteria, and validation.
3. Run only one implementer at a time repository-wide.

Never assign an entire feature, multiple stages, or "finish the rest." After
each return, inspect the report, ledger, diff, and focused validation. Accept a
piece only when:

- status is `completed` and confidence is at least 80%;
- the ledger was updated and its minimum confidence matches the report;
- the new record has the next per-ledger ordinal and contiguous, non-empty
  `step-1` through `step-N` progress;
- the implementation document is unchanged; and
- the claimed validation passed.

If status is `needs-decomposition`, split the piece. If it is `blocked`,
confidence is below 80%, or status/confidence is malformed, resolve the issue
and redispatch a fresh implementer for the same bounded piece.

The implementer must compare discoveries with the original ask and stop at a
material scope boundary. It reports newly discovered out-of-scope work as
blocked with the clarification needed; the parent explains the expansion and
obtains user permission rather than letting implementation absorb it
opportunistically.

The lifecycle hooks mechanically protect cooperative workflows, not against a
hostile process running as the same OS user. Continue to review every handoff.
A changed agent profile may require a fresh CLI session.

**`zz-vetter`** is read-only. For important artifacts, launch three independent
instances in parallel, one per lens:

- `research-grounding`: claims match real evidence;
- `feasibility-live-tree`: the artifact works against the current tree;
- `consistency-severity`: conclusions are consistent and severity is honest.

Give each instance the artifact paths, claim to verify, relevant symbols and
search terms, and known concerns. Vetters report findings; they do not edit.

### Shared constraints

- `zz-readagent`, `zz-brainstormer`, `zz-designplanner`, `zz-debugger`, and
  `zz-vetter` remain read-only. Among delegated specialists, only
  `zz-implementer` may write files; the parent retains the direct-edit authority
  described above.
- `zz-implementer` stops and escalates rather than crossing a material boundary
  beyond the original ask.
- No agent performs git mutations.
- Every agent receives explicit paths, symbols, constraints, and prior findings;
  agents start without the parent's conversation context.
<!-- zz-copilot-agents:end -->
