# Add a Copilot-native `zz-readagent`

## Problem context

The package currently has five specialized Copilot custom agents. Every role can
ground itself with native `read` and `search`, but there is no dedicated scout
whose isolated context absorbs broad factual discovery and returns a compact,
stable, cited read plan. The Qwen-backed `readsubagent` in the related
implementations provides that capability through an external runtime. This
package needs the same useful role without Qwen, MCP, a local model, or a fixed
model choice.

## Selected solution

Add `zz-readagent` as a sixth native Copilot custom agent. Its profile omits the
`model` field so it inherits the model selected through Copilot's native
configuration and UI. It uses exactly the portable `read` and `search` aliases
and acts as an optional isolated-context factual scout.

The role answers repository questions and produces read plans. It does not
review correctness, find bugs, diagnose failures, choose designs, recommend
edits, or implement changes. Existing specialized agents remain independently
self-grounding; the scout is an optimization, not a hidden dependency.

## Architecture and invariants

- Profile path: `.github/agents/zz-readagent.agent.md`.
- Frontmatter name: `zz-readagent`.
- Tools: exactly `read` and `search`.
- No `model` field. Copilot's active model selection controls execution.
- No `execute`, `edit`, filesystem mutation, git operation, MCP tool, Qwen,
  local-model service, or external runtime.
- Locate before reading, then read only the ranges needed to verify the answer.
- Every repository factual claim is backed by an inspected repository-relative
  `path:line` or `path:start-end` citation.
- The scout may follow one relevant reference beyond supplied scope when needed
  and must disclose that expansion.
- Prohibited judgment is refused rather than silently answered. Neutral factual
  evidence and locations may still be returned.
- The implementer lifecycle hook configuration, verifier, and tests are outside
  this feature's modification scope.

## Dispatch contract

The parent supplies one required factual or read-planning question:

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

Only `Question:` is required. Review, correctness and safety judgments, bug
hunting, root-cause diagnosis, recommendations, refactoring or edit strategy,
implementation planning, and design selection are out of scope.

## Report contract

Reports use these headings:

1. `## Answer` first, containing the direct factual answer or read-plan summary.
2. `## Subsystem map`, with 2-5 compact bullets.
3. `## Focused read list`, normally the smallest useful 3-6 paths or ranges.
4. `## Anchors`, containing useful symbols, searches, routes, keys, or ranges.
5. `## Avoid for now` only when useful.
6. `## Uncertainty` only when evidence is incomplete.
7. `## Out of scope` only when requested judgment was refused.

The report contains no whole-file dumps, raw search output, speculative
findings, patches, implementation advice, or invented citations.

## Stages

### Stage 1: Native profile and structural contract test

Create the profile and a standard-library test that checks stable structural
invariants: exact tools, absent model field, required headings and citation
rule, explicit role refusals, and absence of external-runtime dependencies.

Touchpoints:

- `.github/agents/zz-readagent.agent.md`
- `tests/agents/test_readagent_profile.py`

Validation:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/agents -p 'test_*.py'`
- `git --no-pager diff --check`

### Stage 2: Parent delegation integration

Update `.github/copilot-instructions.md` from five to six roles. Add the scout
to role selection and define its dispatch contract. Keep it optional, preserve
parent factual grounding, preserve independent grounding by all specialist
roles, and do not authorize nested delegation.

Touchpoint:

- `.github/copilot-instructions.md`

Validation:

- Static inspection for the six-role count, dispatch fields, optional usage,
  unchanged specialist ownership, and write/git boundaries.
- `git --no-pager diff --check`

### Stage 3: Distribution documentation

Synchronize the role table, installation and verification count, model
inheritance, no-external-runtime statement, and prompt-level enforcement scope.

Touchpoints:

- `README.md`
- `docs/copilot-native-agents.md`
- `PORTING.md`

Validation:

- Search for stale five-role/four-read-only counts and contradictions.
- Run the profile test and existing implementer verifier suite.
- Parse the existing hook JSON and run `git diff --check`.

## Risks and unknowns

- Prompt adherence can vary across user-selected models; the structural profile
  test cannot prove behavioral compliance.
- Copilot lifecycle payload evidence does not currently establish a reliable
  pre-dispatch question payload, so no readagent format hook is added.
- Citation quality depends on the native read surface exposing usable line
  information. The agent must report uncertainty instead of inventing ranges.
- Copilot client wording for model selection varies; documentation must not
  invent an unverified command name.

## Acceptance criteria

- Six discoverable `zz-*` profiles ship, including `zz-readagent`.
- `zz-readagent` has exactly `read` and `search` and no `model` field.
- It requires the dispatch and report contracts above.
- It refuses specialist judgments and cannot execute or edit.
- It requires no Qwen, MCP, local model, network service, or external runtime.
- Parent guidance and public documentation consistently describe the optional
  scout and inherited native model selection.
- Existing roles continue to self-ground and retain their existing boundaries.
- Existing implementer hooks and verifier behavior remain unchanged.
- Focused profile and implementer verifier tests pass.

## Verification plan

After all stages, restart Copilot CLI and confirm six profiles through the
native agent menu. Dispatch a factual question, a read-planning question, and a
prohibited review question. Confirm the report shape and citations, refusal
behavior, and inherited model selection. Repeat representative checks with a
second available model when practical.
