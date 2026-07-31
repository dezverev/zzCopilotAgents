# Implementation ledger: add-zz-readagent

Implementation document: `docs/artifacts/implementationdocs/add-zz-readagent.md`

<!-- zz-implementer-run:start -->
## Piece
Create the native `zz-readagent` profile and its structural contract test.

## Status
completed

## Reported confidence
87%

## Progress
- 2026-07-30T20:03:16-07:00 — Confirmed Stage 1 is one independently testable profile-and-contract-test outcome and inspected the approved design plus existing agent conventions.
- 2026-07-30T20:10:02-07:00 — Created the profile and standard-library structural test; the first test run exposed a whitespace-sensitive assertion for a wrapped phrase.
- 2026-07-30T20:12:21-07:00 — Normalized whitespace in the affected structural assertion and completed all focused validation successfully.

## Confidence checkpoints
- confidence: initial — 90% — The approved design specifies exact profile metadata, dispatch/report contracts, boundaries, test scope, and focused validation.
- confidence: milestone-1 — 87% — Profile and test cover the contract, but the initial suite failed because one assertion did not normalize Markdown line wrapping.
- confidence: milestone-2 — 95% — All seven structural tests pass after making the assertion insensitive to prose wrapping, and diff checks are clean.
- confidence: final — 95% — The owned profile and test satisfy every Stage 1 criterion, both required validation commands pass, and the implementation document is unchanged.

## Files changed
- docs/artifacts/implementationdocs/ledgers/add-zz-readagent.ledger.md — created the required append-only run record.
- .github/agents/zz-readagent.agent.md — added the native factual-scout profile and its dispatch, report, citation, refusal, and capability boundaries.
- tests/agents/test_readagent_profile.py — added a standard-library parser and seven structural contract tests.

## Validation
- `git --no-pager status --short && grep -RIn "^name:\|^tools:\|## Answer\|Question:" .github/agents tests/agents | head -120` — passed; located existing profile conventions and confirmed `tests/agents` was initially absent.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/agents -p 'test_*.py'` — failed: 7 tests ran; the fixed-model assertion did not tolerate a Markdown line break.
- `git --no-pager diff --check` — passed with no output.
- `git --no-pager diff -- docs/artifacts/implementationdocs/add-zz-readagent.md; git --no-pager status --short -- .github/agents/zz-readagent.agent.md tests/agents/test_readagent_profile.py docs/artifacts/implementationdocs/ledgers/add-zz-readagent.ledger.md` — passed; implementation document had no diff and only the three owned files were reported.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/agents -p 'test_*.py'` — passed: 7 tests ran, OK.
- `git --no-pager diff --check` — passed with no output.
- ledger delimiter check using `python3` standard library — passed: exactly one start and one end delimiter.
- Final `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/agents -p 'test_*.py'` — passed: 7 tests ran, OK.
- Final `git --no-pager diff --check` — passed with no output.
- Final implementation-document diff and owned-file status check — passed; the document remains unchanged and only the three owned files were reported.
- Final ledger protocol check using `python3` standard library — passed: required sections occur once, initial/final checkpoints exist, and reported confidence equals the 87% minimum.

## Decisions and deviations
- Used a small regular-expression frontmatter parser plus `ast.literal_eval` so the test remains standard-library-only; normalized prompt whitespace only where line wrapping is not a contract invariant.

## Remaining work
- Stage 2 parent delegation integration and Stage 3 distribution documentation remain for later pieces.

## Blockers
- None.
<!-- zz-implementer-run:end -->

<!-- zz-implementer-run:start -->
## Piece
Integrate `zz-readagent` into the repository parent delegation contract.

## Status
completed

## Reported confidence
89%

## Progress
- 2026-07-30T20:07:08-07:00 — Confirmed Stage 2 is one coherent, independently vettable parent-contract update with explicit acceptance criteria and focused static validation; inspected the approved design, current parent instructions, prior ledger, and working-tree status.
- 2026-07-30T20:14:31-07:00 — Updated the parent contract to register the sixth role, define optional free-text scout dispatch, require parent reinspection, and preserve specialist ownership plus write/git boundaries.
- 2026-07-30T20:17:04-07:00 — Initial static assertion found a whitespace-sensitive phrase check across a Markdown line wrap; the required language is present and direct inspection remained sound.
- 2026-07-30T20:18:46-07:00 — Re-ran normalized static inspection successfully and confirmed no stale five-role wording or whitespace errors.

## Confidence checkpoints
- confidence: initial — 92% — The approved Stage 2 design and piece criteria precisely define the sole owned contract file, dispatch fields, role boundaries, and validation.
- confidence: milestone-1 — 95% — Direct inspection confirms the parent instructions now contain all six table roles, the exact dispatch labels, optionality guidance, reinspection requirement, and unchanged ownership boundaries.
- confidence: milestone-2 — 89% — The first static script failed only because it did not normalize prose line wrapping; `diff --check` passed and direct inspection confirms the asserted boundary text.
- confidence: milestone-3 — 96% — Normalized static assertions and focused line-number inspection pass for every Stage 2 acceptance boundary.
- confidence: final — 96% — All requested validation now passes, the implementation document is unchanged, and changes remain limited to the parent contract plus this append-only ledger record.

## Files changed
- docs/artifacts/implementationdocs/ledgers/add-zz-readagent.ledger.md — appended this required Stage 2 run record.
- .github/copilot-instructions.md — integrated `zz-readagent` into the parent role-selection and mandatory delegation contract.

## Validation
- `git status --short && git --no-pager grep -n -E "five|role-selection|zz-(implementer|vetter|designer)|Mandatory|subagent|git" -- .github/copilot-instructions.md docs/artifacts/implementationdocs/add-zz-readagent.md` — inspection partially completed; status exposed extensive pre-existing worktree changes, while grep exited 1 because the relevant files are untracked and therefore outside `git grep`.
- Initial focused Python static assertions — failed because the literal `bug hunting or diagnosis` assertion did not normalize a Markdown line wrap; all preceding assertions passed.
- `git --no-pager diff --check` — passed with no output.
- Focused grep evidence command — not run because the shell-security guard rejected Markdown backticks in the command; no repository or environment change occurred.
- Normalized focused Python static assertions — passed: six table roles, all dispatch fields, optionality, parent reinspection, specialist self-grounding/ownership, and write/git boundaries confirmed.
- `grep -nE 'Six registered|zz-readagent|Question:|skip it|critical returned|Every specialist|never performs|Only .*may write|No subagent performs git' .github/copilot-instructions.md` — passed; printed the required contract evidence at lines 11, 22, 31, 40-49, 68-71, and 139-140.
- `grep -nE 'Five registered|all five|other four|nested delegation' .github/copilot-instructions.md; git --no-pager diff --check` — passed; no stale or nested-delegation wording was found and diff check emitted no errors.
- Final `git --no-pager diff --check` — passed with no output.
- Final implementation-document diff and owned-path status inspection — passed; the implementation document emitted no diff and the expected untracked owned paths were reported.
- Final ledger lifecycle protocol check using Python standard library — passed: the second run record has every required section exactly once, contains initial/final checkpoints, and reports its 89% minimum checkpoint.

## Decisions and deviations
- Kept the existing parent delegation prose and added an explicit statement that the parent remains the delegator rather than introducing any nested-delegation model.

## Remaining work
- Stage 3 distribution documentation remains for a later piece.

## Blockers
- None.
<!-- zz-implementer-run:end -->

<!-- zz-implementer-run:start -->
## Piece
Synchronize public distribution documentation for the sixth native `zz-readagent` role.

## Status
completed

## Reported confidence
93%

## Progress
- 2026-07-30T20:11:27-07:00 — Confirmed Stage 3 is one coherent documentation-sync outcome with explicit acceptance criteria and focused validation; inspected the approved design, all three owned public documents, active package guidance, prior ledger records, and working-tree status.
- 2026-07-30T20:19:08-07:00 — Updated all three public documents with the sixth-role inventory, scout contract and boundaries, inherited-model behavior, runtime distinction, and prompt-level enforcement scope; focused stale-claim and whitespace searches passed.
- 2026-07-30T20:22:11-07:00 — Both required test suites passed, the existing implementer hook JSON parsed successfully, and final diff/integrity checks were prepared.
- 2026-07-30T20:24:03-07:00 — Corrected the new run record's placement so the pre-existing ledger remains an exact prefix, then repeated the final ledger and integrity checks.

## Confidence checkpoints
- confidence: initial — 93% — The approved design precisely specifies the three documentation touchpoints, required role/model/runtime/contract claims, and validation commands.
- confidence: milestone-1 — 96% — Direct inspection and focused searches confirm all public docs now consistently cover the sixth role without stale five-role or four-read-only claims, and `diff --check` passes.
- confidence: milestone-2 — 97% — All 7 agent tests and all 24 implementer hook tests pass, the hook JSON parses, and the required diff check is clean.
- confidence: milestone-3 — 93% — A final protocol check exposed that the new record had been inserted between prior records; relocating the unchanged record to the end restores the required pre-run byte prefix.
- confidence: final — 97% — Every Stage 3 documentation criterion is represented in the owned docs and all focused validation passes without changing the implementation document.

## Files changed
- docs/artifacts/implementationdocs/ledgers/add-zz-readagent.ledger.md — appended this required Stage 3 run record.
- README.md — updated the shipped-role table, scout overview and contract, model/runtime boundaries, and six-agent verification wording.
- docs/copilot-native-agents.md — documented the native scout design, handoff, tool boundary, model mediation, and absence of readagent hook enforcement.
- PORTING.md — synchronized the migration record to six roles, five read-only roles, and the native scout's contract and runtime distinction.

## Validation
- `git status --short; sha256sum docs/artifacts/implementationdocs/add-zz-readagent.md; grep -RInE 'five (profiles|agents|roles)|four read-only|zz-readagent|readsubagent' README.md PORTING.md docs/copilot-native-agents.md .github` — passed for initial inspection; identified stale five-role and four-read-only claims in owned public docs, confirmed active role guidance, and recorded implementation-document hash `f7357f98bcde411060b093433e472935c5a3d55e4258f59b95ddbde20b0d3e3d`.
- Focused stale-count, readagent-coverage, and active-guidance grep plus `git --no-pager diff --check` — passed; no contradictory five-role/four-read-only/no-readagent public claim remains, required contract terms are present, and whitespace validation emitted no errors.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/agents -p 'test_*.py'` — passed: 7 tests ran, OK.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/hooks -p 'test_*.py'` — passed: 24 tests ran, OK.
- Python `json.loads` parse of `.github/hooks/zz-implementer.json` — passed: object keys are `hooks` and `version`.
- `git --no-pager diff --check` — passed with no output.
- Initial final ledger protocol assertion — failed because it inspected the prior Stage 2 record after the Stage 3 record had been inserted before it; this exposed and prompted correction of the append position.
- Corrected final ledger protocol assertion — passed: the latest record is completed, has each required section once, includes initial/final checkpoints, and reports its 93% minimum.
- Final `git --no-pager diff --check` and implementation-document SHA-256 assertion — passed; no whitespace errors and the document remains byte-identical at `f7357f98bcde411060b093433e472935c5a3d55e4258f59b95ddbde20b0d3e3d`.

## Decisions and deviations
- None.

## Remaining work
- None.

## Blockers
- None.
<!-- zz-implementer-run:end -->

<!-- zz-implementer-run:start -->
## Piece
Correct distribution documentation claims about runtime requirements, ledger suffix validation, model configuration, and outstanding live verification.

## Status
completed

## Reported confidence
90%

## Progress
- 2026-07-30T20:21:37-07:00 — Confirmed the correction set is one coherent, independently vettable documentation outcome with explicit acceptance criteria and focused validation; inspected the approved design, owned documents, cumulative ledger, and working-tree status.
- 2026-07-30T20:28:12-07:00 — Corrected all three public documents; direct inspection and focused search confirm the runtime, cumulative-ledger suffix, CLI model controls, cautious portability, and live-verification wording.
- 2026-07-30T20:31:04-07:00 — Both standard-library suites passed, hook JSON parsed, stale-claim searches and diff checks were clean, and final integrity inspection confirmed the implementation document is unchanged.

## Confidence checkpoints
- confidence: initial — 94% — The requested corrections identify exact claims, owned files, cautious model wording, required validation, and runtime checks that must remain outstanding.
- confidence: milestone-1 — 96% — All requested documentation claims are now present consistently, stale inheritance wording is absent, and the initial diff check is clean.
- confidence: milestone-2 — 90% — The initial ledger patch landed before later records rather than at EOF; relocating the unchanged run record restored the complete pre-run ledger as an exact prefix.
- confidence: milestone-3 — 97% — All 7 agent tests and all 24 hook tests pass, hook JSON parses, stale-claim searches are empty, and whitespace validation is clean.
- confidence: final — 97% — Every documentation correction is directly inspected, all requested focused validation passes, and unperformed live checks are explicitly retained as runtime work.

## Files changed
- docs/artifacts/implementationdocs/ledgers/add-zz-readagent.ledger.md — appended this required correction run record.
- README.md — narrowed the runtime claim, corrected suffix lifecycle wording, documented both test suites and live checks, and grounded model controls cautiously.
- PORTING.md — replaced broad inheritance claims with current CLI controls and client/runtime caveats.
- docs/copilot-native-agents.md — documented unpinned profiles, current CLI controls, and limits on cross-runtime inheritance claims.

## Validation
- Initial `git status --short` and focused documentation grep — passed; located the package-runtime, model, ledger, and verification wording requiring correction and confirmed pre-existing worktree changes.
- Focused corrected-claim grep and `git --no-pager diff --check` — passed; required runtime, `/model`, `/subagents`, live-dispatch, and suffix wording is present with no whitespace errors.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/agents -p 'test_*.py'` — passed: 7 tests ran, OK.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/hooks -p 'test_*.py'` — passed: 24 tests ran, OK.
- Python `json.loads` parse of `.github/hooks/zz-implementer.json` — passed: keys are `hooks` and `version`, with 3 hook groups.
- `git --no-pager diff --check` — passed with no output.
- Final ledger-order, implementation-document SHA-256, and owned-path status inspection — passed; this is the fourth and final ledger record, and the implementation document remains byte-identical at `f7357f98bcde411060b093433e472935c5a3d55e4258f59b95ddbde20b0d3e3d`.
- Final stale-claim search — passed with no matches for broad inheritance, single-record ledger, or package-wide external-runtime claims.
- Final ledger protocol assertion using Python standard library — passed: four balanced records; the latest has each required section once, initial/final checkpoints, completed status, and reported confidence equal to its 90% minimum.
- Final `git --no-pager diff --check`, implementation-document SHA-256, and stale-claim search — passed; no whitespace errors or stale claims, and the approved document hash remains `f7357f98bcde411060b093433e472935c5a3d55e4258f59b95ddbde20b0d3e3d`.

## Decisions and deviations
- Used explicit Copilot CLI command wording while caveating other clients and cloud runtimes, rather than generalizing CLI semantics beyond current evidence.
- The first ledger insertion matched an earlier delimiter; moved the unchanged new record to EOF before further work so all prior ledger bytes again form the required prefix.

## Remaining work
- In a fresh Copilot CLI session, `/agent`, `/env`, factual/read-plan/refusal dispatches, `/subagents` and `/model` configuration inspection, and representative multi-model behavior remain runtime verification work.

## Blockers
- None.
<!-- zz-implementer-run:end -->
