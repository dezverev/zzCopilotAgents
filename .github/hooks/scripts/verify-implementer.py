#!/usr/bin/env python3
"""Fail-closed lifecycle verifier for the zz-implementer agent."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


AGENT = "zz-implementer"
STATE_ENV = "ZZ_IMPLEMENTER_STATE_ROOT"
EVENTS = {"subagentStart", "preToolUse", "subagentStop"}
LEDGER_ROOT = Path("docs/artifacts/implementationdocs/ledgers")
DOC_ROOT = Path("docs/artifacts/implementationdocs")
START_MARKER = "<!-- zz-implementer-run:start -->"
END_MARKER = "<!-- zz-implementer-run:end -->"
ALLOWED_STATUSES = {"completed", "needs-decomposition", "blocked"}
CHECKPOINT_RE = re.compile(
    r"-\s*confidence:\s*(initial|milestone-\d+|final)\s+[—-]\s+"
    r"(\d{1,3})%\s+[—-]\s+(\S.*)"
)
PROGRESS_RE = re.compile(r"- step-([1-9]\d*) — (\S.*)")
ZONE_DOCUMENT = "document"
ZONE_LEDGER = "ledger"
ZONE_UNMANAGED = "unmanaged"


class VerificationError(Exception):
    pass


def _relative_to(path: Path, parent: Path, *, strict: bool = False) -> bool:
    try:
        relative = path.relative_to(parent)
    except ValueError:
        return False
    return not strict or relative != Path()


def _managed_area(path: Path, docs_root: Path, ledger_root: Path) -> str:
    if _relative_to(path, ledger_root):
        return ZONE_LEDGER
    if _relative_to(path, docs_root):
        return ZONE_DOCUMENT
    return ZONE_UNMANAGED


def _raw_symlink_components(path: Path) -> list[Path]:
    current = Path(path.anchor)
    symlinks: list[Path] = []
    for part in path.parts[1:]:
        if part == ".":
            continue
        if part == "..":
            current = current.parent
            continue
        current /= part
        if current.is_symlink():
            symlinks.append(current)
    return symlinks


def _validate_managed_root_chains(repository: Path) -> None:
    for managed_root in (repository / DOC_ROOT, repository / LEDGER_ROOT):
        current = repository
        for part in managed_root.relative_to(repository).parts:
            current /= part
            if current.is_symlink():
                raise VerificationError("unsafe managed path contains a symlink")
            if current.exists() and not current.is_dir():
                raise VerificationError("managed root component is not a directory")


def classify_managed_path(root: Path, candidate: Path | str) -> str:
    """Classify a path without allowing aliases to cross managed-zone boundaries."""
    repository = Path(os.path.abspath(str(Path(root).expanduser())))
    resolved_repository = repository.resolve(strict=False)
    docs_root = repository / DOC_ROOT
    ledger_root = repository / LEDGER_ROOT
    supplied = Path(candidate).expanduser()
    raw = supplied if supplied.is_absolute() else repository / supplied
    lexical = Path(os.path.normpath(str(raw)))

    _validate_managed_root_chains(repository)

    resolved_docs = docs_root.resolve(strict=False)
    resolved_ledgers = ledger_root.resolve(strict=False)
    if (
        not _relative_to(resolved_docs, resolved_repository, strict=True)
        or not _relative_to(resolved_ledgers, resolved_repository, strict=True)
    ):
        raise VerificationError("managed roots resolve outside the repository")

    for symlink in _raw_symlink_components(raw):
        if _relative_to(symlink, docs_root):
            raise VerificationError("unsafe managed path contains a symlink")

    resolved = raw.resolve(strict=False)
    lexical_area = _managed_area(lexical, docs_root, ledger_root)
    resolved_area = _managed_area(resolved, resolved_docs, resolved_ledgers)
    if lexical_area != resolved_area:
        raise VerificationError("path alias crosses a managed-zone boundary")

    if _relative_to(lexical, ledger_root, strict=True):
        return ZONE_LEDGER
    if (
        _relative_to(lexical, docs_root, strict=True)
        and lexical.suffix.lower() == ".md"
    ):
        return ZONE_DOCUMENT
    return ZONE_UNMANAGED


def decision(allowed: bool, reason: str | None = None) -> dict[str, str]:
    result = {"decision": "allow" if allowed else "block"}
    if reason is not None:
        result["reason"] = reason
    return result


def tool_decision(allowed: bool, reason: str | None = None) -> dict[str, str]:
    if allowed:
        return {}
    return {
        "permissionDecision": "deny",
        "permissionDecisionReason": reason or "implementer tool use denied",
    }


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def state_root() -> Path:
    override = os.environ.get(STATE_ENV)
    return (
        Path(override).expanduser().resolve()
        if override
        else Path(tempfile.gettempdir()).resolve() / "zz-implementer-verifier"
    )


def repository_root(cwd: Any) -> Path:
    if not isinstance(cwd, str) or not cwd:
        raise VerificationError("payload is missing cwd")
    current = Path(cwd).expanduser().resolve()
    if not current.is_dir():
        raise VerificationError("payload cwd is not a directory")
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def encoded_files(paths: list[Path], root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): base64.b64encode(path.read_bytes()).decode("ascii")
        for path in paths
    }


def managed_regular_files(root: Path) -> tuple[list[Path], list[Path]]:
    docs_dir = root / DOC_ROOT
    _validate_managed_root_chains(root)
    if not docs_dir.exists():
        return [], []

    documents: list[Path] = []
    ledgers: list[Path] = []
    pending = [docs_dir]
    while pending:
        directory = pending.pop()
        for entry in sorted(os.scandir(directory), key=lambda item: item.name, reverse=True):
            path = Path(entry.path)
            if entry.is_symlink():
                raise VerificationError("unsafe managed path contains a symlink")
            if entry.is_dir(follow_symlinks=False):
                pending.append(path)
            elif entry.is_file(follow_symlinks=False):
                zone = classify_managed_path(root, path)
                if zone == ZONE_DOCUMENT:
                    documents.append(path)
                elif zone == ZONE_LEDGER:
                    ledgers.append(path)
    return sorted(documents), sorted(ledgers)


def snapshot(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    docs, ledgers = managed_regular_files(root)
    return encoded_files(docs, root), encoded_files(ledgers, root)


def paths_for(root: Path, session_id: str) -> tuple[Path, Path]:
    store = state_root()
    return (
        store / ("repo-" + digest(str(root)) + ".active"),
        store / ("run-" + digest(str(root) + "\0" + session_id) + ".json"),
    )


def prepare_state_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def write_private_state(path: Path, value: str) -> None:
    descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(value)
    finally:
        if descriptor != -1:
            os.close(descriptor)


def start(payload: dict[str, Any]) -> dict[str, str]:
    if payload.get("agentName") != AGENT:
        return decision(True)
    session_id = payload.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        raise VerificationError("start payload is missing sessionId")
    root = repository_root(payload.get("cwd"))
    marker, run_file = paths_for(root, session_id)
    prepare_state_directory(marker.parent)
    try:
        descriptor = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise VerificationError("another zz-implementer is already active for this repository") from error
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        docs, ledgers = snapshot(root)
        state = {
            "root": str(root),
            "sessionId": session_id,
            "documents": docs,
            "ledgers": ledgers,
        }
        write_private_state(run_file, json.dumps(state, separators=(",", ":")))
        os.write(descriptor, run_file.name.encode("utf-8"))
    except Exception:
        failed_descriptor = descriptor
        descriptor = -1
        os.close(failed_descriptor)
        run_file.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        raise
    finally:
        if descriptor != -1:
            os.close(descriptor)
    return decision(True)


def markdown_sections(text: str) -> dict[str, list[str]]:
    matches = list(re.finditer(r"(?m)^## ([^\r\n]+)\r?$", text))
    sections: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.setdefault(match.group(1).strip(), []).append(text[match.end() : end].strip())
    return sections


def unique_section(sections: dict[str, list[str]], name: str) -> str:
    values = sections.get(name, [])
    if len(values) != 1 or not values[0]:
        raise VerificationError(f"handoff must contain one non-empty ## {name} section")
    return values[0]


def parse_percentage(value: str, label: str) -> int:
    match = re.fullmatch(r"(\d{1,3})%", value.strip())
    if not match:
        raise VerificationError(f"{label} must be an integer percentage")
    number = int(match.group(1))
    if not 0 <= number <= 100:
        raise VerificationError(f"{label} must be between 0% and 100%")
    return number


def parse_response(response: Any) -> tuple[str, int, str]:
    if not isinstance(response, str):
        raise VerificationError("stop payload is missing response")
    sections = markdown_sections(response)
    status = unique_section(sections, "Status")
    if status not in ALLOWED_STATUSES:
        raise VerificationError("handoff status is not allowed")
    confidence = parse_percentage(unique_section(sections, "Confidence"), "handoff confidence")
    ledger = unique_section(sections, "Ledger")
    if "\n" in ledger:
        raise VerificationError("ledger section must contain only one path")
    if "`" in ledger:
        raise VerificationError("ledger section path must not be wrapped in backticks")
    ledger = ledger.strip()
    if confidence < 80:
        if status != "blocked":
            raise VerificationError("confidence below 80% requires blocked status")
        unique_section(sections, "Low-confidence reason")
        unique_section(sections, "Clarifications needed")
    return status, confidence, ledger


def resolve_ledger(root: Path, reported: str) -> tuple[Path, str]:
    relative = Path(reported)
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise VerificationError("ledger path must be repository-relative")
    if not relative.name.endswith(".ledger.md"):
        raise VerificationError("ledger path must end with .ledger.md")
    candidate = root / relative
    if classify_managed_path(root, candidate) != ZONE_LEDGER:
        raise VerificationError("ledger path is not beneath the ledger directory")
    if not candidate.is_file():
        raise VerificationError("reported ledger does not exist")
    return candidate, candidate.relative_to(root).as_posix()


def decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def verify_documents(root: Path, baseline: dict[str, str]) -> None:
    current, _ = snapshot(root)
    current_docs = current
    if set(current_docs) != set(baseline):
        raise VerificationError("implementation documents were added or removed")
    for name, value in baseline.items():
        if decode(value) != decode(current_docs[name]):
            raise VerificationError(f"implementation document changed: {name}")


def extract_record(appended: bytes, is_new: bool) -> str:
    try:
        text = appended.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationError("appended ledger record is not UTF-8") from error
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise VerificationError("ledger suffix must contain exactly one complete run record")
    before, remainder = text.split(START_MARKER, 1)
    record, after = remainder.split(END_MARKER, 1)
    if (not is_new and before.strip()) or after.strip():
        raise VerificationError("ledger suffix contains content outside the run record")
    return record


def baseline_record_count(baseline: bytes) -> int:
    try:
        text = baseline.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationError("ledger baseline is not UTF-8") from error
    count = 0
    in_record = False
    for line in text.splitlines():
        if line == START_MARKER:
            if in_record:
                raise VerificationError("ledger baseline contains a nested run start marker")
            in_record = True
        elif line == END_MARKER:
            if not in_record:
                raise VerificationError("ledger baseline contains an orphaned run end marker")
            in_record = False
            count += 1
    if in_record:
        raise VerificationError("ledger baseline contains an unterminated run start marker")
    return count


def validate_record_chronology(record: str, expected_ordinal: int) -> None:
    sections = markdown_sections(record)
    ordinal = unique_section(sections, "Run ordinal")
    if not re.fullmatch(r"[1-9]\d*", ordinal):
        raise VerificationError("run ordinal must be a positive decimal integer")
    if int(ordinal) != expected_ordinal:
        raise VerificationError(
            f"run ordinal must equal baseline record count plus one ({expected_ordinal})"
        )

    progress = unique_section(sections, "Progress")
    steps: list[int] = []
    for line in progress.splitlines():
        match = PROGRESS_RE.fullmatch(line)
        if not match:
            raise VerificationError(
                "progress must contain only non-empty ordered '- step-N — ...' bullets"
            )
        steps.append(int(match.group(1)))
    if steps != list(range(1, len(steps) + 1)):
        raise VerificationError("progress steps must start at step-1 and be contiguous in order")


def parse_checkpoints(section: str) -> list[int]:
    checkpoints: list[tuple[str, int]] = []
    for line in section.splitlines():
        match = CHECKPOINT_RE.fullmatch(line)
        if not match:
            raise VerificationError(
                "confidence checkpoints must contain only complete checkpoint lines"
            )
        value = int(match.group(2))
        if value > 100:
            raise VerificationError("checkpoint confidence must be between 0% and 100%")
        checkpoints.append((match.group(1), value))

    labels = [label for label, _ in checkpoints]
    if len(labels) < 2 or labels[0] != "initial" or labels[-1] != "final":
        raise VerificationError(
            "confidence checkpoints require initial first and final last"
        )
    expected = ["initial"]
    expected.extend(f"milestone-{number}" for number in range(1, len(labels) - 1))
    expected.append("final")
    if labels != expected:
        raise VerificationError(
            "confidence checkpoint milestones must be unique, contiguous, and ordered"
        )
    return [value for _, value in checkpoints]


def record_confidence(
    record: str, status: str, confidence: int, expected_ordinal: int
) -> None:
    sections = markdown_sections(record)
    validate_record_chronology(record, expected_ordinal)
    ledger_status = unique_section(sections, "Status")
    confidence_names = [
        name for name in ("Reported confidence", "Confidence") if sections.get(name)
    ]
    if len(confidence_names) != 1:
        raise VerificationError("run record must contain one reported confidence section")
    ledger_confidence = parse_percentage(
        unique_section(sections, confidence_names[0]), "ledger confidence"
    )
    if ledger_status != status or ledger_confidence != confidence:
        raise VerificationError("response status or confidence disagrees with ledger")
    unique_section(sections, "Validation")
    checkpoint_section = unique_section(sections, "Confidence checkpoints")
    values = parse_checkpoints(checkpoint_section)
    if min(values) != confidence:
        raise VerificationError("reported confidence must equal the minimum run checkpoint")


def verify_ledgers(
    root: Path, baseline: dict[str, str], ledger: Path, ledger_name: str, status: str, confidence: int
) -> None:
    baseline_bytes = decode(baseline[ledger_name]) if ledger_name in baseline else b""
    current_bytes = ledger.read_bytes()
    if not current_bytes.startswith(baseline_bytes):
        raise VerificationError("reported ledger is not append-only")
    expected_ordinal = baseline_record_count(baseline_bytes) + 1
    record = extract_record(current_bytes[len(baseline_bytes) :], ledger_name not in baseline)
    record_confidence(record, status, confidence, expected_ordinal)

    _, current = snapshot(root)
    allowed_names = set(baseline) | {ledger_name}
    if set(current) != allowed_names:
        raise VerificationError("an unreported ledger was added or an existing ledger was removed")
    for name, value in baseline.items():
        if name != ledger_name and current.get(name) != value:
            raise VerificationError(f"unreported ledger changed: {name}")


def stop(payload: dict[str, Any]) -> dict[str, str]:
    if payload.get("agentName") != AGENT:
        return decision(True)
    session_id = payload.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        raise VerificationError("stop payload is missing sessionId")
    root = repository_root(payload.get("cwd"))
    marker, run_file = paths_for(root, session_id)
    if not marker.is_file() or not run_file.is_file():
        raise VerificationError("no start state exists for this implementer session")
    try:
        state = json.loads(run_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerificationError("start state is unreadable") from error
    if state.get("root") != str(root) or state.get("sessionId") != session_id:
        raise VerificationError("start state does not match this repository and session")

    status, confidence, reported = parse_response(payload.get("response"))
    ledger, ledger_name = resolve_ledger(root, reported)
    verify_documents(root, state["documents"])
    verify_ledgers(root, state["ledgers"], ledger, ledger_name, status, confidence)
    run_file.unlink()
    marker.unlink()
    return decision(True)


def candidate_paths(value: Any, key: str = "") -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for child_key, child in value.items():
            result.extend(candidate_paths(child, str(child_key)))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(candidate_paths(child, key))
        return result
    lowered = key.lower()
    if isinstance(value, str) and ("path" in lowered or "file" in lowered):
        return [value]
    return []


def active_state(root: Path) -> dict[str, Any] | None:
    marker, _ = paths_for(root, "")
    if not marker.exists():
        return None
    if not marker.is_file():
        raise VerificationError("active implementer marker is malformed")
    try:
        run_name = marker.read_text(encoding="utf-8")
    except OSError as error:
        raise VerificationError("active implementer marker is unreadable") from error
    if not re.fullmatch(r"run-[0-9a-f]{64}\.json", run_name):
        raise VerificationError("active implementer marker is malformed")
    run_file = marker.parent / run_name
    if not run_file.is_file():
        raise VerificationError("active implementer state is missing")
    try:
        state = json.loads(run_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerificationError("active implementer state is unreadable") from error
    if not isinstance(state, dict):
        raise VerificationError("active implementer state is malformed")
    session_id = state.get("sessionId")
    if (
        state.get("root") != str(root)
        or not isinstance(session_id, str)
        or not session_id
        or not isinstance(state.get("documents"), dict)
        or not isinstance(state.get("ledgers"), dict)
        or paths_for(root, session_id)[1] != run_file
    ):
        raise VerificationError("active implementer state does not match its marker")
    return state


def pre_tool(payload: dict[str, Any]) -> dict[str, str]:
    session_id = payload.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        return tool_decision(True)
    root = repository_root(payload.get("cwd"))
    cwd = Path(payload["cwd"]).expanduser().resolve()
    state = active_state(root)
    if state is None or state["sessionId"] != session_id:
        return tool_decision(True)
    tool = payload.get("toolName")
    if not isinstance(tool, str):
        raise VerificationError("preToolUse payload is missing toolName")
    if not any(word in tool.lower() for word in ("edit", "create", "write", "patch")):
        return tool_decision(True)
    for raw in candidate_paths(payload.get("toolArgs", {})):
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = cwd / candidate
        if classify_managed_path(root, candidate) == ZONE_DOCUMENT:
            raise VerificationError("implementation documents are read-only")
    return tool_decision(True)


def main() -> int:
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in EVENTS:
            raise VerificationError("expected explicit subagentStart, preToolUse, or subagentStop event")
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise VerificationError("hook payload must be a JSON object")
        handlers = {
            "subagentStart": start,
            "preToolUse": pre_tool,
            "subagentStop": stop,
        }
        event = sys.argv[1]
        result = handlers[event](payload)
    except VerificationError as error:
        result = (
            tool_decision(False, str(error))
            if len(sys.argv) == 2 and sys.argv[1] == "preToolUse"
            else decision(False, str(error))
        )
    except Exception as error:
        reason = f"verifier failure: {type(error).__name__}"
        result = (
            tool_decision(False, reason)
            if len(sys.argv) == 2 and sys.argv[1] == "preToolUse"
            else decision(False, reason)
        )
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
