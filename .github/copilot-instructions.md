# Project Guidance

This repository distributes the `zz-*` Copilot custom agents. See
[docs/copilot-native-agents.md](../docs/copilot-native-agents.md) for the design
and [README.md](../README.md) for an overview.

Keep the marked block synchronized with the repository-root `AGENTS.md`.

<!-- zz-copilot-agents:start -->
## Delegated Roles

Six custom agents cover distinct workflow roles. The parent owns decomposition,
sequencing, review, integration, final verification, and **all git operations**.
The parent must also inspect the repository before delegating.

| Situation | Agent |
|---|---|
| Answer a focused repository question or produce a read plan | `zz-readagent` |
| Compare materially different approaches | `zz-brainstormer` |
| Design one selected non-trivial approach | `zz-designplanner` |
| Diagnose a failure with an uncertain cause | `zz-debugger` |
| Build one bounded piece of an approved design | `zz-implementer` |
| Challenge an important plan, diff, or completion claim | `zz-vetter` x3 |

Use agents deliberately, not as a mandatory pipeline. A small, obvious change
may need none of them.

### Role rules

**`zz-readagent`** is an optional read-only factual scout. Use it when isolated
discovery saves parent context, not when a direct lookup is cheaper. Critical
returned ranges still require parent inspection.

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

**`zz-brainstormer`** is read-only. Call it before design when multiple
approaches have meaningful consequences. Give it the problem, constraints, and
relevant paths. The parent or user selects an approach.

**`zz-designplanner`** is read-only. Give it exactly one explicitly selected
solution. It returns a staged, implementation-ready design, not code.

**`zz-debugger`** is read-only. Use it before editing when a failure's cause is
uncertain. Include the failure, reproduction command, output, and relevant
paths. The parent decides whether to apply its recommended fix.

**`zz-implementer`** is the only agent that edits files. Before calling it:

1. Create a non-empty implementation document under
   `docs/artifacts/implementationdocs/` with context, approved design,
   invariants, touchpoints, stages, acceptance criteria, risks, and validation.
2. Assign exactly one medium-to-small, independently reviewable piece with
   focused acceptance criteria and validation.
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

- Only `zz-implementer` may write files.
- No agent performs git mutations.
- Every agent receives explicit paths, symbols, constraints, and prior findings;
  agents start without the parent's conversation context.
<!-- zz-copilot-agents:end -->
