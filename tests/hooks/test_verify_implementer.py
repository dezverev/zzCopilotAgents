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

    def record(self, status="completed", confidence=90, checkpoints=(94, 90)):
        return (
            "# Ledger\n\n"
            f"{verifier.START_MARKER}\n"
            f"## Status\n{status}\n\n"
            f"## Reported confidence\n{confidence}%\n\n"
            "## Progress\n- implemented verifier\n\n"
            "## Confidence checkpoints\n"
            f"- confidence: initial — {checkpoints[0]}% — grounded in design\n"
            f"- confidence: final — {checkpoints[1]}% — validation passed\n\n"
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

    def test_stop_rejects_invalid_ledger_paths(self):
        self.start()
        outside = self.repo / "outside.ledger.md"
        outside.write_text(self.record())
        result = self.call_stop(self.response(ledger="outside.ledger.md"))
        self.assert_blocked(result, "not beneath")

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
        self.assert_blocked(self.call_stop(self.response()), "initial and one final")

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
            {
                "permissionDecision": "deny",
                "permissionDecisionReason": "implementation documents are read-only",
            },
            json.loads(stdout.getvalue()),
        )


if __name__ == "__main__":
    unittest.main()
