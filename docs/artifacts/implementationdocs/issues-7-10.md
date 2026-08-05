# Issues 7-10 implementation

## Context

Issues #7-#10 tighten two related user-facing contracts:

- installation must verify the hook runtime before copying runtime files and
  must keep contributor tests outside the consumer installation flow; and
- delegation guidance must let the parent make small edits directly while
  guarding the original user-requested scope from unapproved expansion.

## Approved design

Keep the existing copy-based installation model. Add explicit, platform-specific
Python 3.10 preflight commands and tell users to stop if the command is missing
or too old. Define `.github/` as the runtime payload and move source test
commands under contributor-only wording.

In the synchronized parent contract, distinguish the parent from delegated
agents: the parent may directly perform small, localized, low-risk edits,
including focused vetter follow-ups. `zz-implementer` remains the sole
write-capable delegated role and is reserved for bounded approved-design work
that warrants an implementation document and ledger. Add an original-ask scope
guard that requires user clarification or permission before material expansion.
Make the implementer stop and escalate rather than absorb newly discovered
out-of-scope work.

## Invariants

- `AGENTS.md` and `.github/copilot-instructions.md` retain byte-identical marked
  delegation blocks.
- The five specialist roles documented as read-only remain read-only.
- The parent retains decomposition, sequencing, review, integration, final
  verification, and all git operations.
- Hook runtime remains Python 3.10 or newer; hook behavior is unchanged.
- The implementation document is read-only during implementer runs.

## Touchpoints

- `README.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agents/zz-implementer.agent.md`
- `docs/copilot-native-agents.md`
- `tests/agents/`

## Stages

1. Update and contract-test the consumer installation guidance for issues #7
   and #8.
2. Update the synchronized parent contract, implementer escalation behavior,
   supporting design documentation, and policy tests for issues #9 and #10.
3. Apply focused vetter feedback by narrowing delegated scope enforcement to
   the implementer and aligning scope-blocked reports with the existing
   low-confidence clarification contract.

## Acceptance criteria

### Stage 1

- Linux/macOS and Windows preflight commands verify Python 3.10 or newer before
  hook installation.
- Instructions explicitly stop installation when Python is unavailable or too
  old and provide actionable PATH/install guidance.
- Consumer installation copies only required `.github/` runtime content.
- Development tests are clearly contributor-only and are neither copied nor
  run as installation steps.

### Stage 2

- The parent may directly make small, localized, low-risk edits, including
  focused fixes from vetter feedback.
- Deeper approved-design work that warrants a document and ledger is delegated
  as one bounded piece to `zz-implementer`.
- Read-only delegated roles remain read-only.
- The original ask is the scope baseline throughout implementation.
- Material increases in features, subsystems, dependencies, migrations, risk,
  or delivery effort require user clarification or permission before work
  proceeds.
- A delegated implementer stops and escalates newly discovered out-of-scope
  work rather than implementing it opportunistically.

### Stage 3

- The shared contract does not require read-only specialists that lack the
  original ask to enforce the implementation scope boundary.
- A material or ambiguous scope boundary makes the implementer record
  confidence below 80%, return blocked, and provide clarification, which
  matches the verifier's existing fail-closed report contract.
- Focused agent tests and the complete hook suite pass.

## Risks

- Ambiguous wording could accidentally grant write access to read-only
  specialists; name the parent and delegated implementer separately.
- Scope language could force approval for every tightly coupled correctness
  fix; distinguish those from material expansion while requiring clarification
  when uncertain.
- Documentation-only installation checks can drift; add focused contract tests
  without testing prose more narrowly than necessary.

## Validation

- `python3 -m unittest discover -s tests/agents -p 'test_*.py'`
- `python3 -m unittest discover -s tests/hooks -p 'test_*.py'`
- Confirm the marked blocks in `AGENTS.md` and
  `.github/copilot-instructions.md` are byte-identical through the existing
  parent-contract test.
