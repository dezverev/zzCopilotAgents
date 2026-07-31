import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "hooks"
    / "scripts"
    / "verify-implementer.py"
)
SPEC = importlib.util.spec_from_file_location("verify_implementer", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        (self.repo / ".git").mkdir()
        self.docs = self.repo / "docs/artifacts/implementationdocs"
        self.ledgers = self.docs / "ledgers"
        self.ledgers.mkdir(parents=True)
        (self.docs / "design.md").write_bytes(b"# immutable\n")
        self.state = base / "state"
        self.environment = mock.patch.dict(
            os.environ, {verifier.STATE_ENV: str(self.state)}, clear=False
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temporary.cleanup)
        self.session = "session-1"

    def payload(self, **values):
        payload = {
            "sessionId": self.session,
            "cwd": str(self.repo),
            "agentName": verifier.AGENT,
        }
        payload.update(values)
        return payload

    def start(self):
        result = verifier.start(self.payload())
        self.assertEqual({"decision": "allow"}, result)

    def pre_tool_payload(self, path, **values):
        payload = {
            "sessionId": self.session,
            "cwd": str(self.repo),
            "toolName": "edit",
            "toolArgs": {"filePath": path},
        }
        payload.update(values)
        return payload

    def response(self, status="completed", confidence=90, ledger=None, extras=""):
        ledger = ledger or "docs/artifacts/implementationdocs/ledgers/run.ledger.md"
        return (
            f"## Status\n{status}\n\n"
            f"## Confidence\n{confidence}%\n\n"
            f"{extras}"
            f"## Ledger\n{ledger}\n"
        )

    def record(
        self,
        status="completed",
        confidence=90,
        checkpoints=(94, 90),
        ordinal=1,
        progress="- step-1 — implemented verifier",
        checkpoint_lines=None,
    ):
        checkpoint_lines = checkpoint_lines or (
            f"- confidence: initial — {checkpoints[0]}% — grounded in design\n"
            f"- confidence: final — {checkpoints[1]}% — validation passed"
        )
        return (
            "# Ledger\n\n"
            f"{verifier.START_MARKER}\n"
            f"## Run ordinal\n{ordinal}\n\n"
            f"## Status\n{status}\n\n"
            f"## Reported confidence\n{confidence}%\n\n"
            f"## Progress\n{progress}\n\n"
            "## Confidence checkpoints\n"
            f"{checkpoint_lines}\n\n"
            "## Validation\n- unittest — pass\n"
            f"{verifier.END_MARKER}\n"
        )

    def write_ledger(self, text=None, name="run.ledger.md"):
        path = self.ledgers / name
        path.write_text(text if text is not None else self.record(), encoding="utf-8")
        return path

    def assert_blocked(self, result, phrase=None):
        self.assertEqual("block", result["decision"])
        if phrase:
            self.assertIn(phrase, result["reason"])

    def classify(self, path):
        return verifier.classify_managed_path(self.repo, path)

    def make_repository(self, base):
        repo = base / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        docs = repo / verifier.DOC_ROOT
        ledgers = repo / verifier.LEDGER_ROOT
        ledgers.mkdir(parents=True)
        (docs / "design.md").write_bytes(b"# immutable\n")
        return repo, docs, ledgers

    def redirect_managed_ancestor(self, base, repo, relative):
        ancestor = repo / relative
        external = base / ("external-" + "-".join(Path(relative).parts))
        ancestor.rename(external)
        ancestor.symlink_to(external, target_is_directory=True)

    def test_classifier_recognizes_recursive_documents_and_ledger_precedence(self):
        cases = {
            "docs/artifacts/implementationdocs/direct.md": verifier.ZONE_DOCUMENT,
            "docs/artifacts/implementationdocs/deep/tree/design.MD": verifier.ZONE_DOCUMENT,
            "docs/artifacts/implementationdocs/deep/tree/design.txt": verifier.ZONE_UNMANAGED,
            "docs/artifacts/implementationdocs/ledgers/nested/design.md": verifier.ZONE_LEDGER,
            "docs/artifacts/implementationdocs/ledgers/nested/data.bin": verifier.ZONE_LEDGER,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(expected, self.classify(path))

    def test_classifier_uses_component_safe_containment_and_normalized_paths(self):
        cases = {
            "src/design.md": verifier.ZONE_UNMANAGED,
            "docs/artifacts/implementationdocs-other/design.md": verifier.ZONE_UNMANAGED,
            "docs/artifacts/implementationdocs/ledgers-other/design.md": verifier.ZONE_DOCUMENT,
            "docs/artifacts/implementationdocs/ledgers/../nested/design.md":
                verifier.ZONE_DOCUMENT,
            "docs/artifacts/implementationdocs/nested/../ledgers/run.txt":
                verifier.ZONE_LEDGER,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(expected, self.classify(path))

    def test_classifier_allows_missing_managed_roots(self):
        self.ledgers.rmdir()
        (self.docs / "design.md").unlink()
        self.docs.rmdir()

        self.assertEqual(
            verifier.ZONE_DOCUMENT,
            self.classify("docs/artifacts/implementationdocs/nested/design.md"),
        )
        self.assertEqual(
            verifier.ZONE_LEDGER,
            self.classify("docs/artifacts/implementationdocs/ledgers/new/run.txt"),
        )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_classifier_rejects_symlinks_at_every_managed_level(self):
        scenarios = ("managed-root", "managed-directory", "managed-file",
                     "ledger-directory", "ledger-file")
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory() as temporary:
                    repo = Path(temporary) / "repo"
                    repo.mkdir()
                    docs = repo / verifier.DOC_ROOT
                    ledgers = repo / verifier.LEDGER_ROOT
                    target = repo / "targets"
                    target.mkdir()
                    if scenario == "managed-root":
                        docs.parent.mkdir(parents=True)
                        docs.symlink_to(target, target_is_directory=True)
                        candidate = docs / "design.md"
                    else:
                        ledgers.mkdir(parents=True)
                        if scenario == "managed-directory":
                            link = docs / "nested"
                            link.symlink_to(target, target_is_directory=True)
                            candidate = link / "design.md"
                        elif scenario == "managed-file":
                            destination = target / "design.md"
                            destination.touch()
                            candidate = docs / "design.md"
                            candidate.symlink_to(destination)
                        elif scenario == "ledger-directory":
                            link = ledgers / "nested"
                            link.symlink_to(target, target_is_directory=True)
                            candidate = link / "run.txt"
                        else:
                            destination = target / "run.txt"
                            destination.touch()
                            candidate = ledgers / "run.txt"
                            candidate.symlink_to(destination)
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.classify_managed_path(repo, candidate)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_classifier_rejects_aliases_crossing_managed_boundaries(self):
        outside_alias = self.repo / "document-alias.md"
        outside_alias.symlink_to(self.docs / "design.md")
        with self.assertRaisesRegex(verifier.VerificationError, "boundary"):
            self.classify(outside_alias)

        external = self.repo / "external"
        external.mkdir()
        managed_alias = self.docs / "external"
        managed_alias.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
            self.classify(managed_alias / "design.md")

        internal = self.docs / "internal"
        internal.mkdir()
        traversal_alias = self.docs / "traversal"
        traversal_alias.symlink_to(internal, target_is_directory=True)
        with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
            self.classify(traversal_alias / ".." / "design.md")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_classifier_rejects_managed_root_ancestor_symlinks(self):
        for relative in ("docs", "docs/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    repo, docs, _ = self.make_repository(base)
                    self.redirect_managed_ancestor(base, repo, relative)
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.classify_managed_path(repo, docs / "design.md")

    def test_non_implementer_events_are_noops(self):
        payload = self.payload(agentName="other")
        self.assertEqual({"decision": "allow"}, verifier.start(payload))
        self.assertEqual({}, verifier.pre_tool(payload))
        self.assertEqual({"decision": "allow"}, verifier.stop(payload))
        self.assertFalse(self.state.exists())

    def test_start_snapshots_outside_repo_and_rejects_concurrent_start(self):
        self.start()
        self.assertTrue(self.state.is_dir())
        self.assertFalse(str(self.state).startswith(str(self.repo)))
        files = list(self.state.iterdir())
        self.assertEqual(2, len(files))
        self.assert_blocked_from_exception(verifier.start, self.payload(), "already active")

    def test_failed_start_closes_marker_before_cleanup_and_allows_retry(self):
        marker, run_file = verifier.paths_for(self.repo.resolve(), self.session)
        original_open = os.open
        original_close = os.close
        original_unlink = Path.unlink
        original_write_private_state = verifier.write_private_state
        marker_descriptor = None
        events = []

        def tracking_open(path, flags, mode=0o777):
            nonlocal marker_descriptor
            descriptor = original_open(path, flags, mode)
            if Path(path) == marker:
                marker_descriptor = descriptor
            return descriptor

        def tracking_close(descriptor):
            if descriptor == marker_descriptor:
                events.append("close-marker")
            return original_close(descriptor)

        def tracking_unlink(path, *args, **kwargs):
            if path == marker:
                self.assertEqual(["close-marker"], events)
                events.append("unlink-marker")
            return original_unlink(path, *args, **kwargs)

        def failing_write_private_state(path, value):
            original_write_private_state(path, value)
            raise RuntimeError("forced")

        with (
            mock.patch.object(verifier.os, "open", side_effect=tracking_open),
            mock.patch.object(verifier.os, "close", side_effect=tracking_close),
            mock.patch.object(Path, "unlink", tracking_unlink),
            mock.patch.object(
                verifier, "write_private_state", side_effect=failing_write_private_state
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "forced"):
                verifier.start(self.payload())

        self.assertEqual(["close-marker", "unlink-marker"], events)
        self.assertFalse(marker.exists())
        self.assertFalse(run_file.exists())

        self.start()
        self.assertTrue(marker.exists())
        self.assertTrue(run_file.exists())

    def test_snapshot_recursively_separates_documents_and_all_regular_ledgers(self):
        nested = self.docs / "z/deep"
        nested.mkdir(parents=True)
        (nested / "upper.MD").write_bytes(b"upper")
        (nested / "ignored.txt").write_bytes(b"ignored")
        ledger_dir = self.ledgers / "a/deep"
        ledger_dir.mkdir(parents=True)
        (ledger_dir / "notes.MD").write_bytes(b"ledger markdown")
        (ledger_dir / "opaque.bin").write_bytes(b"opaque")

        documents, ledgers = verifier.snapshot(self.repo)

        self.assertEqual(
            [
                "docs/artifacts/implementationdocs/design.md",
                "docs/artifacts/implementationdocs/z/deep/upper.MD",
            ],
            list(documents),
        )
        self.assertEqual(
            [
                "docs/artifacts/implementationdocs/ledgers/a/deep/notes.MD",
                "docs/artifacts/implementationdocs/ledgers/a/deep/opaque.bin",
            ],
            list(ledgers),
        )

    def test_snapshot_missing_managed_roots_is_empty(self):
        (self.docs / "design.md").unlink()
        self.ledgers.rmdir()
        self.docs.rmdir()

        self.assertEqual(({}, {}), verifier.snapshot(self.repo))

    def test_snapshot_and_start_reject_existing_non_directory_document_root(self):
        (self.docs / "design.md").unlink()
        self.ledgers.rmdir()
        self.docs.rmdir()
        self.docs.write_bytes(b"not a directory")

        with self.assertRaisesRegex(verifier.VerificationError, "not a directory"):
            verifier.snapshot(self.repo)
        with self.assertRaisesRegex(verifier.VerificationError, "not a directory"):
            verifier.start(self.payload())

    def test_snapshot_and_start_reject_regular_file_document_ancestors(self):
        for relative in ("docs", "docs/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    repo, _, _ = self.make_repository(base)
                    ancestor = repo / relative
                    ancestor.rename(base / "former-ancestor")
                    ancestor.write_bytes(b"not a directory")

                    with self.assertRaisesRegex(
                        verifier.VerificationError, "not a directory"
                    ):
                        verifier.snapshot(repo)
                    with self.assertRaisesRegex(
                        verifier.VerificationError, "not a directory"
                    ):
                        verifier.start(self.payload(cwd=str(repo)))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_snapshot_and_start_reject_dangling_document_ancestor_symlinks(self):
        for relative in ("docs", "docs/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    repo, _, _ = self.make_repository(base)
                    ancestor = repo / relative
                    ancestor.rename(base / "former-ancestor")
                    ancestor.symlink_to(base / "missing", target_is_directory=True)

                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.snapshot(repo)
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.start(self.payload(cwd=str(repo)))

    def test_snapshot_and_start_reject_regular_file_ledger_root(self):
        self.ledgers.rmdir()
        self.ledgers.write_bytes(b"not a directory")

        with self.assertRaisesRegex(verifier.VerificationError, "not a directory"):
            verifier.snapshot(self.repo)
        with self.assertRaisesRegex(verifier.VerificationError, "not a directory"):
            verifier.start(self.payload())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_snapshot_and_start_reject_dangling_ledger_root_symlink(self):
        self.ledgers.rmdir()
        self.ledgers.symlink_to(
            Path(self.temporary.name) / "missing-ledgers", target_is_directory=True
        )

        with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
            verifier.snapshot(self.repo)
        with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
            verifier.start(self.payload())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_snapshot_and_start_reject_managed_root_ancestor_symlinks(self):
        for relative in ("docs", "docs/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    repo, _, _ = self.make_repository(base)
                    self.redirect_managed_ancestor(base, repo, relative)
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.snapshot(repo)
                    payload = self.payload(cwd=str(repo))
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.start(payload)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_start_rejects_symlinks_anywhere_in_managed_tree(self):
        external = self.repo / "external"
        external.mkdir()
        protected = self.docs / "design.md"
        scenarios = {
            "nested-document-directory": (
                self.docs / "nested-link", external, True
            ),
            "ledger-escape": (
                self.ledgers / "escape", external, True
            ),
            "ledger-to-protected-document": (
                self.ledgers / "document-link", protected, False
            ),
        }
        for name, (link, target, is_directory) in scenarios.items():
            with self.subTest(name=name):
                link.symlink_to(target, target_is_directory=is_directory)
                with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                    verifier.start(self.payload())
                link.unlink()

        protected.unlink()
        self.ledgers.rmdir()
        self.docs.rmdir()
        self.docs.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
            verifier.start(self.payload())

    @unittest.skipUnless(os.name == "posix", "POSIX mode assertions unavailable")
    def test_start_makes_existing_state_directory_and_files_private(self):
        self.state.mkdir(mode=0o777)
        os.chmod(self.state, 0o777)
        marker, run_file = verifier.paths_for(self.repo.resolve(), self.session)
        run_file.write_text("stale", encoding="utf-8")
        os.chmod(run_file, 0o666)

        self.start()

        self.assertEqual(0o700, stat.S_IMODE(self.state.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(marker.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(run_file.stat().st_mode))

    def assert_blocked_from_exception(self, function, payload, phrase):
        with self.assertRaisesRegex(verifier.VerificationError, phrase):
            function(payload)

    def test_stop_accepts_new_ledger_and_removes_state(self):
        self.start()
        self.write_ledger()
        result = verifier.stop(self.payload(response=self.response()))
        self.assertEqual({"decision": "allow"}, result)
        self.assertEqual([], list(self.state.iterdir()))

    def test_stop_accepts_append_only_existing_ledger(self):
        path = self.write_ledger("# Previous runs\n")
        self.start()
        path.write_text(path.read_text() + self.record().split("# Ledger\n\n", 1)[1])
        result = verifier.stop(self.payload(response=self.response()))
        self.assertEqual({"decision": "allow"}, result)

    def test_stop_accepts_append_only_nested_ledger(self):
        nested = self.ledgers / "team/runs"
        nested.mkdir(parents=True)
        path = nested / "run.ledger.md"
        path.write_text("# Previous runs\n", encoding="utf-8")
        self.start()
        path.write_text(
            path.read_text(encoding="utf-8")
            + self.record().split("# Ledger\n\n", 1)[1],
            encoding="utf-8",
        )
        response = self.response(
            ledger=(
                "docs/artifacts/implementationdocs/ledgers/"
                "team/runs/run.ledger.md"
            )
        )

        self.assertEqual(
            {"decision": "allow"}, verifier.stop(self.payload(response=response))
        )

    def test_stop_preserves_nested_unreported_ledger_protection(self):
        unreported_dir = self.ledgers / "archive/deep"
        unreported_dir.mkdir(parents=True)
        unreported = unreported_dir / "history.bin"
        unreported.write_bytes(b"baseline")
        self.start()
        self.write_ledger()
        unreported.write_bytes(b"changed")

        self.assert_blocked(self.call_stop(self.response()), "unreported ledger changed")

    def test_stop_accepts_append_to_opaque_legacy_record_with_count_plus_one(self):
        legacy = (
            "# Previous runs\n"
            "Legacy timestamps and bodies are not validated.\n"
            f"{verifier.START_MARKER}\n"
            "## Status\ncompleted\n\n"
            "## Progress\n- 2025-01-01T00:00:00Z old timestamp format\n"
            f"{verifier.END_MARKER}\n"
        )
        path = self.write_ledger(legacy)
        baseline = path.read_bytes()
        self.start()
        suffix = self.record(ordinal=2).split("# Ledger\n\n", 1)[1]
        path.write_text(legacy + suffix, encoding="utf-8")

        self.assertEqual({"decision": "allow"}, verifier.stop(
            self.payload(response=self.response())
        ))
        self.assertEqual(baseline, path.read_bytes()[:len(baseline)])

    def test_baseline_record_count_accepts_preamble_and_complete_legacy_records(self):
        baseline = (
            "arbitrary preamble\n"
            f"inline {verifier.START_MARKER} is content\n"
            f"{verifier.START_MARKER}\nlegacy body\n{verifier.END_MARKER}\n"
            "content between records\n"
            f"{verifier.START_MARKER}\nanything\n{verifier.END_MARKER}\n"
        ).encode()
        self.assertEqual(2, verifier.baseline_record_count(baseline))

    def test_baseline_record_count_rejects_malformed_exact_marker_ordering(self):
        malformed = {
            "orphaned": f"{verifier.END_MARKER}\n",
            "reversed": f"{verifier.END_MARKER}\n{verifier.START_MARKER}\n",
            "nested": (
                f"{verifier.START_MARKER}\n{verifier.START_MARKER}\n"
                f"{verifier.END_MARKER}\n"
            ),
            "unterminated": f"{verifier.START_MARKER}\nlegacy body\n",
            "orphan_after_complete": (
                f"{verifier.START_MARKER}\n{verifier.END_MARKER}\n"
                f"{verifier.END_MARKER}\n"
            ),
        }
        for name, baseline in malformed.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(verifier.VerificationError, "ledger baseline"):
                    verifier.baseline_record_count(baseline.encode())

    def test_record_chronology_rejects_invalid_ordinals(self):
        valid = self.record().split(verifier.START_MARKER, 1)[1]
        invalid = {
            "missing": valid.replace("## Run ordinal\n1\n\n", ""),
            "empty": valid.replace("## Run ordinal\n1", "## Run ordinal\n"),
            "duplicate": valid.replace(
                "## Run ordinal\n1\n\n",
                "## Run ordinal\n1\n\n## Run ordinal\n1\n\n",
            ),
            "zero": valid.replace("## Run ordinal\n1", "## Run ordinal\n0"),
            "negative": valid.replace("## Run ordinal\n1", "## Run ordinal\n-1"),
            "non_decimal": valid.replace("## Run ordinal\n1", "## Run ordinal\none"),
            "wrong": valid.replace("## Run ordinal\n1", "## Run ordinal\n2"),
            "extra_prose": valid.replace("## Run ordinal\n1", "## Run ordinal\n1\nextra"),
        }
        for name, record in invalid.items():
            with self.subTest(name=name):
                with self.assertRaises(verifier.VerificationError):
                    verifier.validate_record_chronology(record, 1)

    def test_record_chronology_accepts_multiple_ordered_progress_steps(self):
        record = self.record(
            progress=(
                "- step-1 — inspected baseline\n"
                "- step-2 — implemented checks\n"
                "- step-3 — ran tests"
            )
        )
        verifier.validate_record_chronology(record, 1)

    def test_record_chronology_rejects_invalid_progress(self):
        cases = {
            "timestamp": "- 2026-07-30T21:58:35Z — implemented",
            "malformed": "- step-one — implemented",
            "duplicate": "- step-1 — first\n- step-1 — again",
            "gap": "- step-1 — first\n- step-3 — third",
            "reordered": "- step-2 — second\n- step-1 — first",
            "empty": "- step-1 — ",
            "extra_prose": "- step-1 — first\nnot a bullet",
            "blank_line": "- step-1 — first\n\n- step-2 — second",
            "wrong_separator": "- step-1 - first",
            "zero": "- step-0 — first",
        }
        for name, progress in cases.items():
            with self.subTest(name=name):
                record = self.record(progress=progress)
                with self.assertRaises(verifier.VerificationError):
                    verifier.validate_record_chronology(record, 1)

    def test_blocked_stop_retains_state_and_can_continue(self):
        self.start()
        result = self.call_stop(self.response())
        self.assert_blocked(result, "does not exist")
        self.assertEqual(2, len(list(self.state.iterdir())))
        self.write_ledger()
        self.assertEqual(
            {"decision": "allow"}, verifier.stop(self.payload(response=self.response()))
        )

    def call_stop(self, response):
        try:
            return verifier.stop(self.payload(response=response))
        except verifier.VerificationError as error:
            return verifier.decision(False, str(error))

    def test_stop_rejects_missing_state_and_document_changes(self):
        self.write_ledger()
        self.assert_blocked(self.call_stop(self.response()), "no start state")
        self.start()
        (self.docs / "design.md").write_text("# changed\n")
        self.assert_blocked(self.call_stop(self.response()), "document changed")

    def test_stop_rejects_added_and_deleted_documents(self):
        self.start()
        self.write_ledger()
        (self.docs / "extra.md").write_text("new")
        self.assert_blocked(self.call_stop(self.response()), "added or removed")

    def test_stop_rejects_nested_document_modification(self):
        nested = self.docs / "area/deep"
        nested.mkdir(parents=True)
        document = nested / "design.MD"
        document.write_bytes(b"baseline")
        self.start()
        self.write_ledger()
        document.write_bytes(b"changed")

        self.assert_blocked(self.call_stop(self.response()), "document changed")

    def test_stop_rejects_nested_document_addition(self):
        nested = self.docs / "area/deep"
        nested.mkdir(parents=True)
        self.start()
        self.write_ledger()
        (nested / "new.md").write_bytes(b"new")

        self.assert_blocked(self.call_stop(self.response()), "added or removed")

    def test_stop_rejects_nested_document_and_containing_directory_deletion(self):
        nested = self.docs / "area/deep"
        nested.mkdir(parents=True)
        document = nested / "design.md"
        document.write_bytes(b"baseline")
        self.start()
        self.write_ledger()
        document.unlink()
        nested.rmdir()

        self.assert_blocked(self.call_stop(self.response()), "added or removed")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_stop_rejects_symlink_introduced_after_start(self):
        self.start()
        self.write_ledger()
        (self.docs / "introduced.md").symlink_to(self.docs / "design.md")

        self.assert_blocked(self.call_stop(self.response()), "symlink")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_stop_rejects_nested_ledger_directory_symlink_introduced_after_start(self):
        self.start()
        self.write_ledger()
        external = self.repo / "external-ledgers"
        external.mkdir()
        (self.ledgers / "nested").symlink_to(external, target_is_directory=True)

        self.assert_blocked(self.call_stop(self.response()), "symlink")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_stop_rejects_managed_ancestor_symlink_introduced_after_start(self):
        self.start()
        self.write_ledger()
        self.redirect_managed_ancestor(
            Path(self.temporary.name), self.repo, "docs/artifacts"
        )

        self.assert_blocked(self.call_stop(self.response()), "symlink")

    def test_stop_rejects_invalid_ledger_paths(self):
        self.start()
        outside = self.repo / "outside.ledger.md"
        outside.write_text(self.record())
        result = self.call_stop(self.response(ledger="outside.ledger.md"))
        self.assert_blocked(result, "not beneath")

    def test_resolve_ledger_accepts_valid_nested_regular_file(self):
        nested = self.ledgers / "team/deep"
        nested.mkdir(parents=True)
        ledger = nested / "run.ledger.md"
        ledger.write_text(self.record(), encoding="utf-8")
        reported = (
            "docs/artifacts/implementationdocs/ledgers/team/deep/run.ledger.md"
        )

        self.assertEqual(
            (ledger, reported), verifier.resolve_ledger(self.repo, reported)
        )

    def test_resolve_ledger_rejects_absolute_traversal_and_cross_zone_paths(self):
        protected = self.docs / "protected.ledger.md"
        protected.write_text(self.record(), encoding="utf-8")
        sibling = self.docs / "ledgers-other"
        sibling.mkdir()
        (sibling / "run.ledger.md").write_text(self.record(), encoding="utf-8")
        invalid = {
            str(self.ledgers / "run.ledger.md"): "repository-relative",
            "docs/artifacts/implementationdocs/ledgers/../protected.ledger.md":
                "repository-relative",
            "docs/artifacts/implementationdocs/protected.ledger.md":
                "not beneath",
            "docs/artifacts/implementationdocs/ledgers-other/run.ledger.md":
                "not beneath",
        }
        for reported, message in invalid.items():
            with self.subTest(reported=reported):
                with self.assertRaisesRegex(verifier.VerificationError, message):
                    verifier.resolve_ledger(self.repo, reported)

    def test_resolve_ledger_preserves_filename_existence_and_regular_file_contract(self):
        directory = self.ledgers / "directory.ledger.md"
        directory.mkdir()
        invalid = {
            "docs/artifacts/implementationdocs/ledgers/run.LEDGER.MD":
                "must end with .ledger.md",
            "docs/artifacts/implementationdocs/ledgers/missing.ledger.md":
                "does not exist",
            "docs/artifacts/implementationdocs/ledgers/directory.ledger.md":
                "does not exist",
        }
        for reported, message in invalid.items():
            with self.subTest(reported=reported):
                with self.assertRaisesRegex(verifier.VerificationError, message):
                    verifier.resolve_ledger(self.repo, reported)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_resolve_ledger_rejects_symlinks_and_cross_zone_aliases(self):
        target = self.repo / "outside.ledger.md"
        target.write_text(self.record(), encoding="utf-8")
        file_link = self.ledgers / "file.ledger.md"
        file_link.symlink_to(target)
        external = self.repo / "external"
        external.mkdir()
        (external / "run.ledger.md").write_text(self.record(), encoding="utf-8")
        directory_link = self.ledgers / "linked"
        directory_link.symlink_to(external, target_is_directory=True)
        protected_link = self.ledgers / "protected.ledger.md"
        protected_link.symlink_to(self.docs / "design.md")
        outside_alias = self.repo / "ledger-alias.ledger.md"
        outside_alias.symlink_to(self.ledgers / "missing.ledger.md")
        invalid = (
            "docs/artifacts/implementationdocs/ledgers/file.ledger.md",
            "docs/artifacts/implementationdocs/ledgers/linked/run.ledger.md",
            "docs/artifacts/implementationdocs/ledgers/protected.ledger.md",
            "ledger-alias.ledger.md",
        )
        for reported in invalid:
            with self.subTest(reported=reported):
                with self.assertRaises(verifier.VerificationError):
                    verifier.resolve_ledger(self.repo, reported)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_resolve_ledger_rejects_managed_root_ancestor_symlinks(self):
        reported = (
            "docs/artifacts/implementationdocs/ledgers/run.ledger.md"
        )
        for relative in ("docs", "docs/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    repo, _, ledgers = self.make_repository(base)
                    (ledgers / "run.ledger.md").write_text(
                        self.record(), encoding="utf-8"
                    )
                    self.redirect_managed_ancestor(base, repo, relative)
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.resolve_ledger(repo, reported)

    def test_stop_rejects_backticked_ledger_path(self):
        self.start()
        self.write_ledger()
        path = "`docs/artifacts/implementationdocs/ledgers/run.ledger.md`"
        self.assert_blocked(self.call_stop(self.response(ledger=path)), "backticks")

    def test_stop_rejects_non_ledger_filename(self):
        self.start()
        self.write_ledger(name="run.md")
        result = self.call_stop(
            self.response(
                ledger="docs/artifacts/implementationdocs/ledgers/run.md"
            )
        )
        self.assert_blocked(result, "must end with .ledger.md")

    def test_stop_rejects_non_append_only_ledger(self):
        path = self.write_ledger("baseline\n")
        self.start()
        path.write_text(self.record())
        self.assert_blocked(self.call_stop(self.response()), "not append-only")

    def test_stop_rejects_malformed_or_duplicate_report_headings(self):
        self.start()
        self.write_ledger()
        duplicate = self.response() + "\n## Status\ncompleted\n"
        self.assert_blocked(self.call_stop(duplicate), "one non-empty ## Status")
        malformed = self.response().replace("## Confidence", "### Confidence")
        self.assert_blocked(self.call_stop(malformed))

    def test_stop_rejects_status_and_confidence_disagreement(self):
        self.start()
        self.write_ledger()
        self.assert_blocked(
            self.call_stop(self.response(status="blocked")), "disagrees"
        )

    def test_stop_rejects_missing_checkpoints_and_wrong_minimum(self):
        self.start()
        self.write_ledger(self.record().replace("initial", "milestone-1"))
        self.assert_blocked(self.call_stop(self.response()), "initial first and final last")

    def test_stop_rejects_missing_confidence_checkpoints_section(self):
        self.start()
        self.write_ledger(
            self.record().replace(
                "## Confidence checkpoints", "## Checkpoint evidence"
            )
        )
        self.assert_blocked(
            self.call_stop(self.response()), "one non-empty ## Confidence checkpoints"
        )

    def test_stop_rejects_duplicate_confidence_checkpoints_sections(self):
        self.start()
        duplicated = self.record().replace(
            "## Confidence checkpoints\n"
            "- confidence: initial — 94% — grounded in design\n"
            "- confidence: final — 90% — validation passed",
            "## Confidence checkpoints\n"
            "- confidence: initial — 94% — grounded in design\n\n"
            "## Confidence checkpoints\n"
            "- confidence: final — 90% — validation passed",
        )
        self.write_ledger(duplicated)
        self.assert_blocked(
            self.call_stop(self.response()), "one non-empty ## Confidence checkpoints"
        )

    def test_stop_rejects_checkpoint_minimum_disagreement(self):
        self.start()
        self.write_ledger(self.record(checkpoints=(95, 92)))
        self.assert_blocked(self.call_stop(self.response()), "minimum")

    def test_stop_accepts_strict_initial_contiguous_milestones_and_final(self):
        self.start()
        self.write_ledger(
            self.record(
                checkpoint_lines=(
                    "- confidence: initial — 96% — design is explicit\n"
                    "- confidence: milestone-1 — 93% — parser implemented\n"
                    "- confidence: milestone-2 — 91% — negatives covered\n"
                    "- confidence: final — 90% — suite passed"
                )
            )
        )
        self.assertEqual(
            {"decision": "allow"}, verifier.stop(self.payload(response=self.response()))
        )

    def test_stop_rejects_every_malformed_checkpoint_section_line(self):
        valid_initial = "- confidence: initial — 94% — grounded in design"
        valid_final = "- confidence: final — 90% — validation passed"
        cases = {
            "blank": f"{valid_initial}\n\n{valid_final}",
            "prose": f"{valid_initial}\ncheckpoint pending\n{valid_final}",
            "wrong_prefix": f"{valid_initial}\n* confidence: milestone-1 — 91% — done\n{valid_final}",
            "missing_colon": f"{valid_initial}\n- confidence milestone-1 — 91% — done\n{valid_final}",
            "bad_separator": f"{valid_initial}\n- confidence: milestone-1 : 91% — done\n{valid_final}",
            "missing_percent": f"{valid_initial}\n- confidence: milestone-1 — 91 — done\n{valid_final}",
            "missing_rationale": f"{valid_initial}\n- confidence: milestone-1 — 91% — \n{valid_final}",
        }
        for name, checkpoint_lines in cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    verifier.VerificationError, "complete checkpoint lines"
                ):
                    verifier.parse_checkpoints(checkpoint_lines)

    def test_stop_rejects_invalid_checkpoint_label_ordering(self):
        line = lambda label: f"- confidence: {label} — 90% — evidence"
        cases = {
            "duplicate_initial": ["initial", "initial", "final"],
            "duplicate_final": ["initial", "final", "final"],
            "duplicate_milestone": ["initial", "milestone-1", "milestone-1", "final"],
            "gap": ["initial", "milestone-2", "final"],
            "reordered": ["initial", "milestone-2", "milestone-1", "final"],
            "milestone_after_final": ["initial", "final", "milestone-1"],
            "initial_not_first": ["milestone-1", "initial", "final"],
            "missing_initial": ["milestone-1", "final"],
            "missing_final": ["initial", "milestone-1"],
            "milestone_zero": ["initial", "milestone-0", "final"],
            "milestone_leading_zero": ["initial", "milestone-01", "final"],
        }
        for name, labels in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(verifier.VerificationError):
                    verifier.parse_checkpoints("\n".join(map(line, labels)))

    def test_malformed_low_confidence_milestone_cannot_be_ignored(self):
        self.start()
        self.write_ledger(
            self.record(
                checkpoint_lines=(
                    "- confidence: initial — 94% — grounded in design\n"
                    "- confidence: milestone-1: 20% — malformed separator\n"
                    "- confidence: final — 90% — validation passed"
                )
            )
        )
        self.assert_blocked(
            self.call_stop(self.response()), "complete checkpoint lines"
        )

    def test_confidence_policy(self):
        self.start()
        self.write_ledger(self.record(status="blocked", confidence=70, checkpoints=(80, 70)))
        self.assert_blocked(
            self.call_stop(self.response(status="completed", confidence=70)),
            "requires blocked",
        )
        valid = self.response(
            status="blocked",
            confidence=70,
            extras=(
                "## Low-confidence reason\nEvidence is incomplete.\n\n"
                "## Clarifications needed\nConfirm the payload.\n\n"
            ),
        )
        self.assertEqual({"decision": "allow"}, verifier.stop(self.payload(response=valid)))

    def test_pre_tool_denies_docs_and_allows_ledgers_and_unrelated_paths(self):
        self.start()
        denied = self.pre_tool_payload(str(self.docs / "design.md"))
        with self.assertRaisesRegex(verifier.VerificationError, "read-only"):
            verifier.pre_tool(denied)
        ledger = self.pre_tool_payload(
            "docs/artifacts/implementationdocs/ledgers/run.ledger.md"
        )
        unrelated = self.pre_tool_payload("src/main.py")
        self.assertEqual({}, verifier.pre_tool(ledger))
        self.assertEqual({}, verifier.pre_tool(unrelated))

    def test_pre_tool_classifies_recursive_normalized_and_sibling_paths(self):
        self.start()
        denied = (
            "docs/artifacts/implementationdocs/nested/design.md",
            str(self.docs / "nested/upper.MD"),
            "docs/artifacts/implementationdocs/./nested/../design.md",
            (
                "docs/artifacts/implementationdocs/ledgers/../"
                "nested/report.ledger.md"
            ),
        )
        for path in denied:
            with self.subTest(path=path):
                with self.assertRaisesRegex(verifier.VerificationError, "read-only"):
                    verifier.pre_tool(self.pre_tool_payload(path))

        allowed = (
            "docs/artifacts/implementationdocs/ledgers/run.ledger.md",
            "docs/artifacts/implementationdocs/ledgers/team/deep/run.ledger.md",
            "docs/artifacts/implementationdocs/ledgers-other/run.txt",
            "docs/artifacts/implementationdocs-other/design.md",
            "src/main.py",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertEqual({}, verifier.pre_tool(self.pre_tool_payload(path)))

    def test_pre_tool_anchors_relative_paths_to_nested_payload_cwd(self):
        self.start()
        nested_cwd = self.repo / "sub"
        nested_cwd.mkdir()
        denied = (
            "../docs/artifacts/implementationdocs/design.md",
            "../docs/artifacts/implementationdocs/nested/design.MD",
        )
        for path in denied:
            with self.subTest(path=path):
                with self.assertRaisesRegex(verifier.VerificationError, "read-only"):
                    verifier.pre_tool(
                        self.pre_tool_payload(path, cwd=str(nested_cwd))
                    )

        allowed = (
            "../docs/artifacts/implementationdocs/ledgers/team/run.ledger.md",
            "../src/main.py",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertEqual(
                    {},
                    verifier.pre_tool(
                        self.pre_tool_payload(path, cwd=str(nested_cwd))
                    ),
                )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_pre_tool_rejects_managed_symlinks_and_cross_zone_aliases(self):
        self.start()
        external = self.repo / "external"
        external.mkdir()
        managed_alias = self.docs / "external"
        managed_alias.symlink_to(external, target_is_directory=True)
        outside_alias = self.repo / "document-alias"
        outside_alias.symlink_to(self.docs, target_is_directory=True)
        protected_alias = self.ledgers / "protected.md"
        protected_alias.symlink_to(self.docs / "design.md")
        paths = (
            managed_alias / "design.md",
            outside_alias / "nested.md",
            protected_alias,
        )
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(verifier.VerificationError):
                    verifier.pre_tool(self.pre_tool_payload(str(path)))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_pre_tool_rejects_managed_root_ancestor_symlinks(self):
        for relative in ("docs", "docs/artifacts"):
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    repo, docs, _ = self.make_repository(base)
                    payload = self.payload(cwd=str(repo))
                    verifier.start(payload)
                    self.redirect_managed_ancestor(base, repo, relative)
                    tool_payload = self.pre_tool_payload(str(docs / "design.md"))
                    tool_payload["cwd"] = str(repo)
                    with self.assertRaisesRegex(verifier.VerificationError, "symlink"):
                        verifier.pre_tool(tool_payload)

    def test_pre_tool_without_active_implementer_is_a_noop(self):
        payload = self.pre_tool_payload(str(self.docs / "design.md"))
        self.assertNotIn("agentName", payload)
        self.assertEqual({}, verifier.pre_tool(payload))

    def test_pre_tool_fails_closed_for_malformed_or_mismatched_active_state(self):
        self.start()
        marker, run_file = verifier.paths_for(self.repo.resolve(), self.session)
        marker.write_text("not-a-run-file", encoding="utf-8")
        with self.assertRaisesRegex(verifier.VerificationError, "marker is malformed"):
            verifier.pre_tool(self.pre_tool_payload(str(self.docs / "design.md")))

        marker.write_text(run_file.name, encoding="utf-8")
        state = json.loads(run_file.read_text(encoding="utf-8"))
        state["root"] = str(self.repo / "other")
        run_file.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaisesRegex(verifier.VerificationError, "does not match"):
            verifier.pre_tool(self.pre_tool_payload(str(self.docs / "design.md")))

    def test_main_reads_one_payload_and_emits_compact_json(self):
        stdin = io.StringIO(json.dumps(self.payload(agentName="other")))
        stdout = io.StringIO()
        with mock.patch.object(verifier.sys, "argv", ["verify", "subagentStart"]):
            with mock.patch.object(verifier.sys, "stdin", stdin):
                with mock.patch.object(verifier.sys, "stdout", stdout):
                    self.assertEqual(0, verifier.main())
        self.assertEqual('{"decision":"allow"}\n', stdout.getvalue())

    def test_main_emits_pre_tool_permission_envelope(self):
        self.start()
        stdin = io.StringIO(
            json.dumps(self.pre_tool_payload(str(self.docs / "design.md")))
        )
        stdout = io.StringIO()
        with mock.patch.object(verifier.sys, "argv", ["verify", "preToolUse"]):
            with mock.patch.object(verifier.sys, "stdin", stdin):
                with mock.patch.object(verifier.sys, "stdout", stdout):
                    self.assertEqual(0, verifier.main())
        self.assertEqual(
            (
                '{"permissionDecision":"deny","permissionDecisionReason":'
                '"implementation documents are read-only"}\n'
            ),
            stdout.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
