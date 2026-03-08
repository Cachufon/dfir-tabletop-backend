#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import secrets
import shutil
import socket
import time
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import streamlit as st

try:
    import segno  # type: ignore
except Exception:
    segno = None

try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore
except Exception:
    st_autorefresh = None

try:
    import yaml  # type: ignore
except Exception:
    st.error("Missing dependency PyYAML. Install with: pip install pyyaml")
    raise


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/ui/ttx_studio.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


REPO_ROOT = repo_root_from_here()


def parse_app_args() -> argparse.Namespace:
    # Streamlit forwards args placed after `--` into sys.argv. Use parse_known_args for safety.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode", default="full", choices=["full", "facilitate", "console"], help="UI mode: full studio, facilitator-only, or console-only.")
    parser.add_argument("--case-dir", default="", help="Optional case folder (contains case_manifest.json).")
    args, _ = parser.parse_known_args()
    return args


APP_ARGS = parse_app_args()

st.set_page_config(page_title="TTX Studio (Local)", layout="wide")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp_path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def read_taxonomy_categories(repo_root: Path) -> List[str]:
    taxonomy_path = repo_root / "dfir_backend" / "ttx" / "scenario_taxonomy.md"
    if not taxonomy_path.exists():
        return []
    categories: List[str] = []
    for raw_line in taxonomy_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            category = line[3:].strip()
            if category and category not in categories:
                categories.append(category)
    return categories


def persist_case_scenario_category(case_dir: Path, category: str) -> None:
    normalized_category = category.strip()
    if not normalized_category:
        return

    manifest_path = case_dir / "case_manifest.json"
    manifest_obj = load_json_safe(manifest_path) or {}
    if not isinstance(manifest_obj.get("scenario"), dict):
        manifest_obj["scenario"] = {}
    manifest_obj["scenario"]["category"] = normalized_category
    manifest_obj["last_updated_at_utc"] = now_iso()
    write_json_atomic(manifest_path, manifest_obj)

    intake_path = case_dir / "10_inputs" / "intake_structured.json"
    intake_obj = load_json_safe(intake_path) or {}
    intake_obj["preferred_scenario_category"] = normalized_category
    write_json_atomic(intake_path, intake_obj)


def live_state_path(case_dir: Path) -> Path:
    return case_dir / "30_outputs" / "ttx_logs" / "live_state.json"


def load_live_state(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def write_live_state(
    case_dir: Path,
    case_id: str,
    current_inject_id: str,
    responses_open: bool,
    open_until_epoch: Optional[int],
    race_enabled: bool = False,
    deputy_mode: bool = False,
    deputy_role_unavailable: Optional[str] = None,
    deputy_minutes: Optional[int] = None,
    display_mode: Optional[str] = None,
    display_image_path: Optional[str] = None,
) -> Dict[str, Any]:
    existing_state = load_live_state(live_state_path(case_dir))
    existing_display_mode = ""
    existing_display_image_path = ""
    if isinstance(existing_state, dict):
        existing_display_mode = str(existing_state.get("display_mode", "")).strip()
        existing_display_image_path = str(existing_state.get("display_image_path", "")).strip()

    payload = {
        "case_id": case_id,
        "current_inject_id": current_inject_id,
        "responses_open": bool(responses_open),
        "open_until_epoch": open_until_epoch,
        "race_enabled": bool(race_enabled),
        "deputy_mode": bool(deputy_mode),
        "deputy_role_unavailable": deputy_role_unavailable,
        "deputy_minutes": deputy_minutes,
        "display_mode": (display_mode.strip() if isinstance(display_mode, str) else existing_display_mode),
        "display_image_path": (display_image_path.strip() if isinstance(display_image_path, str) else existing_display_image_path),
        "updated_epoch": int(time.time()),
    }
    write_json_atomic(live_state_path(case_dir), payload)
    return payload


def participants_dir(case_dir: Path) -> Path:
    return case_dir / "30_outputs" / "ttx_logs" / "participants"


def participants_roster_path(case_dir: Path) -> Path:
    return participants_dir(case_dir) / "participants.json"


def acquire_lock(path: Path, timeout_seconds: int = 5) -> Path:
    lock_path = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(lock_fd)
            return lock_path
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timeout acquiring lock: {lock_path}")
            time.sleep(0.05)


def load_or_create_participants_roster(case_dir: Path) -> Dict[str, Any]:
    roster_path = participants_roster_path(case_dir)
    roster_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = acquire_lock(roster_path)
    try:
        if roster_path.exists():
            try:
                parsed = json.loads(roster_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    join_code = str(parsed.get("join_code", "")).strip()
                    participants = parsed.get("participants", [])
                    if not isinstance(participants, list):
                        participants = []
                    if join_code:
                        return {
                            "join_code": join_code,
                            "participants": [p for p in participants if isinstance(p, dict)],
                        }
                    payload = {
                        "join_code": secrets.token_urlsafe(6),
                        "participants": [p for p in participants if isinstance(p, dict)],
                    }
                    write_json_atomic(roster_path, payload)
                    return payload
            except Exception:
                pass

        payload = {
            "join_code": secrets.token_urlsafe(6),
            "participants": [],
        }
        write_json_atomic(roster_path, payload)
        return payload
    finally:
        try:
            lock_path.unlink()
        except OSError:
            pass


def participant_responses_dir(case_dir: Path) -> Path:
    return participants_dir(case_dir) / "responses"


def participant_response_path(case_dir: Path, participant_id: str) -> Path:
    return participant_responses_dir(case_dir) / f"{participant_id}.jsonl"


def detect_lan_host() -> str:
    sock: Optional[socket.socket] = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        host = str(sock.getsockname()[0]).strip()
        return host if host else "<HOST>"
    except Exception:
        return "<HOST>"
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass


def shareable_base_url_from_env(port_num: int) -> Optional[str]:
    configured = str(os.getenv("TTX_BASE_URL", "")).strip()
    if not configured:
        return None

    parsed = urlparse(configured)
    hostname = (parsed.hostname or "").strip()
    if hostname == "0.0.0.0":
        scheme = parsed.scheme or "http"
        return f"{scheme}://127.0.0.1:{port_num}"

    return configured.rstrip("/")


def normalize_base_url(raw_base_url: str, port_num: int) -> str:
    candidate = raw_base_url.strip()
    if not candidate:
        candidate = f"http://127.0.0.1:{port_num}"

    parsed = urlparse(candidate)
    if not parsed.scheme:
        parsed = urlparse(f"http://{candidate}")

    scheme = parsed.scheme or "http"
    hostname = (parsed.hostname or "").strip() or "127.0.0.1"
    if hostname == "0.0.0.0":
        hostname = "127.0.0.1"

    netloc = hostname
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    elif parsed.netloc:
        netloc = f"{netloc}:{port_num}"
    elif ":" in candidate:
        netloc = f"{netloc}:{port_num}"
    else:
        netloc = f"{netloc}:{port_num}"

    return f"{scheme}://{netloc}".rstrip("/")


def natural_inject_order(injects: List[Dict[str, Any]]) -> List[str]:
    ordered_ids: List[str] = []
    for inj in injects:
        inject_id = str(inj.get("id", "")).strip()
        if inject_id and inject_id not in ordered_ids:
            ordered_ids.append(inject_id)
    return ordered_ids


def inject_sort_key(inject_id: str) -> Tuple[int, int, str]:
    normalized = inject_id.strip()
    if normalized.startswith("i") and normalized[1:].isdigit():
        return (0, int(normalized[1:]), normalized)
    return (1, 0, normalized)


def collect_participant_responses(case_dir: Path, injects: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    total_participants = 0
    roster_path = participants_roster_path(case_dir)
    if roster_path.exists():
        try:
            parsed_roster = json.loads(roster_path.read_text(encoding="utf-8"))
            if isinstance(parsed_roster, dict):
                roster_participants = parsed_roster.get("participants", [])
                if isinstance(roster_participants, list):
                    total_participants = len([p for p in roster_participants if isinstance(p, dict)])
        except Exception:
            total_participants = 0

    responses_dir = participant_responses_dir(case_dir)
    if not responses_dir.exists():
        return [], {}, {
            "total_participants": total_participants,
            "responses_per_inject": {},
            "completion_rate_per_inject": {},
        }

    participant_files = sorted(
        [p for p in responses_dir.glob("*.jsonl") if p.is_file()],
        key=lambda p: p.stem,
    )
    inject_order = sorted(natural_inject_order(injects), key=inject_sort_key)

    collected_rows: List[Dict[str, Any]] = []
    for response_file in participant_files:
        participant_id = response_file.stem.strip()
        if not participant_id:
            continue
        try:
            with response_file.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        parsed = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(parsed, dict):
                        continue
                    row = dict(parsed)
                    row["participant_id"] = participant_id
                    row["inject_id"] = str(parsed.get("inject_id", "")).strip()
                    row["epoch"] = int(parsed.get("epoch", 0)) if str(parsed.get("epoch", "")).strip() else 0
                    collected_rows.append(row)
        except Exception:
            continue

    def response_sort_key(row: Dict[str, Any]) -> Tuple[int, int, str, int, str]:
        inject_id = str(row.get("inject_id", "")).strip()
        return (
            *inject_sort_key(inject_id),
            int(row.get("epoch", 0)),
            str(row.get("participant_id", "")).strip(),
        )

    collected_rows.sort(key=response_sort_key)

    participant_responses_by_inject: Dict[str, List[Dict[str, Any]]] = {inject_id: [] for inject_id in inject_order}
    for row in collected_rows:
        inject_id = str(row.get("inject_id", "")).strip()
        if inject_id not in participant_responses_by_inject:
            participant_responses_by_inject[inject_id] = []
        participant_responses_by_inject[inject_id].append(row)

    responses_per_inject: Dict[str, int] = {}
    completion_rate_per_inject: Dict[str, float] = {}
    ordered_inject_ids = sorted(participant_responses_by_inject.keys(), key=inject_sort_key)
    for inject_id in ordered_inject_ids:
        responses = participant_responses_by_inject.get(inject_id, [])
        response_participants = {str(r.get("participant_id", "")).strip() for r in responses if str(r.get("participant_id", "")).strip()}
        responses_per_inject[inject_id] = len(response_participants)
        completion_rate_per_inject[inject_id] = (len(response_participants) / total_participants) if total_participants > 0 else 0.0

    summary = {
        "total_participants": total_participants,
        "responses_per_inject": responses_per_inject,
        "completion_rate_per_inject": completion_rate_per_inject,
    }
    return collected_rows, participant_responses_by_inject, summary


def inject_completion_status(case_dir: Path, inject_id: str) -> Dict[str, Any]:
    normalized_inject_id = inject_id.strip()
    roster_participants: List[Dict[str, Any]] = []
    roster_path = participants_roster_path(case_dir)
    if roster_path.exists():
        try:
            parsed = json.loads(roster_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                raw_participants = parsed.get("participants", [])
                if isinstance(raw_participants, list):
                    roster_participants = [p for p in raw_participants if isinstance(p, dict)]
        except Exception:
            roster_participants = []

    joined_by_id: Dict[str, Dict[str, str]] = {}
    for participant in roster_participants:
        participant_id = str(participant.get("participant_id", "")).strip()
        if not participant_id:
            continue
        joined_by_id[participant_id] = {
            "participant_id": participant_id,
            "display_name": str(participant.get("display_name", "")).strip(),
            "role": str(participant.get("role", "")).strip(),
        }

    submitted_participant_ids: set[str] = set()
    responses_dir = participant_responses_dir(case_dir)
    if normalized_inject_id and responses_dir.exists():
        for response_file in responses_dir.glob("*.jsonl"):
            participant_id = response_file.stem.strip()
            if not participant_id:
                continue
            try:
                with response_file.open("r", encoding="utf-8") as handle:
                    for raw_line in handle:
                        line = raw_line.strip()
                        if not line:
                            continue
                        parsed = json.loads(line)
                        if not isinstance(parsed, dict):
                            continue
                        if str(parsed.get("inject_id", "")).strip() == normalized_inject_id:
                            submitted_participant_ids.add(participant_id)
                            break
            except Exception:
                continue

    missing_participants: List[Dict[str, str]] = []
    for participant_id, participant in joined_by_id.items():
        if participant_id in submitted_participant_ids:
            continue
        missing_participants.append({
            "display_name": participant.get("display_name", ""),
            "role": participant.get("role", ""),
        })

    return {
        "total_participants": len(joined_by_id),
        "submitted_count": len([p for p in submitted_participant_ids if p in joined_by_id]),
        "missing_participants": sorted(missing_participants, key=lambda row: (row.get("display_name", ""), row.get("role", ""))),
    }


def upsert_participant_roster(case_dir: Path, join_code: str, participant_entry: Dict[str, Any]) -> None:
    roster_path = participants_roster_path(case_dir)
    roster_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = acquire_lock(roster_path)
    try:
        existing: Dict[str, Any] = {}
        if roster_path.exists():
            try:
                parsed = json.loads(roster_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    existing = parsed
            except Exception:
                existing = {}
        participants = existing.get("participants", []) if isinstance(existing.get("participants", []), list) else []
        participant_id = str(participant_entry.get("participant_id", "")).strip()
        filtered = [row for row in participants if isinstance(row, dict) and str(row.get("participant_id", "")).strip() != participant_id]
        filtered.append(participant_entry)
        payload = {
            "join_code": join_code,
            "participants": filtered,
        }
        write_json_atomic(roster_path, payload)
    finally:
        try:
            lock_path.unlink()
        except OSError:
            pass


def append_participant_response(case_dir: Path, participant_id: str, payload: Dict[str, Any]) -> None:
    response_path = participant_response_path(case_dir, participant_id)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, separators=(",", ":")) + "\n"
    fd = os.open(str(response_path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def participant_submitted_inject(case_dir: Path, participant_id: str, inject_id: str) -> bool:
    response_path = participant_response_path(case_dir, participant_id)
    if not response_path.exists() or not inject_id.strip():
        return False
    try:
        with response_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict) and str(obj.get("inject_id", "")).strip() == inject_id.strip():
                    return True
    except Exception:
        return False
    return False


def handling_label_from_manifest(manifest: Dict[str, Any]) -> str:
    hl = str(manifest.get("handling_label", "")).strip()
    if hl:
        return hl
    tlp = str(manifest.get("tlp", "")).strip()
    mapping = {
        "TLP:CLEAR": "PUBLIC",
        "TLP:GREEN": "INTERNAL",
        "TLP:AMBER": "CONFIDENTIAL",
        "TLP:AMBER+STRICT": "CLIENT_CONFIDENTIAL",
        "TLP:RED": "CLIENT_CONFIDENTIAL",
    }
    return mapping.get(tlp, "CLIENT_CONFIDENTIAL" if tlp else "CLIENT_CONFIDENTIAL")


def case_context(case_dir: str) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
    if not case_dir.strip():
        return None, None
    p = Path(case_dir).expanduser().resolve()
    if not p.is_dir():
        return p, None
    manifest_path = p / "case_manifest.json"
    if not manifest_path.exists():
        return p, None
    try:
        return p, load_json(manifest_path)
    except Exception:
        return p, None


def resolve_case_dir_from_query(case_param: str) -> Tuple[Optional[Path], Optional[str]]:
    normalized_case_param = case_param.strip()
    if not normalized_case_param:
        return None, "Missing required query parameter: `case`."

    allowed_case_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if any(ch not in allowed_case_chars for ch in normalized_case_param):
        return None, "Invalid case id. Allowed characters: letters, numbers, underscore, hyphen."

    cases_root = str(os.environ.get("TTX_CASES_ROOT", "~/ttx_cases")).strip() or "~/ttx_cases"
    root = Path(cases_root).expanduser().resolve()
    resolved_case_dir = (root / normalized_case_param).resolve()

    try:
        resolved_case_dir.relative_to(root)
    except ValueError:
        return None, "Invalid case path."

    if not resolved_case_dir.is_dir():
        return None, f"Case not found: {resolved_case_dir}"

    return resolved_case_dir, None


QUERY_CASE_ID = str(st.query_params.get("case", "")).strip()
case_dir_from_query = ""
if not APP_ARGS.case_dir.strip() and QUERY_CASE_ID:
    allowed_case_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if all(ch in allowed_case_chars for ch in QUERY_CASE_ID):
        query_cases_root = str(os.environ.get("TTX_CASES_ROOT", "~/ttx_cases")).strip() or "~/ttx_cases"
        query_root = Path(query_cases_root).expanduser().resolve()
        query_case_dir = (query_root / QUERY_CASE_ID).resolve()
        try:
            query_case_dir.relative_to(query_root)
            case_dir_from_query = str(query_case_dir)
        except ValueError:
            case_dir_from_query = ""

CASE_DIR_PATH, CASE_MANIFEST = case_context(APP_ARGS.case_dir or case_dir_from_query)


def resolve_case_rel(rel: str) -> Optional[Path]:
    if CASE_DIR_PATH is None:
        return None
    return (CASE_DIR_PATH / rel).resolve()


def case_assets_dir(case_dir: Path) -> Path:
    return case_dir / "40_assets"


def case_asset_image_files(case_dir: Path) -> List[Path]:
    assets_dir = case_assets_dir(case_dir)
    if not assets_dir.exists():
        return []
    allowed_suffixes = {".png", ".jpg", ".jpeg"}
    return sorted(
        [p for p in assets_dir.iterdir() if p.is_file() and p.suffix.lower() in allowed_suffixes],
        key=lambda p: p.name.lower(),
    )


def case_manifest_exists() -> bool:
    return bool(CASE_DIR_PATH and (CASE_DIR_PATH / "case_manifest.json").exists() and CASE_MANIFEST)


def aar_manifest_paths() -> Optional[Dict[str, Path]]:
    if not case_manifest_exists() or CASE_DIR_PATH is None or CASE_MANIFEST is None:
        return None
    try:
        scenario_yaml = (CASE_DIR_PATH / str(CASE_MANIFEST["scenario"]["scenario_yaml_path"])).resolve()
        runtime_json = (CASE_DIR_PATH / str(CASE_MANIFEST["outputs"]["scribe_runtime_json_path"])).resolve()
        aar_draft_path = (CASE_DIR_PATH / str(CASE_MANIFEST["outputs"]["aar_draft_path"])).resolve()
        aar_ai_bundle_path = (CASE_DIR_PATH / str(CASE_MANIFEST["outputs"]["aar_ai_bundle_path"])).resolve()
        ir_plan_path = (CASE_DIR_PATH / str(CASE_MANIFEST["inputs"]["ir_plan_path"])).resolve()
        intake_notes_path = (CASE_DIR_PATH / str(CASE_MANIFEST["inputs"]["intake_notes_path"])).resolve()
    except Exception:
        return None
    return {
        "scenario_yaml": scenario_yaml,
        "runtime_json": runtime_json,
        "aar_draft_path": aar_draft_path,
        "aar_ai_bundle_path": aar_ai_bundle_path,
        "ir_plan_path": ir_plan_path,
        "intake_notes_path": intake_notes_path,
        "out_dir": aar_draft_path.parent,
    }


def run_script(cmd: List[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def case_status_flags(case_dir: Path) -> Dict[str, bool]:
    return {
        "case_manifest.json": (case_dir / "case_manifest.json").exists(),
        "10_inputs/intake_notes.md": (case_dir / "10_inputs" / "intake_notes.md").exists(),
        "10_inputs/intake_structured.json": (case_dir / "10_inputs" / "intake_structured.json").exists(),
        "20_delivery/scenario.yaml": (case_dir / "20_delivery" / "scenario.yaml").exists(),
        "20_delivery/ttx_package": (case_dir / "20_delivery" / "ttx_package").exists(),
    }


def default_scoring() -> Dict[str, Dict[str, Any]]:
    return {
        "detection_awareness": {"label": "Detection & Awareness", "score": 3, "evidence": ""},
        "decision_making": {"label": "Decision-Making", "score": 3, "evidence": ""},
        "communication": {"label": "Communication", "score": 3, "evidence": ""},
        "escalation_authority": {"label": "Escalation & Authority", "score": 3, "evidence": ""},
        "legal_regulatory": {"label": "Legal & Regulatory Awareness", "score": 3, "evidence": ""},
        "documentation_tracking": {"label": "Documentation & Tracking", "score": 3, "evidence": ""},
    }


def ensure_session_defaults() -> None:
    st.session_state.setdefault("scenario_loaded", False)
    st.session_state.setdefault("scenario_path", "")
    st.session_state.setdefault("scenario_obj", None)
    st.session_state.setdefault("timer_started", False)
    st.session_state.setdefault("timer_start_utc", "")
    st.session_state.setdefault("manual_t_plus", 0)
    st.session_state.setdefault("notes_global", "")
    st.session_state.setdefault("notes_hotwash", "")
    st.session_state.setdefault("notes_by_inject", {})  # inject_id -> dict
    st.session_state.setdefault("selected_inject_id", "")
    st.session_state.setdefault("parking_lot", "")
    st.session_state.setdefault("scoring", default_scoring())
    st.session_state.setdefault("hide_numeric_scores_in_md", True)
    st.session_state.setdefault("hotwash_went_well", "")
    st.session_state.setdefault("hotwash_gaps", "")
    st.session_state.setdefault("hotwash_improvements", "")
    st.session_state.setdefault("hotwash_open_questions", "")
    st.session_state.setdefault("opening_script_text", "")
    st.session_state.setdefault("opening_script_scenario_path", "")
    st.session_state.setdefault("participant_identity", None)


def render_participant_portal() -> None:
    query_mode = str(st.query_params.get("mode", "")).strip().lower()
    if query_mode != "participant":
        return
    st.title("TTX Participant Portal")

    query_case_id = str(st.query_params.get("case", "")).strip()
    query_join_code = str(st.query_params.get("join", "")).strip()
    st.caption("Participant mode is enabled via `?mode=participant`.")

    manifest: Optional[Dict[str, Any]] = None
    if not query_case_id:
        st.error("Missing required query parameter: `case`. Use `?mode=participant&case=<case_id>`.")
        st.stop()

    resolved_case_dir, case_error = resolve_case_dir_from_query(query_case_id)
    if case_error:
        st.error(case_error)
        st.stop()
    if resolved_case_dir is None:
        st.error("Failed to resolve case directory.")
        st.stop()

    manifest_path = resolved_case_dir / "case_manifest.json"
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        st.error(f"Failed to load case manifest: {exc}")
        st.stop()

    st.success(f"Case loaded: {manifest.get('case_id', query_case_id)}")

    roster = load_or_create_participants_roster(resolved_case_dir)
    expected_join_code = str(roster.get("join_code", "")).strip()
    entered_join_code = st.text_input("Join code", value=query_join_code)
    if not entered_join_code.strip():
        st.info("Enter the join code to continue.")
        st.stop()
    if entered_join_code.strip() != expected_join_code:
        st.error("Invalid join code.")
        st.stop()

    display_name = st.text_input("Your name / alias (shown to facilitator)", value="", help="Use your preferred name for this exercise.")
    roles = manifest.get("audience_roles", []) if isinstance(manifest.get("audience_roles", []), list) else []
    role_options = [str(role).strip() for role in roles if str(role).strip()]
    role_options_with_custom = role_options + ["Other (type custom)"]

    role_value = ""
    if role_options_with_custom:
        selected_role_option = st.selectbox("Role", options=role_options_with_custom, index=0)
        if selected_role_option == "Other (type custom)":
            role_value = st.text_input("Custom role", value="")
        else:
            role_value = selected_role_option
    else:
        role_value = st.text_input("Role", value="")

    if st.button("Join"):
        if not display_name.strip():
            st.error("Display name is required.")
        elif not str(role_value).strip():
            st.error("Role is required.")
        else:
            participants = roster.get("participants", []) if isinstance(roster.get("participants", []), list) else []
            participant_id = ""
            for row in participants:
                if not isinstance(row, dict):
                    continue
                existing_name = str(row.get("display_name", "")).strip()
                existing_role = str(row.get("role", "")).strip()
                if existing_name == display_name.strip() and existing_role == str(role_value).strip():
                    participant_id = str(row.get("participant_id", "")).strip()
                    break
            if not participant_id:
                participant_id = secrets.token_hex(4)
            created_epoch = int(time.time())
            st.session_state["participant_identity"] = {
                "case_id": str(manifest.get("case_id", query_case_id)).strip() or query_case_id,
                "case_dir": str(resolved_case_dir),
                "participant_id": participant_id,
                "display_name": display_name.strip(),
                "role": str(role_value).strip(),
                "joined_at_utc": now_iso(),
            }
            upsert_participant_roster(
                resolved_case_dir,
                expected_join_code,
                {
                    "participant_id": participant_id,
                    "display_name": display_name.strip(),
                    "role": str(role_value).strip(),
                    "created_epoch": created_epoch,
                },
            )
            st.success("Participant identity saved.")

    if isinstance(st.session_state.get("participant_identity"), dict):
        st.info(f"Joined as {st.session_state['participant_identity'].get('display_name', '')} ({st.session_state['participant_identity'].get('role', '')})")

        if callable(st_autorefresh):
            st_autorefresh(interval=2500, key="participant_portal_autorefresh")
        else:
            st.button("Refresh status")

        state_path = live_state_path(resolved_case_dir)
        live_state = load_live_state(state_path)
        if not live_state:
            st.warning("Waiting for facilitator live state...")
            st.stop()

        current_inject_id = str(live_state.get("current_inject_id", "")).strip()
        responses_open = bool(live_state.get("responses_open", False))
        race_enabled = bool(live_state.get("race_enabled", False))
        deputy_mode = bool(live_state.get("deputy_mode", False))
        deputy_role_unavailable = str(live_state.get("deputy_role_unavailable", "")).strip()
        deputy_minutes_raw = live_state.get("deputy_minutes", None)
        deputy_minutes: Optional[int] = None
        if deputy_minutes_raw is not None:
            try:
                deputy_minutes = int(deputy_minutes_raw)
            except Exception:
                deputy_minutes = None
        open_until_epoch_raw = live_state.get("open_until_epoch", None)
        open_until_epoch: Optional[int] = None
        if open_until_epoch_raw is not None:
            try:
                open_until_epoch = int(open_until_epoch_raw)
            except Exception:
                open_until_epoch = None

        scenario_rel = str(manifest.get("scenario", {}).get("scenario_yaml_path", "")).strip()
        inject_prompt = ""
        if scenario_rel:
            scenario_path = (resolved_case_dir / scenario_rel).resolve()
            try:
                scenario_obj = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
                injects = []
                if isinstance(scenario_obj, dict):
                    injects_raw = scenario_obj.get("injects", [])
                    if isinstance(injects_raw, list):
                        injects = [i for i in injects_raw if isinstance(i, dict)]
                current_inject = next((i for i in injects if str(i.get("id", "")).strip() == current_inject_id), None)
                if isinstance(current_inject, dict):
                    inject_prompt = str(current_inject.get("participant_prompt", "")).strip()
            except Exception:
                inject_prompt = ""

        now_epoch = int(time.time())
        open_now = bool(responses_open and open_until_epoch is not None and now_epoch <= open_until_epoch)

        st.markdown(f"### Current Inject: {current_inject_id or '(not set)'}")
        if inject_prompt:
            st.markdown("#### Inject Prompt")
            st.markdown(inject_prompt)
        if deputy_mode and deputy_role_unavailable and deputy_minutes is not None:
            st.warning(f"Assume {deputy_role_unavailable} is unavailable for {deputy_minutes} min; deputies act.")

        identity = st.session_state.get("participant_identity", {})
        participant_id = str(identity.get("participant_id", "")).strip() if isinstance(identity, dict) else ""
        already_submitted = bool(participant_id and current_inject_id and participant_submitted_inject(resolved_case_dir, participant_id, current_inject_id))

        if open_now:
            remaining = max(0, int(open_until_epoch or 0) - now_epoch)
            st.success(f"Responses are open for this inject ({remaining}s remaining).")
            if already_submitted:
                st.info(f"Submitted for {current_inject_id}")
                st.button("Submit response", disabled=True)
            else:
                with st.form(key=f"participant_response_{current_inject_id or 'none'}"):
                    actions = st.text_area("Actions", value="", height=100)
                    questions = st.text_area("Questions", value="", height=100)
                    escalations = st.text_area("Escalations", value="", height=100)
                    decision = st.text_area("Decision", value="", height=80)
                    evidence = st.text_area("Evidence", value="", height=100)
                    other_notes = st.text_area("Other notes", value="", height=100)
                    confidence = st.slider("Confidence", min_value=0, max_value=3, value=0, step=1)
                    decision_owner = ""
                    decision_owner_confidence = None
                    if race_enabled:
                        race_roles = [str(role).strip() for role in roles if str(role).strip()]
                        if not race_roles:
                            joined_role = str(identity.get("role", "")).strip()
                            race_roles = [joined_role] if joined_role else ["Unspecified"]
                        decision_owner = st.selectbox("decision_owner", options=race_roles, index=0)
                        decision_owner_confidence = st.slider("decision_owner_confidence", min_value=0, max_value=3, value=0, step=1)
                    submitted = st.form_submit_button("Submit response")
                    if submitted:
                        if not participant_id:
                            st.error("Participant session is missing participant_id. Please re-join.")
                        elif participant_submitted_inject(resolved_case_dir, participant_id, current_inject_id):
                            st.info(f"Submitted for {current_inject_id}")
                        else:
                            append_participant_response(
                                resolved_case_dir,
                                participant_id,
                                {
                                    "epoch": int(time.time()),
                                    "inject_id": current_inject_id,
                                    "participant_id": participant_id,
                                    "display_name": str(identity.get("display_name", "")).strip(),
                                    "role": str(identity.get("role", "")).strip(),
                                    "actions": actions,
                                    "questions": questions,
                                    "escalations": escalations,
                                    "decision": decision,
                                    "evidence": evidence,
                                    "other_notes": other_notes,
                                    "confidence": confidence,
                                    "decision_owner": decision_owner,
                                    "decision_owner_confidence": decision_owner_confidence,
                                },
                            )
                            st.success("Response submitted.")
                            st.rerun()
        else:
            st.info("Waiting for facilitator")

    st.stop()


def render_display_view(case_dir: Path, query_join_code: str) -> None:
    current_live_state = load_live_state(live_state_path(case_dir)) or {}
    responses_open = bool(current_live_state.get("responses_open", False))

    pause_updates = st.checkbox("Pause updates", value=False, key="display_pause_updates")
    st.button("Refresh display")
    if not pause_updates and callable(st_autorefresh):
        refresh_interval_ms = 2000 if responses_open else 5000
        st_autorefresh(interval=refresh_interval_ms, key="display_autorefresh")

    roster = load_or_create_participants_roster(case_dir)
    join_code = str(roster.get("join_code", "")).strip()
    case_param = case_dir.name

    port = st.get_option("server.port")
    try:
        port_num = int(port)
    except Exception:
        port_num = 8501
    host = detect_lan_host()

    participant_url = f"http://{host}:{port_num}/?mode=participant&case={case_param}&join={join_code}"
    display_url = f"http://{host}:{port_num}/?mode=display&case={case_param}&join={join_code}"

    if host == "<HOST>":
        st.caption("Replace <HOST> with this facilitator machine hostname or LAN IP before sharing links.")

    display_mode = str(current_live_state.get("display_mode", "join")).strip().lower() or "join"
    current_inject_id = str(current_live_state.get("current_inject_id", "")).strip()
    open_until_raw = current_live_state.get("open_until_epoch", None)
    open_until_epoch: Optional[int] = None
    if open_until_raw is not None:
        try:
            open_until_epoch = int(open_until_raw)
        except Exception:
            open_until_epoch = None

    if display_mode == "image":
        display_image_rel = str(current_live_state.get("display_image_path", "")).strip()
        if not display_image_rel:
            st.warning("No image selected. Returning to join screen.")
            display_mode = "join"
        else:
            image_path = (case_dir / display_image_rel).resolve()
            assets_dir = case_assets_dir(case_dir).resolve()
            allowed_suffixes = {".png", ".jpg", ".jpeg"}
            try:
                image_path.relative_to(assets_dir)
                if not image_path.is_file() or image_path.suffix.lower() not in allowed_suffixes:
                    raise ValueError("invalid-image")
                st.image(str(image_path), use_container_width=True)
                return
            except Exception:
                st.error("Configured image is invalid or missing. Returning to join screen.")
                display_mode = "join"

    if display_mode == "inject":
        scenario_path = case_dir / "20_delivery" / "scenario.yaml"
        inject_obj: Optional[Dict[str, Any]] = None
        if scenario_path.exists():
            try:
                scenario_obj = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
                injects = scenario_obj.get("injects", []) if isinstance(scenario_obj, dict) else []
                inject_rows = [row for row in injects if isinstance(row, dict)] if isinstance(injects, list) else []
                inject_obj = next((row for row in inject_rows if str(row.get("id", "")).strip() == current_inject_id), None)
            except Exception:
                inject_obj = None

        inject_label = current_inject_id or "(not set)"
        inject_t_plus = ""
        participant_prompt = ""
        audience_values: List[str] = []
        if isinstance(inject_obj, dict):
            inject_label = str(inject_obj.get("id", "")).strip() or inject_label
            inject_t_plus = str(inject_obj.get("t_plus_min", "")).strip()
            participant_prompt = str(inject_obj.get("participant_prompt", "")).strip()
            raw_audience = inject_obj.get("audience", [])
            if isinstance(raw_audience, list):
                audience_values = [str(item).strip() for item in raw_audience if str(item).strip()]

        inject_header = f"Inject {inject_label}"
        if inject_t_plus:
            inject_header += f" (T+{inject_t_plus})"

        st.markdown("## Now Playing")
        st.markdown(f"### {inject_header}")
        if audience_values:
            st.caption(f"Target audience: {', '.join(audience_values)}")
        if participant_prompt:
            st.markdown(participant_prompt)
        else:
            st.info("No participant prompt available for this inject.")

        now_epoch = int(time.time())
        responses_open_now = bool(responses_open and open_until_epoch is not None and now_epoch <= open_until_epoch)
        if responses_open_now:
            remaining = max(0, int(open_until_epoch or 0) - now_epoch)
            minutes = remaining // 60
            seconds = remaining % 60
            completion = inject_completion_status(case_dir, current_inject_id)
            submitted = int(completion.get("submitted_count", 0))
            total = int(completion.get("total_participants", 0))
            st.success(f"Responses open: {minutes:02d}:{seconds:02d} remaining")
            st.markdown(f"### Submitted: {submitted} / {total}")
            if total > 0:
                st.progress(min(1.0, max(0.0, submitted / total)))
        return

    st.markdown("## Join Session")
    st.markdown(f"<h1 style='font-size: 6rem; margin: 0.5rem 0;'>Join code: {join_code}</h1>", unsafe_allow_html=True)
    if segno is not None:
        qr_buffer = io.BytesIO()
        segno.make(participant_url).save(qr_buffer, kind="png", scale=10)
        st.image(qr_buffer.getvalue(), width=460)
    else:
        st.info("Install `segno` to show a QR code on the display.")
    st.code(participant_url)
    st.caption("Open on phone; submit responses when prompted")
    if query_join_code and query_join_code != join_code:
        st.caption("Note: URL join code differs from current session join code.")
    st.caption(f"Display URL: {display_url}")


def render_display_portal() -> None:
    query_mode = str(st.query_params.get("mode", "")).strip().lower()
    if query_mode != "display":
        return

    st.title("TTX Display")
    st.caption("Display mode is enabled via `?mode=display`.")

    query_case_id = str(st.query_params.get("case", "")).strip()
    query_join_code = str(st.query_params.get("join", "")).strip()
    resolved_case_dir, case_error = resolve_case_dir_from_query(query_case_id)
    if case_error:
        st.error(f"{case_error} Use `?mode=display&case=<case_id>`.")
        st.stop()
    if resolved_case_dir is None:
        st.error("Failed to resolve case directory.")
        st.stop()

    render_display_view(resolved_case_dir, query_join_code)
    st.stop()


ensure_session_defaults()
query_mode = str(st.query_params.get("mode", "")).strip().lower()
if query_mode == "display":
    render_display_portal()
if query_mode == "participant":
    render_participant_portal()


def render_console() -> None:
    st.header("Operator Console")
    st.caption("Deterministic case operations: every action runs only when you click its button.")

    def parse_lines(value: str) -> List[str]:
        return [line.strip() for line in value.splitlines() if line.strip()]

    audience_role_options = ["Executive", "IT", "Security", "Legal/Privacy", "PR/Comms", "HR", "Compliance"]

    def load_scenario_info(case_dir: Path) -> Tuple[bool, bool, str]:
        scenario_yaml_path = case_dir / "20_delivery" / "scenario.yaml"
        if not scenario_yaml_path.exists():
            return False, False, ""
        try:
            scenario_obj = yaml.safe_load(scenario_yaml_path.read_text(encoding="utf-8"))
        except Exception:
            return True, False, ""
        injects = scenario_obj.get("injects", []) if isinstance(scenario_obj, dict) else []
        inject_rows = [row for row in injects if isinstance(row, dict)] if isinstance(injects, list) else []
        first_inject_id = str(inject_rows[0].get("id", "")).strip() if inject_rows else ""
        return True, bool(first_inject_id), first_inject_id

    def compute_preflight_status(case_dir: Path) -> Tuple[List[Tuple[str, str, str]], str]:
        intake_structured_exists = (case_dir / "10_inputs" / "intake_structured.json").exists()
        intake_notes_exists = (case_dir / "10_inputs" / "intake_notes.md").exists()
        ir_plan_exists = (case_dir / "10_inputs" / "ir_plan.txt").exists()
        threat_brief_exists = (case_dir / "10_inputs" / "threat_brief.md").exists()

        scenario_exists, scenario_has_injects, _ = load_scenario_info(case_dir)
        manifest_obj = load_json_safe(case_dir / "case_manifest.json") or {}
        scenario_obj = manifest_obj.get("scenario", {}) if isinstance(manifest_obj.get("scenario", {}), dict) else {}
        scenario_approved = bool(str(scenario_obj.get("approved_at_utc", "")).strip())

        package_dir = case_dir / "20_delivery" / "ttx_package"
        package_exists = package_dir.exists() and any(package_dir.iterdir())

        roster_obj = load_json_safe(participants_roster_path(case_dir)) or {}
        join_code_exists = bool(str(roster_obj.get("join_code", "")).strip())

        live_state_obj = load_live_state(live_state_path(case_dir))
        live_state_join = bool(
            isinstance(live_state_obj, dict)
            and str(live_state_obj.get("display_mode", "")).strip().lower() == "join"
            and str(live_state_obj.get("current_inject_id", "")).strip()
        )

        inputs_ready = intake_structured_exists and intake_notes_exists and ir_plan_exists and threat_brief_exists
        scenario_ready = scenario_exists and scenario_has_injects and scenario_approved
        session_ready = join_code_exists and live_state_join

        rows: List[Tuple[str, str, str]] = [
            ("Inputs", "🟢" if inputs_ready else ("🟡" if any([intake_structured_exists, intake_notes_exists, ir_plan_exists, threat_brief_exists]) else "🔴"), f"intake_structured={'yes' if intake_structured_exists else 'no'}, intake_notes={'yes' if intake_notes_exists else 'no'}, ir_plan={'yes' if ir_plan_exists else 'no'}, threat_brief={'yes' if threat_brief_exists else 'no'}"),
            ("Scenario", "🟢" if scenario_ready else ("🟡" if scenario_exists else "🔴"), f"scenario_yaml={'yes' if scenario_exists else 'no'}, injects={'yes' if scenario_has_injects else 'no'}, approved={'yes' if scenario_approved else 'no'}"),
            ("Package", "🟢" if package_exists else "🔴", "package exists" if package_exists else "package missing"),
            ("Session", "🟢" if session_ready else ("🟡" if join_code_exists or live_state_join else "🔴"), f"join_code={'yes' if join_code_exists else 'no'}, live_state_join={'yes' if live_state_join else 'no'}"),
        ]

        if not intake_structured_exists:
            next_action = "Save 10_inputs/intake_structured.json in Prepare tab"
        elif not scenario_exists:
            next_action = "Use Build tab Option A or Option C to create scenario.yaml"
        elif not scenario_has_injects:
            next_action = "Fix scenario.yaml to include at least one inject id"
        elif not scenario_approved:
            next_action = "Approve scenario in Build tab"
        elif not package_exists:
            next_action = "Build package in Build tab"
        elif not join_code_exists:
            next_action = "Open Run tab to generate join code"
        elif not live_state_join:
            next_action = "Click Start Session in Run tab"
        else:
            next_action = "Session is ready to run"

        return rows, next_action

    cases_root_default = str(os.environ.get("TTX_CASES_ROOT", "~/ttx_cases")).strip() or "~/ttx_cases"
    cases_root = Path(cases_root_default).expanduser().resolve()
    cases_root.mkdir(parents=True, exist_ok=True)

    case_dirs = sorted(
        [d for d in cases_root.iterdir() if d.is_dir() and (d / "case_manifest.json").exists()],
        key=lambda path: path.name.lower(),
    )
    case_label_to_dir: Dict[str, Path] = {}
    case_labels: List[str] = ["(select case)"]
    for case_dir in case_dirs:
        manifest_obj = load_json_safe(case_dir / "case_manifest.json") or {}
        manifest_case_id = str(manifest_obj.get("case_id", case_dir.name)).strip() or case_dir.name
        client_name = str(manifest_obj.get("client_name", "")).strip() or "(client)"
        label = f"{case_dir.name} — {manifest_case_id} — {client_name}"
        case_label_to_dir[label] = case_dir
        case_labels.append(label)

    if "show_create_case" not in st.session_state:
        st.session_state["show_create_case"] = False

    previous_case_dir = str(st.session_state.get("case_dir", "")).strip()
    previous_label = "(select case)"
    for label, case_dir in case_label_to_dir.items():
        if str(case_dir) == previous_case_dir:
            previous_label = label
            break

    selected_case_dir: Optional[Path] = None
    with st.sidebar.expander("Case & Status", expanded=(previous_label == "(select case)")):
        selected_label = st.selectbox(
            "Select case",
            options=case_labels,
            index=(case_labels.index(previous_label) if previous_label in case_labels else 0),
        )

        if selected_label != "(select case)":
            selected_case_dir = case_label_to_dir.get(selected_label)
            if selected_case_dir is not None:
                st.session_state["case_dir"] = str(selected_case_dir)
        else:
            st.session_state["case_dir"] = ""

        st.markdown("#### Preflight")
        if selected_case_dir is None:
            st.caption("Select a case to view preflight status.")
        else:
            preflight_rows, next_action = compute_preflight_status(selected_case_dir)
            compact_badges = " · ".join([f"{label} {icon}" for label, icon, _ in preflight_rows])
            st.markdown(compact_badges)
            st.caption(next_action)

    if st.sidebar.button("Create new case…", use_container_width=True):
        st.session_state["show_create_case"] = True

    create_case_success_message = str(st.session_state.pop("create_case_success_message", "")).strip()
    if create_case_success_message:
        st.success(create_case_success_message)

    if selected_case_dir is None or bool(st.session_state.get("show_create_case", False)):
        with st.container(border=True):
            st.subheader("Create new case")
            new_case_dir = st.text_input("case-dir", value=str(cases_root / "new_case"))
            new_case_id = st.text_input("case-id", value="")
            new_bundle_type = st.selectbox("bundle-type", options=["EXECUTIVE", "HALF_DAY", "FULL_DAY", "CUSTOM"], index=0)
            new_duration = st.number_input("duration", min_value=30, value=90, step=15)
            new_timezone = st.text_input("timezone", value="UTC")
            new_handling_label = st.selectbox("handling-label", options=["PUBLIC", "INTERNAL", "CONFIDENTIAL", "CLIENT_CONFIDENTIAL"], index=3)
            new_audience_roles = st.multiselect("audience-roles", options=audience_role_options, default=audience_role_options[:5])
            new_industry = st.text_input("industry", value="")
            new_region = st.text_input("region", value="")
            allow_new_case_in_repo = st.checkbox("allow_in_repo", value=False, key="console_create_case_allow_in_repo")

            if st.button("Create case"):
                requested_case_dir = Path(new_case_dir).expanduser().resolve()
                if not allow_new_case_in_repo:
                    try:
                        requested_case_dir.relative_to(REPO_ROOT)
                        st.error("Refusing to create case inside this repo. Enable allow_in_repo to override.")
                        requested_case_dir = None
                    except ValueError:
                        pass
                if requested_case_dir is not None:
                    cmd = [
                        sys.executable,
                        str(REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "init_ttx_case.py"),
                        "--case-dir",
                        str(requested_case_dir),
                        "--case-id",
                        new_case_id.strip(),
                        "--bundle-type",
                        new_bundle_type,
                        "--duration-minutes",
                        str(int(new_duration)),
                        "--timezone",
                        new_timezone.strip(),
                        "--handling-label",
                        new_handling_label,
                        "--audience-roles",
                        ", ".join(new_audience_roles),
                        "--industry",
                        new_industry.strip(),
                        "--region",
                        new_region.strip(),
                        "--force",
                    ]
                    if allow_new_case_in_repo:
                        cmd.append("--allow-in-repo")
                    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
                    if result.returncode == 0:
                        st.session_state["case_dir"] = str(requested_case_dir)
                        st.session_state["show_create_case"] = False
                        st.session_state["create_case_success_message"] = f"Created case: {requested_case_dir}"
                        st.rerun()
                    else:
                        st.error("Create case failed.")
                        st.code(result.stderr or result.stdout)

    preflight_rows: List[Tuple[str, str, str]] = []
    if selected_case_dir is not None:
        preflight_rows, _ = compute_preflight_status(selected_case_dir)
    if selected_case_dir is None:
        st.caption("Case: (none selected) • case_id: (n/a) • Status: not started")
    else:
        manifest_obj = load_json_safe(selected_case_dir / "case_manifest.json") or {}
        manifest_case_id = str(manifest_obj.get("case_id", "")).strip() or "(missing)"
        short_status = " · ".join([f"{label} {icon}" for label, icon, _ in preflight_rows])
        st.caption(f"Case: {selected_case_dir.name} • case_id: {manifest_case_id} • {short_status}")

    tab_prepare, tab_build, tab_run = st.tabs(["Prepare", "Build", "Run"])

    with tab_prepare:
        if selected_case_dir is None:
            st.info("Select a case first.")
        else:
            input_status_items = [
                ("intake_structured.json", selected_case_dir / "10_inputs" / "intake_structured.json", True),
                ("intake_notes.md", selected_case_dir / "10_inputs" / "intake_notes.md", False),
                ("ir_plan.txt", selected_case_dir / "10_inputs" / "ir_plan.txt", False),
                ("threat_brief.md", selected_case_dir / "10_inputs" / "threat_brief.md", False),
            ]
            st.markdown("#### Inputs status")
            status_row = []
            for label, path, required in input_status_items:
                exists = path.exists()
                icon = "🟢" if exists else ("🔴" if required else "🟡")
                status_row.append(f"{icon} {label}")
            st.markdown(" • ".join(status_row))

            with st.expander("Inputs details", expanded=False):
                for label, path, required in input_status_items:
                    exists = path.exists()
                    icon = "🟢" if exists else ("🔴" if required else "🟡")
                    st.markdown(f"- {icon} `10_inputs/{label}`")
                    if not exists:
                        warning_text = "required input missing" if required else "optional input not provided"
                        st.caption(f"Warning: {warning_text}. Path: {path}")

            taxonomy_categories = read_taxonomy_categories(REPO_ROOT)
            if not taxonomy_categories:
                st.error("No scenario categories found in dfir_backend/ttx/scenario_taxonomy.md.")

            manifest_path = selected_case_dir / "case_manifest.json"
            intake_path = selected_case_dir / "10_inputs" / "intake_structured.json"
            manifest_obj = load_json_safe(manifest_path) or {}
            if not manifest_obj:
                st.error("Selected case does not have a readable case_manifest.json.")
            else:
                manifest_scenario = manifest_obj.get("scenario", {})
                if not isinstance(manifest_scenario, dict):
                    manifest_scenario = {}
                intake_obj = load_json_safe(intake_path) or {}
                existing_preferred_category = str(intake_obj.get("preferred_scenario_category", "")).strip()
                existing_manifest_category = str(manifest_scenario.get("category", "")).strip()
                existing_category = existing_manifest_category or existing_preferred_category
                prepare_category_options = [""] + taxonomy_categories
                prepare_category_index = prepare_category_options.index(existing_category) if existing_category in prepare_category_options else 0
                selected_prepare_category = st.selectbox(
                    "Scenario category (required for Option C)",
                    options=prepare_category_options,
                    index=prepare_category_index,
                    key=f"console_prepare_scenario_category::{selected_case_dir}",
                    help="Option C uses this to select the module map + inject banks.",
                    placeholder="Select a scenario category",
                )
                if selected_prepare_category:
                    if selected_prepare_category != existing_manifest_category or selected_prepare_category != existing_preferred_category:
                        persist_case_scenario_category(selected_case_dir, selected_prepare_category)
                        manifest_obj = load_json_safe(manifest_path) or manifest_obj
                        intake_obj = load_json_safe(intake_path) or intake_obj
                        st.success("Scenario category saved to case_manifest.json and intake_structured.json.")

                with st.form("manifest_edit_form"):
                    manifest_client_name = st.text_input("client_name", value=str(manifest_obj.get("client_name", "")))
                    manifest_timezone = st.text_input("timezone", value=str(manifest_obj.get("timezone", "UTC")))
                    manifest_duration = st.number_input("duration_minutes", min_value=30, value=int(manifest_obj.get("duration_minutes", 90) or 90), step=15)
                    manifest_handling = st.text_input("handling_label", value=handling_label_from_manifest(manifest_obj))
                    saved_roles = [str(x).strip() for x in manifest_obj.get("audience_roles", []) if str(x).strip()]
                    default_roles = [role for role in saved_roles if role in audience_role_options] or audience_role_options[:5]
                    manifest_audience_roles = st.multiselect("audience_roles", options=audience_role_options, default=default_roles)
                    manifest_industry = st.text_input("industry", value=str(manifest_obj.get("industry", "")))
                    manifest_region = st.text_input("region", value=str(manifest_obj.get("region", "")))
                    save_manifest = st.form_submit_button("Save case_manifest.json")
                if save_manifest:
                    manifest_obj["client_name"] = manifest_client_name.strip()
                    manifest_obj["timezone"] = manifest_timezone.strip()
                    manifest_obj["duration_minutes"] = int(manifest_duration)
                    manifest_obj["handling_label"] = manifest_handling.strip()
                    manifest_obj["audience_roles"] = manifest_audience_roles
                    manifest_obj["industry"] = manifest_industry.strip()
                    manifest_obj["region"] = manifest_region.strip()
                    manifest_obj["last_updated_at_utc"] = now_iso()
                    write_json_atomic(manifest_path, manifest_obj)
                    st.success(f"Wrote {manifest_path}")

            intake_obj = load_json_safe(intake_path) or {}
            st.markdown("#### Structured intake")
            with st.form("intake_structured_form"):
                client_organization = st.text_input("client_organization", value=str(intake_obj.get("client_organization", "")))
                client_alias = st.text_input("client_alias", value=str(intake_obj.get("client_alias", "")))
                st.caption("Primary objectives — Example: Validate incident command handoffs during first 60 minutes.")
                primary_objectives = st.text_area("primary_objectives (one per line)", value="\n".join([str(x).strip() for x in intake_obj.get("primary_objectives", []) if str(x).strip()]), height=100)
                st.caption("Critical services — Example: VPN, identity provider, endpoint detection, and payroll.")
                critical_services = st.text_area("critical_services (one per line)", value="\n".join([str(x).strip() for x in intake_obj.get("critical_services", []) if str(x).strip()]), height=100)
                st.caption("Crown jewels — Example: Customer PII data warehouse and source code repositories.")
                crown_jewels_value = st.text_area("crown_jewels (one per line)", value="\n".join([str(x).strip() for x in intake_obj.get("crown_jewels", []) if str(x).strip()]), height=100)
                st.caption("Leadership concerns — Example: Regulatory reporting timeline and public statement readiness.")
                leadership_concerns_value = st.text_area("leadership_concerns (one per line)", value="\n".join([str(x).strip() for x in intake_obj.get("leadership_concerns", []) if str(x).strip()]), height=100)
                preferred_scenario_category = st.text_input("preferred_scenario_category", value=str(intake_obj.get("preferred_scenario_category", "")), disabled=True)
                save_intake = st.form_submit_button("Save intake_structured.json")
            if save_intake:
                payload = {
                    "client_organization": client_organization.strip(),
                    "client_alias": client_alias.strip(),
                    "primary_objectives": parse_lines(primary_objectives),
                    "critical_services": parse_lines(critical_services),
                    "crown_jewels": parse_lines(crown_jewels_value),
                    "leadership_concerns": parse_lines(leadership_concerns_value),
                    "preferred_scenario_category": preferred_scenario_category.strip(),
                }
                write_json_atomic(intake_path, payload)
                st.success(f"Wrote {intake_path}")

    with tab_build:
        if selected_case_dir is None:
            st.info("Select a case first.")
        else:
            scenario_yaml = selected_case_dir / "20_delivery" / "scenario.yaml"
            taxonomy_categories = read_taxonomy_categories(REPO_ROOT)
            scenario_candidates = sorted((REPO_ROOT / "dfir_backend" / "ttx" / "scenarios").glob("*.yaml"), key=lambda p: p.name.lower())
            base_options = ["(none)"] + [str(path.relative_to(REPO_ROOT)) for path in scenario_candidates]

            manifest_path = selected_case_dir / "case_manifest.json"
            manifest_obj = load_json_safe(manifest_path) or {}
            manifest_scenario = manifest_obj.get("scenario", {}) if isinstance(manifest_obj.get("scenario", {}), dict) else {}
            intake_path = selected_case_dir / "10_inputs" / "intake_structured.json"
            intake_obj = load_json_safe(intake_path) or {}
            existing_preferred_category = str(intake_obj.get("preferred_scenario_category", "")).strip()
            existing_manifest_category = str(manifest_scenario.get("category", "")).strip()
            existing_category = existing_manifest_category or existing_preferred_category
            build_category_options = [""] + taxonomy_categories
            build_category_index = build_category_options.index(existing_category) if existing_category in build_category_options else 0
            st.markdown("#### Scenario Source")
            scenario_source = st.radio(
                "Scenario source",
                options=["Option A: Base scenario", "Option C: Compile from library"],
                key=f"console_build_scenario_source::{selected_case_dir}",
            )

            if scenario_source == "Option A: Base scenario":
                selected_base_scenario = st.selectbox("Base scenario", options=base_options, index=0)
                if st.button("Generate scenario.yaml", type="primary"):
                    if selected_base_scenario == "(none)":
                        st.error("Select a base scenario first.")
                    else:
                        try:
                            src = (REPO_ROOT / selected_base_scenario).resolve()
                            scenario_yaml.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, scenario_yaml)
                            st.success(f"Copied {src} -> {scenario_yaml}")
                        except Exception as exc:
                            st.error(f"Option A copy failed: {exc}")
            else:
                selected_build_category = st.selectbox(
                    "Scenario category (required for Option C)",
                    options=build_category_options,
                    index=build_category_index,
                    key=f"console_build_scenario_category::{selected_case_dir}",
                    help="Option C uses this to select the module map + inject banks.",
                    placeholder="Select a scenario category",
                )
                if selected_build_category:
                    if selected_build_category != existing_manifest_category or selected_build_category != existing_preferred_category:
                        persist_case_scenario_category(selected_case_dir, selected_build_category)
                        st.success("Scenario category saved to case_manifest.json and intake_structured.json.")

                option_c_allowed = bool(selected_build_category)
                if not option_c_allowed:
                    st.error("Option C is disabled. Set 'Scenario category (required for Option C)' in Prepare or Build.")

                if st.button("Generate scenario.yaml", type="primary", disabled=not option_c_allowed):
                    cmd = [
                        sys.executable,
                        str(REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "compile_ttx_scenario_from_library.py"),
                        "--case-dir",
                        str(selected_case_dir),
                        "--force",
                        "--allow-in-repo",
                    ]
                    result = run_script(cmd)
                    if result.returncode == 0:
                        st.success("Option C compile completed.")
                        st.code(result.stdout)
                    else:
                        st.error("Option C compile failed.")
                        st.code(result.stderr or result.stdout)

            st.markdown("#### Workflow")
            validate_state_key = f"build_validate_passed::{selected_case_dir}"
            approval_phrase_key = f"build_approval_phrase::{selected_case_dir}"
            approved_at_utc = str(manifest_scenario.get("approved_at_utc", "")).strip()
            scenario_approved = bool(approved_at_utc)

            if validate_state_key not in st.session_state:
                st.session_state[validate_state_key] = False

            validate_passed = bool(st.session_state.get(validate_state_key, False))
            if scenario_approved:
                validate_passed = True
                st.session_state[validate_state_key] = True

            step_1_state = "✅ Complete" if validate_passed else "⏳ Pending"
            step_2_state = "✅ Complete" if scenario_approved else "⏳ Pending"
            step_3_state = "✅ Ready" if scenario_approved else "🔒 Locked"

            st.markdown(f"**Step 1: Validate** — {step_1_state}  ")
            st.caption("Deterministic schema + policy gate")
            if st.button("Validate scenario.yaml", type="primary"):
                if not scenario_yaml.exists():
                    st.error(f"Scenario file does not exist: {scenario_yaml}")
                    st.session_state[validate_state_key] = False
                else:
                    cmd = [
                        sys.executable,
                        str(REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_scenario_file.py"),
                        "--input",
                        str(scenario_yaml),
                    ]
                    result = run_script(cmd)
                    if result.returncode == 0:
                        st.success("Validation passed.")
                        st.session_state[validate_state_key] = True
                        st.code(result.stdout)
                    else:
                        st.error("Validation failed.")
                        st.session_state[validate_state_key] = False
                        st.code(result.stderr or result.stdout)

            st.markdown(f"**Step 2: Approve** — {step_2_state}  ")
            st.caption("Human gate for customer-ready scenario")
            approve_disabled = not bool(st.session_state.get(validate_state_key, False))
            if st.button("Approve scenario", disabled=approve_disabled):
                manifest_path = selected_case_dir / "case_manifest.json"
                manifest_obj = load_json_safe(manifest_path)
                if not manifest_obj:
                    st.error("Cannot approve scenario: case_manifest.json is missing or invalid.")
                elif not scenario_yaml.exists():
                    st.error("Cannot approve scenario: 20_delivery/scenario.yaml is missing.")
                else:
                    manifest_obj.setdefault("scenario", {})
                    if not isinstance(manifest_obj["scenario"], dict):
                        manifest_obj["scenario"] = {}
                    manifest_obj["scenario"]["scenario_yaml_path"] = "20_delivery/scenario.yaml"
                    manifest_obj["scenario"]["approved_at_utc"] = now_iso()
                    manifest_obj["state"] = "SCENARIO_APPROVED"
                    manifest_obj["last_updated_at_utc"] = now_iso()
                    write_json_atomic(manifest_path, manifest_obj)
                    st.success("Scenario approved.")
                    scenario_approved = True

            st.markdown(f"**Step 3: Build package** — {step_3_state}  ")
            st.caption("Generate SitMan/Facilitator/Participant packet")
            build_disabled = not scenario_approved
            if st.button("Build package", disabled=build_disabled):
                if not scenario_yaml.exists():
                    st.error(f"Scenario file does not exist: {scenario_yaml}")
                else:
                    out_dir = selected_case_dir / "20_delivery" / "ttx_package"
                    cmd = [
                        sys.executable,
                        str(REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "build_ttx_package_from_yaml.py"),
                        "--input",
                        str(scenario_yaml),
                        "--out-dir",
                        str(out_dir),
                        "--case-dir",
                        str(selected_case_dir),
                        "--force",
                        "--allow-in-repo",
                    ]
                    result = run_script(cmd)
                    if result.returncode == 0:
                        st.success("Package build completed.")
                        st.code(result.stdout)
                    else:
                        st.error("Package build failed.")
                        st.code(result.stderr or result.stdout)

            st.markdown("##### Optional: Combined gate")
            approval_phrase = st.text_input("Type confirmation", key=approval_phrase_key, placeholder="I_HAVE_REVIEWED_THE_SCENARIO")
            combined_disabled = (not bool(st.session_state.get(validate_state_key, False))) or approval_phrase.strip() != "I_HAVE_REVIEWED_THE_SCENARIO"
            if st.button("Approve + Build package", disabled=combined_disabled):
                manifest_path = selected_case_dir / "case_manifest.json"
                manifest_obj = load_json_safe(manifest_path)
                if not manifest_obj:
                    st.error("Cannot approve scenario: case_manifest.json is missing or invalid.")
                elif not scenario_yaml.exists():
                    st.error("Cannot approve scenario: 20_delivery/scenario.yaml is missing.")
                else:
                    manifest_obj.setdefault("scenario", {})
                    if not isinstance(manifest_obj["scenario"], dict):
                        manifest_obj["scenario"] = {}
                    manifest_obj["scenario"]["scenario_yaml_path"] = "20_delivery/scenario.yaml"
                    manifest_obj["scenario"]["approved_at_utc"] = now_iso()
                    manifest_obj["state"] = "SCENARIO_APPROVED"
                    manifest_obj["last_updated_at_utc"] = now_iso()
                    write_json_atomic(manifest_path, manifest_obj)
                    out_dir = selected_case_dir / "20_delivery" / "ttx_package"
                    cmd = [
                        sys.executable,
                        str(REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "build_ttx_package_from_yaml.py"),
                        "--input",
                        str(scenario_yaml),
                        "--out-dir",
                        str(out_dir),
                        "--case-dir",
                        str(selected_case_dir),
                        "--force",
                        "--allow-in-repo",
                    ]
                    result = run_script(cmd)
                    if result.returncode == 0:
                        st.success("Scenario approved and package build completed.")
                        st.code(result.stdout)
                    else:
                        st.error("Scenario approved, but package build failed.")
                        st.code(result.stderr or result.stdout)

    with tab_run:
        if selected_case_dir is None:
            st.info("Select a case first.")
        else:
            case_param = selected_case_dir.name
            roster = load_or_create_participants_roster(selected_case_dir)
            join_code = str(roster.get("join_code", "")).strip()

            port = st.get_option("server.port")
            try:
                port_num = int(port)
            except Exception:
                port_num = 8501

            env_share_base = shareable_base_url_from_env(port_num)
            default_base_url = env_share_base or f"http://127.0.0.1:{port_num}"
            base_url_key = f"run_base_url_{case_param}"
            if base_url_key not in st.session_state:
                st.session_state[base_url_key] = default_base_url

            st.markdown("### Base URL")
            quick_button_col1, quick_button_col2 = st.columns(2)
            with quick_button_col1:
                if st.button("Use localhost"):
                    st.session_state[base_url_key] = f"http://127.0.0.1:{port_num}"
            with quick_button_col2:
                if st.button("Use LAN IP"):
                    detected_lan_host = detect_lan_host()
                    if detected_lan_host and detected_lan_host not in {"<HOST>", "0.0.0.0", "127.0.0.1"}:
                        st.session_state[base_url_key] = f"http://{detected_lan_host}:{port_num}"
                    else:
                        st.warning("Unable to detect a LAN IP. Enter one manually.")

            base_url_input = st.text_input("Base URL", key=base_url_key)
            base_url = normalize_base_url(base_url_input, port_num)
            if base_url != base_url_input.strip():
                st.session_state[base_url_key] = base_url

            st.caption("Note: 0.0.0.0 is a bind address. Use 127.0.0.1 for local testing or your LAN IP for other devices.")

            participant_url = f"{base_url}/?mode=participant&case={case_param}&join={join_code}"
            display_url = f"{base_url}/?mode=display&case={case_param}&join={join_code}"
            facilitator_url = f"{base_url}/?mode=facilitator&case={case_param}&join={join_code}"

            st.markdown(f"### Join code: `{join_code}`")

            if st.button("Start Session", type="primary"):
                scenario_exists, scenario_has_injects, first_inject_id = load_scenario_info(selected_case_dir)
                if not scenario_exists:
                    st.error("Cannot start session: 20_delivery/scenario.yaml is missing.")
                elif not scenario_has_injects:
                    st.error("Cannot start session: scenario.yaml must include at least one inject with an id.")
                else:
                    load_or_create_participants_roster(selected_case_dir)
                    write_live_state(
                        selected_case_dir,
                        case_param,
                        first_inject_id,
                        False,
                        None,
                        race_enabled=False,
                        deputy_mode=False,
                        display_mode="join",
                    )
                    st.success("Session started. live_state.json initialized with display_mode=join.")

            st.link_button("Open Display", display_url)
            st.link_button("Open Facilitator DM", facilitator_url)
            st.link_button("Open Participant portal", participant_url)

            st.markdown("### Shareable join link")
            st.text_input("Participant join link", value=participant_url, disabled=True)
            st.text_input("Display link", value=display_url, disabled=True)
            st.text_input("Facilitator DM link", value=facilitator_url, disabled=True)


if APP_ARGS.mode != "facilitate" and query_mode not in {"participant", "display", "facilitator"}:
    render_console()
    st.stop()

# Defaults from case manifest (facilitator mode)
default_scenario_path = ""
default_export_dir = ""
case_summary = ""
facilitator_roster: Optional[Dict[str, Any]] = None

if CASE_DIR_PATH:
    facilitator_roster = load_or_create_participants_roster(CASE_DIR_PATH)
    case_assets_dir(CASE_DIR_PATH).mkdir(parents=True, exist_ok=True)

if CASE_DIR_PATH and CASE_MANIFEST:
    case_id = CASE_MANIFEST.get("case_id", "")
    state = CASE_MANIFEST.get("state", "")
    duration = CASE_MANIFEST.get("duration_minutes", "")
    tz = CASE_MANIFEST.get("timezone", "")
    handling = handling_label_from_manifest(CASE_MANIFEST)
    case_summary = f"Case: {case_id} • State: {state} • {duration} min • {tz} • Handling: {handling}"

    scenario_rel = str(CASE_MANIFEST.get("scenario", {}).get("scenario_yaml_path", "20_delivery/scenario.yaml"))
    logs_rel = str(CASE_MANIFEST.get("outputs", {}).get("logs_dir", "30_outputs/ttx_logs"))
    default_scenario_path = str(resolve_case_rel(scenario_rel) or "")
    default_export_dir = str(resolve_case_rel(logs_rel) or "")

# If scenario path empty in session, seed from case default
if not st.session_state["scenario_path"] and default_scenario_path:
    st.session_state["scenario_path"] = default_scenario_path


with st.sidebar:
    st.title("TTX Studio (Local)")

    if case_summary:
        st.caption(case_summary)

    st.markdown("Build package → export participant handouts → facilitate + scribe + export logs. Store client outputs outside git.")

    if CASE_DIR_PATH and isinstance(facilitator_roster, dict):
        join_code = str(facilitator_roster.get("join_code", "")).strip()
        port = st.get_option("server.port")
        try:
            port_num = int(port)
        except Exception:
            port_num = 8501
        case_id_for_link = ""
        if CASE_MANIFEST:
            case_id_for_link = str(CASE_MANIFEST.get("case_id", "")).strip()
        case_id_for_link = case_id_for_link or str(CASE_DIR_PATH.name).strip()
        host = detect_lan_host()

        st.divider()
        st.subheader("Participant Portal")
        st.text_input("Join code", value=join_code, disabled=True)
        participant_url = f"http://{host}:{port_num}/?mode=participant&case={case_id_for_link}&join={join_code}"
        st.text_input("Participant URL", value=participant_url, disabled=True)
        if host == "<HOST>":
            st.caption("Replace <HOST> with this facilitator machine's hostname or LAN IP before sharing.")

    # Navigation: facilitator-only mode hides build/export/validate pages
    if APP_ARGS.mode == "facilitate":
        pages = ["Facilitate"]
    elif APP_ARGS.mode == "console":
        pages = ["Console"]
    else:
        pages = ["Console", "Build Package", "Export Handouts (HTML)", "Validate Repo Scenarios", "Facilitate"]

    query_mode = str(st.query_params.get("mode", "")).strip().lower()
    forced_page = "Facilitate" if query_mode == "facilitator" else ""
    if forced_page:
        page = forced_page
        st.caption("Route locked by query parameter `mode=facilitator`.")
    else:
        default_index = 0 if APP_ARGS.mode in {"facilitate", "console"} else 0
        page = st.radio("Go to", pages, index=default_index)

    st.divider()
    with st.expander("Safety / data handling", expanded=False):
        st.caption("Keep outputs in approved storage. Enable repo writes only for synthetic content.")
        allow_in_repo = st.checkbox("Allow outputs inside this repo (synthetic only)", value=False, disabled=(APP_ARGS.mode == "facilitate"))
        overwrite_force = st.checkbox("Overwrite output files (--force)", value=True, disabled=False)

    if st.button("Reset facilitation state"):
        st.session_state["scenario_loaded"] = False
        st.session_state["scenario_obj"] = None
        st.session_state["timer_started"] = False
        st.session_state["timer_start_utc"] = ""
        st.session_state["manual_t_plus"] = 0
        st.session_state["notes_global"] = ""
        st.session_state["notes_hotwash"] = ""
        st.session_state["notes_by_inject"] = {}
        st.session_state["selected_inject_id"] = ""
        st.session_state["parking_lot"] = ""
        st.session_state["scoring"] = default_scoring()
        st.session_state["hide_numeric_scores_in_md"] = True
        st.session_state["hotwash_went_well"] = ""
        st.session_state["hotwash_gaps"] = ""
        st.session_state["hotwash_improvements"] = ""
        st.session_state["hotwash_open_questions"] = ""
        st.session_state["opening_script_text"] = ""
        st.session_state["opening_script_scenario_path"] = ""
        st.success("Reset complete.")


def load_scenario_yaml(path_str: str) -> Dict[str, Any]:
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Scenario YAML not found: {p}")
    obj = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Scenario YAML root must be a mapping/object.")
    return obj


def scenario_header(obj: Dict[str, Any]) -> Tuple[str, str, int]:
    sc = obj.get("scenario", {}) if isinstance(obj.get("scenario", {}), dict) else {}
    title = str(sc.get("title", "TTX Scenario")).strip()
    summary = str(sc.get("summary", "")).strip()
    duration = sc.get("duration_minutes", 0)
    try:
        duration_int = int(duration)
    except Exception:
        duration_int = 0
    return title, summary, duration_int


def inject_list(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    injects = obj.get("injects", [])
    if not isinstance(injects, list):
        return []
    out: List[Dict[str, Any]] = []
    for inj in injects:
        if isinstance(inj, dict):
            out.append(inj)
    # sort by t_plus_min if present
    def key_fn(x: Dict[str, Any]) -> int:
        v = x.get("t_plus_min", 0)
        try:
            return int(v)
        except Exception:
            return 0
    return sorted(out, key=key_fn)


def as_bullets(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def inject_label(inj: Dict[str, Any]) -> str:
    participant_prompt = str(inj.get("participant_prompt", "")).strip()
    first_line = participant_prompt.splitlines()[0].strip() if participant_prompt else ""
    if not first_line:
        return "(no participant prompt)"
    return first_line[:80]


def scoring_dimensions() -> List[Tuple[str, str]]:
    return [
        ("detection_awareness", "Detection & Awareness"),
        ("decision_making", "Decision-Making"),
        ("communication", "Communication"),
        ("escalation_authority", "Escalation & Authority"),
        ("legal_regulatory", "Legal & Regulatory Awareness"),
        ("documentation_tracking", "Documentation & Tracking"),
    ]


def scoring_snapshot() -> Dict[str, Dict[str, Any]]:
    raw = st.session_state.get("scoring", {})
    out: Dict[str, Dict[str, Any]] = {}
    for dimension_id, label in scoring_dimensions():
        entry = raw.get(dimension_id, {}) if isinstance(raw.get(dimension_id, {}), dict) else {}
        try:
            score = int(entry.get("score", 3))
        except Exception:
            score = 3
        out[dimension_id] = {
            "label": str(entry.get("label", label)).strip() or label,
            "score": min(5, max(1, score)),
            "evidence": str(entry.get("evidence", "")),
        }
    return out


def scoring_overall_avg(scoring: Dict[str, Dict[str, Any]]) -> float:
    scores = [int(v.get("score", 3)) for v in scoring.values()]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 1)


def scoring_priority_gaps(scoring: Dict[str, Dict[str, Any]]) -> List[str]:
    return [
        str(v.get("label", "")).strip()
        for v in scoring.values()
        if int(v.get("score", 3)) <= 2 and str(v.get("label", "")).strip()
    ]


def current_t_plus_minutes() -> int:
    if st.session_state["timer_started"] and st.session_state["timer_start_utc"]:
        try:
            start = datetime.fromisoformat(st.session_state["timer_start_utc"])
            now = datetime.now(timezone.utc)
            return max(0, int((now - start).total_seconds() // 60))
        except Exception:
            pass
    # fallback to manual
    try:
        return int(st.session_state["manual_t_plus"])
    except Exception:
        return 0


def notes_for_inject(inject_id: str) -> Dict[str, str]:
    notes_by = st.session_state["notes_by_inject"]
    if inject_id not in notes_by:
        notes_by[inject_id] = {
            "discussion": "",
            "decisions": "",
            "actions": "",
            "questions": "",
            "evidence": "",
            "timestamp_utc": now_iso(),
        }
    return notes_by[inject_id]


def build_opening_script(scenario_obj: Dict[str, Any]) -> str:
    sc = scenario_obj.get("scenario", {}) if isinstance(scenario_obj.get("scenario", {}), dict) else {}
    title = str(sc.get("title", "TTX Scenario")).strip()
    summary = str(sc.get("summary", "")).strip()
    threat_context = str(sc.get("threat_context", "")).strip()
    business_context = str(sc.get("business_context", "")).strip()
    objectives = sc.get("objectives", []) if isinstance(sc.get("objectives", []), list) else []

    script_lines: List[str] = []
    script_lines.append(f"Welcome to today's tabletop exercise: {title}.")
    if summary:
        script_lines.append(summary)
    if threat_context:
        script_lines.append(f"Threat context: {threat_context}")
    if business_context:
        script_lines.append(f"Business context: {business_context}")
    if objectives:
        first_three = [str(o).strip() for o in objectives[:3] if str(o).strip()]
        if first_three:
            script_lines.append("Today's objectives are: " + "; ".join(first_three) + ".")
    script_lines.append("Please verbalize assumptions, call out decision points clearly, and assign owners for follow-up actions.")
    return "\n\n".join(script_lines)


def build_facilitator_checklist(scenario_obj: Dict[str, Any], injects: List[Dict[str, Any]]) -> List[str]:
    sc = scenario_obj.get("scenario", {}) if isinstance(scenario_obj.get("scenario", {}), dict) else {}
    objectives = sc.get("objectives", []) if isinstance(sc.get("objectives", []), list) else []
    duration = sc.get("duration_minutes", "")

    checklist: List[str] = [
        "Open session, set exercise ground rules, and identify facilitator + scribe.",
        f"Confirm exercise duration ({duration} minutes) and timing cadence.",
        "Read opening script and align on scope, assumptions, and constraints.",
        "For each inject: capture discussion summary, decisions, and action items.",
        "Track unresolved questions and assign explicit owners/timeboxes.",
        "Run hotwash before close and capture top improvements.",
        "Export logs and confirm artifacts are stored in approved location.",
    ]
    for idx, obj in enumerate(objectives, start=1):
        objective = str(obj).strip()
        if objective:
            checklist.append(f"Objective {idx}: {objective}")
    checklist.append(f"Inject coverage check: {len(injects)} injects reviewed.")
    return checklist


def export_logs(export_dir: Path, scenario_path: str, scenario_obj: Dict[str, Any]) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)

    tplus = current_t_plus_minutes()
    injects = inject_list(scenario_obj)
    opening_script = str(st.session_state.get("opening_script_text", ""))
    facilitator_checklist = build_facilitator_checklist(scenario_obj, injects)
    scoring = scoring_snapshot()
    overall_avg = scoring_overall_avg(scoring)
    priority_gaps = scoring_priority_gaps(scoring)
    hide_numeric_in_md = bool(st.session_state.get("hide_numeric_scores_in_md", True))
    participant_rows: List[Dict[str, Any]] = []
    participant_responses_by_inject: Dict[str, List[Dict[str, Any]]] = {}
    participation_summary: Dict[str, Any] = {
        "total_participants": 0,
        "responses_per_inject": {},
        "completion_rate_per_inject": {},
    }
    if CASE_DIR_PATH:
        participant_rows, participant_responses_by_inject, participation_summary = collect_participant_responses(CASE_DIR_PATH, injects)

    payload = {
        "exported_at_utc": now_iso(),
        "case_dir": str(CASE_DIR_PATH) if CASE_DIR_PATH else "",
        "scenario_path": scenario_path,
        "t_plus_current_min": tplus,
        "timer_started": bool(st.session_state["timer_started"]),
        "timer_start_utc": st.session_state.get("timer_start_utc", ""),
        "notes_global": st.session_state.get("notes_global", ""),
        "session_notes": st.session_state.get("notes_global", ""),
        "notes_hotwash": st.session_state.get("notes_hotwash", ""),
        "hotwash_notes": st.session_state.get("notes_hotwash", ""),
        "parking_lot": st.session_state.get("parking_lot", ""),
        "scoring": {
            "model_path": "dfir_backend/ttx/scoring_model.md",
            "scale": "1-5",
            "dimensions": scoring,
            "overall_avg": overall_avg,
            "priority_gaps": priority_gaps,
            "hide_numeric_in_md": hide_numeric_in_md,
        },
        "hotwash_structured": {
            "went_well": st.session_state.get("hotwash_went_well", ""),
            "gaps": st.session_state.get("hotwash_gaps", ""),
            "improvements": st.session_state.get("hotwash_improvements", ""),
            "open_questions": st.session_state.get("hotwash_open_questions", ""),
        },
        "notes_by_inject": st.session_state.get("notes_by_inject", {}),
        "participant_responses_by_inject": participant_responses_by_inject,
        "participation_summary": participation_summary,
        "opening_script": opening_script,
        "facilitator_checklist": facilitator_checklist,
        "scenario": scenario_obj.get("scenario", {}),
        "injects": scenario_obj.get("injects", []),
    }

    json_path = export_dir / "scribe_runtime.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    title, summary, duration = scenario_header(scenario_obj)
    md_lines: List[str] = []
    md_lines.append("# Scribe Logs\n")
    md_lines.append(f"- Exported (UTC): {payload['exported_at_utc']}\n")
    if payload["case_dir"]:
        md_lines.append(f"- Case dir: {payload['case_dir']}\n")
    md_lines.append(f"- Scenario: {title}\n")
    if summary:
        md_lines.append(f"- Summary: {summary}\n")
    md_lines.append(f"- Duration (min): {duration}\n")
    md_lines.append(f"- Current T+ (min): {tplus}\n\n")

    if opening_script.strip():
        md_lines.append("## Opening Script\n\n")
        md_lines.append(opening_script.strip() + "\n\n")

    checklist_items = payload.get("facilitator_checklist", [])
    if isinstance(checklist_items, list) and checklist_items:
        md_lines.append("## Facilitator Run Sheet / Checklist\n\n")
        for item in checklist_items:
            md_lines.append(f"- [ ] {str(item)}\n")
        md_lines.append("\n")

    if payload["notes_global"].strip():
        md_lines.append("## Global Notes\n\n")
        md_lines.append(payload["notes_global"].strip() + "\n\n")

    scoring_payload = payload.get("scoring", {}) if isinstance(payload.get("scoring", {}), dict) else {}
    scoring_dimensions_payload = scoring_payload.get("dimensions", {}) if isinstance(scoring_payload.get("dimensions", {}), dict) else {}
    md_lines.append("## Scoring Summary (internal)\n\n")
    if bool(scoring_payload.get("hide_numeric_in_md", True)):
        md_lines.append("Overall readiness: (numeric captured in runtime JSON)\n\n")
        gaps = scoring_payload.get("priority_gaps", []) if isinstance(scoring_payload.get("priority_gaps", []), list) else []
        if gaps:
            md_lines.append("**Priority gaps:**\n")
            for gap in gaps:
                md_lines.append(f"- {str(gap)}\n")
            md_lines.append("\n")
    else:
        md_lines.append(f"Overall readiness: {scoring_payload.get('overall_avg', 0.0)}\n\n")
        md_lines.append("| Dimension | Score | Evidence |\n")
        md_lines.append("|---|---:|---|\n")
        for dimension_id, _ in scoring_dimensions():
            d = scoring_dimensions_payload.get(dimension_id, {}) if isinstance(scoring_dimensions_payload.get(dimension_id, {}), dict) else {}
            evidence = str(d.get("evidence", "")).replace("\n", "<br>")
            md_lines.append(f"| {str(d.get('label', ''))} | {int(d.get('score', 3))} | {evidence} |\n")
        md_lines.append("\n")

    if payload.get("parking_lot", "").strip():
        md_lines.append("## Parking Lot\n\n")
        md_lines.append(str(payload.get("parking_lot", "")).strip() + "\n\n")

    md_lines.append("## Inject Notes\n\n")
    for inj in injects:
        inj_id = str(inj.get("id", "")).strip()
        inj_t = inj.get("t_plus_min", "")
        participant_prompt = str(inj.get("participant_prompt", "")).strip()
        inj_label = inject_label(inj)
        md_lines.append(f"### Inject {inj_id} — T+{inj_t} — {inj_label}\n\n")
        if participant_prompt:
            md_lines.append("**Participant Prompt:**\n\n")
            md_lines.append(participant_prompt + "\n\n")
        n = payload["notes_by_inject"].get(inj_id, {})
        for k, label in [("discussion", "Discussion"), ("decisions", "Decisions"), ("actions", "Action Items"), ("questions", "Open Questions"), ("evidence", "Evidence/Artifacts")]:
            v = str(n.get(k, "")).strip()
            if v:
                md_lines.append(f"**{label}:**\n\n{v}\n\n")
        md_lines.append("\n")

    hotwash_structured = payload.get("hotwash_structured", {}) if isinstance(payload.get("hotwash_structured", {}), dict) else {}
    if any(str(hotwash_structured.get(k, "")).strip() for k in ["went_well", "gaps", "improvements", "open_questions"]):
        md_lines.append("## Hotwash (structured)\n\n")
        if str(hotwash_structured.get("went_well", "")).strip():
            md_lines.append("**What went well**\n\n")
            md_lines.append(str(hotwash_structured.get("went_well", "")).strip() + "\n\n")
        if str(hotwash_structured.get("gaps", "")).strip():
            md_lines.append("**Top gaps / risks**\n\n")
            md_lines.append(str(hotwash_structured.get("gaps", "")).strip() + "\n\n")
        if str(hotwash_structured.get("improvements", "")).strip():
            md_lines.append("**Top improvements (0/30/90 days)**\n\n")
            md_lines.append(str(hotwash_structured.get("improvements", "")).strip() + "\n\n")
        if str(hotwash_structured.get("open_questions", "")).strip():
            md_lines.append("**Open questions / follow-ups**\n\n")
            md_lines.append(str(hotwash_structured.get("open_questions", "")).strip() + "\n\n")

    if payload["notes_hotwash"].strip():
        md_lines.append("## Additional hotwash notes (freeform)\n\n")
        md_lines.append(payload["notes_hotwash"].strip() + "\n\n")

    md_path = export_dir / "scribe_logs_filled.md"
    md_path.write_text("".join(md_lines), encoding="utf-8")

    csv_path = export_dir / "scribe_inject_notes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["inject_id", "t_plus_min", "inject_label", "participant_prompt", "discussion", "decisions", "actions", "questions", "evidence"])
        for inj in injects:
            inj_id = str(inj.get("id", "")).strip()
            inj_label = inject_label(inj)
            inj_t = inj.get("t_plus_min", "")
            participant_prompt = str(inj.get("participant_prompt", "")).strip()
            n = payload["notes_by_inject"].get(inj_id, {})
            w.writerow([
                inj_id,
                inj_t,
                inj_label,
                participant_prompt,
                str(n.get("discussion", "")),
                str(n.get("decisions", "")),
                str(n.get("actions", "")),
                str(n.get("questions", "")),
                str(n.get("evidence", "")),
            ])

    participant_csv_path = export_dir / "participant_responses.csv"
    with participant_csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "inject_id",
            "epoch",
            "participant_id",
            "display_name",
            "role",
            "actions",
            "questions",
            "escalations",
            "decision",
            "decision_owner",
            "decision_owner_confidence",
            "evidence",
            "other_notes",
            "catch_all_response",
            "confidence",
        ])
        for row in participant_rows:
            w.writerow([
                str(row.get("inject_id", "")),
                int(row.get("epoch", 0)),
                str(row.get("participant_id", "")),
                str(row.get("display_name", "")),
                str(row.get("role", "")),
                str(row.get("actions", "")),
                str(row.get("questions", "")),
                str(row.get("escalations", "")),
                str(row.get("decision", "")),
                str(row.get("decision_owner", "")),
                str(row.get("decision_owner_confidence", "")),
                str(row.get("evidence", "")),
                str(row.get("other_notes", "")),
                str(row.get("catch_all_response", "")),
                str(row.get("confidence", "")),
            ])

    if CASE_DIR_PATH and CASE_MANIFEST:
        try:
            mp = CASE_DIR_PATH / "case_manifest.json"
            m = load_json(mp)
            m.setdefault("facilitation", {})
            m["facilitation"]["status"] = "COMPLETE"
            if not m["facilitation"].get("started_at_utc"):
                m["facilitation"]["started_at_utc"] = payload["timer_start_utc"] or ""
            m["facilitation"]["completed_at_utc"] = now_iso()
            m["last_updated_at_utc"] = now_iso()
            save_json(mp, m)
        except Exception:
            pass

    return export_dir


if page == "Console":
    render_console()


if page == "Build Package":
    st.header("Build Package")

    st.info("Recommended: build packages via the CLI case workflow. This page is for power users.")

    scenario_path = st.text_input("Scenario YAML path", value=st.session_state["scenario_path"])
    out_dir = st.text_input("Output directory (ttx_package)", value=str(Path.home() / "ttx_outputs" / "ttx_package"))

    if st.button("Build package"):
        p = Path(out_dir).expanduser().resolve()

        if p.is_relative_to(REPO_ROOT) and not allow_in_repo:
            st.error("Refusing to write outputs inside the repo. Enable the safety checkbox for synthetic only.")
        else:
            script = REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "build_ttx_package_from_yaml.py"
            cmd = [sys.executable, str(script), "--input", scenario_path, "--out-dir", str(p)]
            if overwrite_force:
                cmd.append("--force")
            if allow_in_repo:
                cmd.append("--allow-in-repo")

            r = run_script(cmd)
            if r.returncode == 0:
                st.success("Package built.")
                st.code(r.stdout)
            else:
                st.error("Build failed.")
                st.code(r.stderr or r.stdout)

elif page == "Export Handouts (HTML)":
    st.header("Export Handouts (HTML)")

    st.info("Recommended: export handouts via the CLI case workflow. This page is for power users.")

    pkg_dir = st.text_input("Package directory (contains sitman.md + participant_guide.md)", value="")
    out_dir = st.text_input("HTML output directory", value=str(Path.home() / "ttx_outputs" / "handouts_html"))
    make_zip = st.checkbox("Also create ZIP", value=True)

    if st.button("Export handouts"):
        p = Path(out_dir).expanduser().resolve()
        if p.is_relative_to(REPO_ROOT) and not allow_in_repo:
            st.error("Refusing to write outputs inside the repo. Enable the safety checkbox for synthetic only.")
        else:
            script = REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "export_ttx_handouts_html.py"
            cmd = [sys.executable, str(script), "--package-dir", pkg_dir, "--out-dir", str(p)]
            if make_zip:
                cmd.append("--zip")
            if allow_in_repo:
                cmd.append("--allow-in-repo")
            r = run_script(cmd)
            if r.returncode == 0:
                st.success("Handouts exported.")
                st.code(r.stdout)
            else:
                st.error("Export failed.")
                st.code(r.stderr or r.stdout)

elif page == "Validate Repo Scenarios":
    st.header("Validate Repo Scenarios")
    st.caption("Library hygiene: validates all scenarios committed to the repo.")

    if st.button("Run validator"):
        script = REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_scenarios.py"
        r = run_script([sys.executable, str(script)])
        if r.returncode == 0:
            st.success("Validation passed.")
            st.code(r.stdout)
        else:
            st.error("Validation failed.")
            st.code(r.stderr or r.stdout)

elif page == "Facilitate":
    st.header("Facilitate + Scribe (single workspace)")
    st.caption("Load a scenario YAML to begin facilitation.")

    def load_scenario_action(path_value: str) -> None:
        try:
            obj = load_scenario_yaml(path_value)
            st.session_state["scenario_loaded"] = True
            st.session_state["scenario_obj"] = obj
            st.session_state["scenario_path"] = path_value
            st.success("Scenario loaded.")
        except Exception as e:
            st.session_state["scenario_loaded"] = False
            st.session_state["scenario_obj"] = None
            st.error(str(e))

    colA, colB = st.columns([2, 1], vertical_alignment="top")

    with colB:
        st.subheader("Load scenario YAML")
        scenario_path = st.text_input("Scenario YAML path", value=st.session_state["scenario_path"])
        if st.button("Load scenario", key="load_scenario_sidebar"):
            load_scenario_action(scenario_path)

    with colA:
        if not st.session_state["scenario_loaded"] or not st.session_state["scenario_obj"]:
            st.markdown("## Load scenario")
            st.info("Start by loading the scenario YAML to unlock Run, Injects, and Debrief.")
            scenario_path_main = st.text_input("Scenario YAML path", value=st.session_state["scenario_path"], key="scenario_path_main")
            if st.button("Load scenario", type="primary", use_container_width=True, key="load_scenario_main"):
                load_scenario_action(scenario_path_main)
        else:
            obj = st.session_state["scenario_obj"]
            current_scenario_path = str(st.session_state.get("scenario_path", ""))
            if (not str(st.session_state.get("opening_script_text", "")).strip()) or st.session_state.get("opening_script_scenario_path", "") != current_scenario_path:
                st.session_state["opening_script_text"] = build_opening_script(obj)
                st.session_state["opening_script_scenario_path"] = current_scenario_path

            title, summary, duration = scenario_header(obj)
            sc = obj.get("scenario", {}) if isinstance(obj.get("scenario", {}), dict) else {}
            injects = inject_list(obj)
            objectives = sc.get("objectives", [])

            tab_run, tab_injects, tab_debrief = st.tabs(["Run", "Injects", "Debrief"])

            with tab_run:
                st.markdown("### Start exercise timer")
                if st.button("Start exercise timer", type="primary"):
                    st.session_state["timer_started"] = True
                    st.session_state["timer_start_utc"] = now_iso()
                    st.success("Timer started.")
                st.caption(f"Timer started: {st.session_state['timer_started']}")
                st.number_input("Manual T+ (min) override", min_value=0, value=int(st.session_state["manual_t_plus"]), key="manual_t_plus")
                st.caption(f"Current T+ (min): {current_t_plus_minutes()}")
                st.divider()

                st.markdown(f"## {title}")
                if summary:
                    st.markdown(summary)

                st.markdown("### Scenario Overview")
                st.markdown(f"- **Duration:** {duration} minutes")
                audiences = sc.get("audiences", []) if isinstance(sc.get("audiences", []), list) else []
                if audiences:
                    st.markdown(f"- **Audiences:** {', '.join(str(a) for a in audiences)}")
                assumptions = sc.get("assumptions", []) if isinstance(sc.get("assumptions", []), list) else []
                if assumptions:
                    st.markdown("- **Assumptions:**")
                    for assumption in assumptions:
                        st.write(f"  - {assumption}")

                st.markdown("### Opening Script")
                st.text_area("Facilitator opening script", key="opening_script_text", height=220)

                checklist = build_facilitator_checklist(obj, injects)
                with st.expander("Facilitator run sheet / checklist", expanded=True):
                    for idx, item in enumerate(checklist):
                        st.checkbox(item, key=f"checklist_{idx}")

                if isinstance(objectives, list) and objectives:
                    st.markdown("### Objectives")
                    for o in objectives:
                        st.write(f"- {o}")

                st.markdown("### Facilitator Notes (Global)")
                st.text_area("Global facilitation notes", key="notes_global", height=140)

            with tab_injects:
                if not injects:
                    st.warning("No injects found in scenario YAML.")
                else:
                    inject_ids = [str(i.get("id", "")) for i in injects]
                    if not st.session_state["selected_inject_id"]:
                        st.session_state["selected_inject_id"] = inject_ids[0]

                    current_idx = inject_ids.index(st.session_state["selected_inject_id"])
                    nav_left, nav_center, nav_right = st.columns([1, 3, 1], vertical_alignment="center")
                    with nav_left:
                        if st.button("⬅️ Prev", disabled=(current_idx == 0)):
                            st.session_state["selected_inject_id"] = inject_ids[current_idx - 1]
                            st.rerun()
                    with nav_center:
                        st.markdown(f"**Inject {current_idx + 1} of {len(inject_ids)}**")
                    with nav_right:
                        if st.button("Next ➡️", disabled=(current_idx >= len(inject_ids) - 1)):
                            st.session_state["selected_inject_id"] = inject_ids[current_idx + 1]
                            st.rerun()

                    selected = st.session_state["selected_inject_id"]
                    st.session_state["selected_inject_id"] = selected
                    current = next((i for i in injects if str(i.get("id", "")) == selected), injects[0])

                    live_state: Optional[Dict[str, Any]] = None
                    if CASE_DIR_PATH and CASE_MANIFEST:
                        current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                        live_state_file = live_state_path(CASE_DIR_PATH)
                        live_state = load_live_state(live_state_file)
                        if not isinstance(live_state, dict):
                            live_state = write_live_state(CASE_DIR_PATH, current_case_id, str(current.get("id", "")).strip(), False, None)
                        else:
                            existing_open_until = live_state.get("open_until_epoch", None)
                            normalized_open_until: Optional[int] = None
                            if existing_open_until is not None:
                                try:
                                    normalized_open_until = int(existing_open_until)
                                except Exception:
                                    normalized_open_until = None
                            existing_deputy_minutes = live_state.get("deputy_minutes", None)
                            normalized_deputy_minutes: Optional[int] = None
                            if existing_deputy_minutes is not None:
                                try:
                                    normalized_deputy_minutes = int(existing_deputy_minutes)
                                except Exception:
                                    normalized_deputy_minutes = None
                            if (
                                str(live_state.get("case_id", "")).strip() != current_case_id
                                or str(live_state.get("current_inject_id", "")).strip() != str(current.get("id", "")).strip()
                                or "race_enabled" not in live_state
                                or "deputy_mode" not in live_state
                                or "deputy_role_unavailable" not in live_state
                                or "deputy_minutes" not in live_state
                            ):
                                live_state = write_live_state(
                                    CASE_DIR_PATH,
                                    current_case_id,
                                    str(current.get("id", "")).strip(),
                                    bool(live_state.get("responses_open", False)),
                                    normalized_open_until,
                                    bool(live_state.get("race_enabled", False)),
                                    bool(live_state.get("deputy_mode", False)),
                                    str(live_state.get("deputy_role_unavailable", "")).strip() or None,
                                    normalized_deputy_minutes,
                                )

                    st.markdown(f"### Inject {current.get('id', '')}  ·  T+{current.get('t_plus_min', '')}")

                    race_enabled_ui = bool(isinstance(live_state, dict) and live_state.get("race_enabled", False))
                    deputy_mode_ui = bool(isinstance(live_state, dict) and live_state.get("deputy_mode", False))
                    deputy_role_options = [str(role).strip() for role in (CASE_MANIFEST.get("audience_roles", []) if CASE_MANIFEST else []) if str(role).strip()]
                    existing_deputy_role = str(live_state.get("deputy_role_unavailable", "")).strip() if isinstance(live_state, dict) else ""
                    if existing_deputy_role and existing_deputy_role not in deputy_role_options:
                        deputy_role_options.append(existing_deputy_role)
                    if not deputy_role_options:
                        deputy_role_options = ["(select role)"]
                    deputy_role_index = deputy_role_options.index(existing_deputy_role) if existing_deputy_role in deputy_role_options else 0
                    existing_deputy_minutes = live_state.get("deputy_minutes", None) if isinstance(live_state, dict) else None
                    deputy_minutes_ui = int(existing_deputy_minutes) if isinstance(existing_deputy_minutes, int) else 15

                    st.markdown("#### Inject Controls")
                    duration_presets = {
                        "90s": 90,
                        "3m": 180,
                        "5m": 300,
                        "8m": 480,
                        "custom": None,
                    }
                    selected_duration_preset = st.radio(
                        "Response window",
                        options=list(duration_presets.keys()),
                        index=2,
                        horizontal=True,
                        key=f"response_window_preset_{selected}",
                    )
                    custom_duration_seconds = st.number_input(
                        "Custom duration (seconds)",
                        min_value=30,
                        value=300,
                        step=30,
                        key=f"response_window_custom_seconds_{selected}",
                        disabled=(selected_duration_preset != "custom"),
                    )
                    selected_duration_seconds = (
                        int(custom_duration_seconds)
                        if selected_duration_preset == "custom"
                        else int(duration_presets[selected_duration_preset] or 300)
                    )
                    selected_duration_label = (
                        f"{selected_duration_seconds}s" if selected_duration_preset == "custom" else selected_duration_preset
                    )

                    with st.expander("Advanced", expanded=False):
                        race_enabled_ui = st.checkbox(
                            "Decision Rights Race",
                            value=race_enabled_ui,
                            key=f"race_enabled_{selected}",
                            help="ROI: Spot ownership misalignment early so you can redirect before decisions stall.",
                        )
                        deputy_mode_ui = st.toggle(
                            "Primary role unavailable",
                            value=deputy_mode_ui,
                            key=f"deputy_mode_{selected}",
                            help="ROI: Stress-test delegation paths and expose single-point-of-failure roles.",
                        )
                        selected_deputy_role = st.selectbox("Unavailable role", options=deputy_role_options, index=deputy_role_index, key=f"deputy_role_{selected}")
                        deputy_minutes_ui = st.number_input("Unavailable minutes", min_value=1, value=deputy_minutes_ui, step=1, key=f"deputy_minutes_{selected}")

                    display_control_left, display_control_right = st.columns(2)
                    with display_control_left:
                        if st.button("Show Join QR", key=f"show_join_qr_{selected}") and CASE_DIR_PATH and CASE_MANIFEST:
                            current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                            live_state = write_live_state(
                                CASE_DIR_PATH,
                                current_case_id,
                                str(current.get("id", "")).strip(),
                                bool(live_state.get("responses_open", False)),
                                live_state.get("open_until_epoch", None),
                                race_enabled_ui,
                                deputy_mode_ui,
                                selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None,
                                int(deputy_minutes_ui) if deputy_mode_ui else None,
                                "join",
                                None,
                            )
                    with display_control_right:
                        if st.button("Show Current Inject", key=f"show_current_inject_{selected}") and CASE_DIR_PATH and CASE_MANIFEST:
                            current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                            live_state = write_live_state(
                                CASE_DIR_PATH,
                                current_case_id,
                                str(current.get("id", "")).strip(),
                                bool(live_state.get("responses_open", False)),
                                live_state.get("open_until_epoch", None),
                                race_enabled_ui,
                                deputy_mode_ui,
                                selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None,
                                int(deputy_minutes_ui) if deputy_mode_ui else None,
                                "inject",
                                None,
                            )

                    if CASE_DIR_PATH:
                        assets_dir = CASE_DIR_PATH / "40_assets"
                        if assets_dir.is_dir():
                            image_options = sorted([
                                str(path.relative_to(CASE_DIR_PATH))
                                for path in assets_dir.iterdir()
                                if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
                            ])
                            if image_options:
                                selected_image = st.selectbox("Display image", options=image_options, key=f"display_image_{selected}")
                                if st.button("Show Image", key=f"show_display_image_{selected}") and CASE_MANIFEST:
                                    current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                                    live_state = write_live_state(
                                        CASE_DIR_PATH,
                                        current_case_id,
                                        str(current.get("id", "")).strip(),
                                        bool(live_state.get("responses_open", False)),
                                        live_state.get("open_until_epoch", None),
                                        race_enabled_ui,
                                        deputy_mode_ui,
                                        selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None,
                                        int(deputy_minutes_ui) if deputy_mode_ui else None,
                                        "image",
                                        selected_image,
                                    )

                    if CASE_DIR_PATH and CASE_MANIFEST and isinstance(live_state, dict):
                        current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                        normalized_deputy_role = selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None
                        normalized_deputy_minutes = int(deputy_minutes_ui) if deputy_mode_ui else None
                        live_state = write_live_state(
                            CASE_DIR_PATH,
                            current_case_id,
                            str(current.get("id", "")).strip(),
                            bool(live_state.get("responses_open", False)),
                            live_state.get("open_until_epoch", None),
                            race_enabled_ui,
                            deputy_mode_ui,
                            normalized_deputy_role,
                            normalized_deputy_minutes,
                            str(live_state.get("display_mode", "join")).strip() or "join",
                            str(live_state.get("display_image_path", "")).strip() or None,
                        )

                    control_left, control_mid, control_right = st.columns(3)
                    with control_left:
                        if st.button(f"Open responses ({selected_duration_label})") and CASE_DIR_PATH and CASE_MANIFEST:
                            current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                            live_state = write_live_state(
                                CASE_DIR_PATH,
                                current_case_id,
                                str(current.get("id", "")).strip(),
                                True,
                                int(time.time()) + selected_duration_seconds,
                                race_enabled_ui,
                                deputy_mode_ui,
                                selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None,
                                int(deputy_minutes_ui) if deputy_mode_ui else None,
                            )
                            st.success(f"Responses opened for {selected_duration_label}.")
                    with control_mid:
                        if st.button("Refresh submissions"):
                            st.rerun()
                    with control_right:
                        if st.button("Close early") and CASE_DIR_PATH and CASE_MANIFEST:
                            current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                            live_state = write_live_state(
                                CASE_DIR_PATH,
                                current_case_id,
                                str(current.get("id", "")).strip(),
                                False,
                                None,
                                race_enabled_ui,
                                deputy_mode_ui,
                                selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None,
                                int(deputy_minutes_ui) if deputy_mode_ui else None,
                            )
                            st.success("Responses closed.")

                    st.markdown("#### Display Controls")
                    if CASE_DIR_PATH and CASE_MANIFEST and isinstance(live_state, dict):
                        uploaded_image = st.file_uploader(
                            "Upload display image (PNG/JPG)",
                            type=["png", "jpg", "jpeg"],
                            key=f"display_image_uploader_{selected}",
                        )
                        if uploaded_image is not None:
                            upload_name = Path(str(uploaded_image.name)).name
                            upload_suffix = Path(upload_name).suffix.lower()
                            if upload_suffix in {".png", ".jpg", ".jpeg"}:
                                destination_path = case_assets_dir(CASE_DIR_PATH) / upload_name
                                destination_path.write_bytes(uploaded_image.getvalue())
                                st.success(f"Saved image: {upload_name}")
                            else:
                                st.error("Only PNG/JPG files are allowed.")

                        available_images = case_asset_image_files(CASE_DIR_PATH)
                        image_options = ["(none)"] + [img.name for img in available_images]
                        selected_image_name = st.selectbox(
                            "Image to display",
                            options=image_options,
                            index=0,
                            key=f"display_image_select_{selected}",
                        )
                        if st.button("Show Image", key=f"show_image_button_{selected}"):
                            if selected_image_name == "(none)":
                                st.error("Select an image first.")
                            else:
                                image_rel_path = str(Path("40_assets") / selected_image_name)
                                current_case_id = str(CASE_MANIFEST.get("case_id", "")).strip()
                                live_state = write_live_state(
                                    CASE_DIR_PATH,
                                    current_case_id,
                                    str(current.get("id", "")).strip(),
                                    bool(live_state.get("responses_open", False)),
                                    live_state.get("open_until_epoch", None),
                                    race_enabled_ui,
                                    deputy_mode_ui,
                                    selected_deputy_role if deputy_mode_ui and selected_deputy_role != "(select role)" else None,
                                    int(deputy_minutes_ui) if deputy_mode_ui else None,
                                    "image",
                                    image_rel_path,
                                )
                                st.success(f"Display now showing: {selected_image_name}")

                    if isinstance(live_state, dict):
                        st.caption(
                            f"Live state — open: {bool(live_state.get('responses_open', False))}, "
                            f"open_until_epoch: {live_state.get('open_until_epoch', None)}"
                        )

                    responses_are_open = bool(isinstance(live_state, dict) and live_state.get("responses_open", False))
                    if responses_are_open and CASE_DIR_PATH:
                        if callable(st_autorefresh):
                            st_autorefresh(interval=2500, key=f"facilitator_inject_completion_{str(current.get('id', '')).strip()}")
                        completion = inject_completion_status(CASE_DIR_PATH, str(current.get("id", "")).strip())
                        st.markdown(
                            f"**Responses: {int(completion.get('submitted_count', 0))} / {int(completion.get('total_participants', 0))} submitted**"
                        )
                        missing = completion.get("missing_participants", []) if isinstance(completion.get("missing_participants", []), list) else []
                        if missing:
                            with st.expander("Missing participants", expanded=False):
                                for participant in missing:
                                    display_name = str(participant.get("display_name", "")).strip() or "(unknown)"
                                    role = str(participant.get("role", "")).strip()
                                    if role:
                                        st.write(f"- {display_name} ({role})")
                                    else:
                                        st.write(f"- {display_name}")

                    responses_path_dir = participant_responses_dir(CASE_DIR_PATH) if CASE_DIR_PATH else None
                    race_enabled_current = bool(isinstance(live_state, dict) and live_state.get("race_enabled", False))
                    if race_enabled_current and responses_path_dir and responses_path_dir.exists():
                        owner_counts: Dict[str, int] = {}
                        total_submitted = 0
                        for response_file in responses_path_dir.glob("*.jsonl"):
                            try:
                                with response_file.open("r", encoding="utf-8") as handle:
                                    for raw_line in handle:
                                        line = raw_line.strip()
                                        if not line:
                                            continue
                                        obj = json.loads(line)
                                        if not isinstance(obj, dict):
                                            continue
                                        if str(obj.get("inject_id", "")).strip() != str(current.get("id", "")).strip():
                                            continue
                                        decision_owner_value = str(obj.get("decision_owner", "")).strip()
                                        if not decision_owner_value:
                                            continue
                                        owner_counts[decision_owner_value] = owner_counts.get(decision_owner_value, 0) + 1
                                        total_submitted += 1
                            except Exception:
                                continue

                        st.markdown("#### Decision Rights Race")
                        if total_submitted == 0:
                            st.info("No Decision Rights Race submissions yet for this inject.")
                        else:
                            race_rows = [{"decision_owner": k, "count": v} for k, v in sorted(owner_counts.items(), key=lambda item: item[0])]
                            st.table(race_rows)
                            st.bar_chart(race_rows, x="decision_owner", y="count")
                            alignment_score = max(owner_counts.values()) / total_submitted
                            st.metric("alignment score", f"{alignment_score:.2f}")
                    participant_prompt = str(current.get("participant_prompt", "")).strip()
                    facilitator_guidance = str(current.get("facilitator_guidance", "")).strip()
                    expected_discussion = as_bullets(current.get("expected_discussion", []))
                    expected_decisions = as_bullets(current.get("expected_decisions", []))
                    evaluation_criteria = as_bullets(current.get("evaluation_criteria", []))
                    evidence_refs = as_bullets(current.get("evidence_refs", []))

                    if participant_prompt:
                        st.markdown("#### Participant Prompt")
                        st.markdown(participant_prompt)
                    if facilitator_guidance:
                        st.markdown("#### Facilitator Guidance")
                        st.markdown(facilitator_guidance)

                    if expected_discussion or expected_decisions:
                        st.markdown("#### Expected conversation and decisions")
                        if expected_discussion:
                            st.markdown("**Expected discussion:**")
                            for item in expected_discussion:
                                st.write(f"- {item}")
                        if expected_decisions:
                            st.markdown("**Expected decisions:**")
                            for item in expected_decisions:
                                st.write(f"- {item}")

                    if evaluation_criteria:
                        st.markdown("#### Evaluation")
                        st.markdown("**Evaluation criteria:**")
                        for item in evaluation_criteria:
                            st.write(f"- {item}")

                    if evidence_refs:
                        st.markdown("#### Evidence")
                        st.markdown("**Evidence refs:**")
                        for item in evidence_refs:
                            st.write(f"- {item}")

                    n = notes_for_inject(selected)
                    note_tab_discussion, note_tab_decisions, note_tab_actions, note_tab_questions, note_tab_evidence = st.tabs(["Discussion", "Decisions", "Actions", "Questions", "Evidence"])
                    with note_tab_discussion:
                        st.text_area("Discussion summary", value=n.get("discussion", ""), key=f"discussion_{selected}", height=110)
                    with note_tab_decisions:
                        st.text_area("Decisions", value=n.get("decisions", ""), key=f"decisions_{selected}", height=110)
                    with note_tab_actions:
                        st.text_area("Action items", value=n.get("actions", ""), key=f"actions_{selected}", height=110)
                    with note_tab_questions:
                        st.text_area("Open questions", value=n.get("questions", ""), key=f"questions_{selected}", height=110)
                    with note_tab_evidence:
                        st.text_area("Evidence / artifacts", value=n.get("evidence", ""), key=f"evidence_{selected}", height=110)

                    current_notes = {
                        "discussion": st.session_state.get(f"discussion_{selected}", ""),
                        "decisions": st.session_state.get(f"decisions_{selected}", ""),
                        "actions": st.session_state.get(f"actions_{selected}", ""),
                        "questions": st.session_state.get(f"questions_{selected}", ""),
                        "evidence": st.session_state.get(f"evidence_{selected}", ""),
                    }
                    previous_notes = {
                        "discussion": str(n.get("discussion", "")),
                        "decisions": str(n.get("decisions", "")),
                        "actions": str(n.get("actions", "")),
                        "questions": str(n.get("questions", "")),
                        "evidence": str(n.get("evidence", "")),
                    }
                    timestamp_utc = str(n.get("timestamp_utc", now_iso()))
                    if any(current_notes[k] != previous_notes[k] for k in current_notes):
                        timestamp_utc = now_iso()
                    notes_by = st.session_state["notes_by_inject"]
                    notes_by[selected] = {
                        "discussion": current_notes["discussion"],
                        "decisions": current_notes["decisions"],
                        "actions": current_notes["actions"],
                        "questions": current_notes["questions"],
                        "evidence": current_notes["evidence"],
                        "timestamp_utc": timestamp_utc,
                    }
                    st.session_state["notes_by_inject"] = notes_by

            with tab_debrief:
                st.markdown("## Parking Lot")
                st.text_area("Parking lot (capture questions / topics to follow up later)", key="parking_lot", height=140)

                with st.expander("Export logs and AAR tools", expanded=False):
                    export_dir_val = st.text_input("Export directory (secure storage recommended)", value=(default_export_dir or ""))
                    if st.button("Export scribe logs (MD + CSV + JSON)"):
                        out = Path(export_dir_val).expanduser().resolve()
                        if out.is_relative_to(REPO_ROOT) and not allow_in_repo:
                            st.error("Refusing to write outputs inside the repo. Enable the safety checkbox for synthetic only.")
                        else:
                            exported = export_logs(out, st.session_state["scenario_path"], st.session_state["scenario_obj"])
                            st.success(f"Exported to: {exported}")

                    aar_paths = aar_manifest_paths()
                    can_generate_aar = APP_ARGS.case_dir.strip() != "" and aar_paths is not None

                    if st.button("Generate AAR Draft", disabled=not can_generate_aar):
                        if not aar_paths:
                            st.error("AAR generation requires --case-dir with a valid case_manifest.json.")
                        else:
                            draft_builder = REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "build_aar_draft_from_runtime.py"
                            cmd = [
                                sys.executable,
                                str(draft_builder),
                                "--case-dir",
                                APP_ARGS.case_dir.strip(),
                            ]
                            r = run_script(cmd)
                            if r.returncode == 0:
                                st.success(f"AAR draft generated: {aar_paths['aar_draft_path']}")
                                if r.stdout.strip():
                                    st.code(r.stdout)
                            else:
                                st.error("AAR draft generation failed.")
                                st.code(r.stderr or r.stdout)

                    if st.button("Build AAR AI bundle (paste-ready)", disabled=not can_generate_aar):
                        if not aar_paths:
                            st.error("AAR AI bundle requires --case-dir with a valid case_manifest.json.")
                        else:
                            bundle_builder = REPO_ROOT / "dfir_backend" / "ttx" / "scripts" / "build_aar_ai_bundle.py"
                            cmd = [
                                sys.executable,
                                str(bundle_builder),
                                "--scenario-yaml",
                                str(aar_paths["scenario_yaml"]),
                                "--runtime-json",
                                str(aar_paths["runtime_json"]),
                                "--out-dir",
                                str(aar_paths["out_dir"]),
                            ]
                            if aar_paths["ir_plan_path"].exists():
                                cmd.extend(["--ir-plan", str(aar_paths["ir_plan_path"])])
                            if aar_paths["intake_notes_path"].exists():
                                cmd.extend(["--intake-notes", str(aar_paths["intake_notes_path"])])
                            r = run_script(cmd)
                            if r.returncode == 0:
                                st.success(f"AAR AI bundle generated: {aar_paths['aar_ai_bundle_path']}")
                                if r.stdout.strip():
                                    st.code(r.stdout)
                            else:
                                st.error("AAR AI bundle generation failed.")
                                st.code(r.stderr or r.stdout)

                st.markdown("## Hotwash (Debrief)")
                st.caption("Run a 5–10 minute structured debrief; these fields feed the AAR output.")
                st.text_area("What went well (3–5 bullets)", key="hotwash_went_well", height=120)
                st.text_area("Top gaps / risks (3–5 bullets)", key="hotwash_gaps", height=120)
                st.text_area("Top improvements (0/30/90 days; include owner roles if possible)", key="hotwash_improvements", height=120)
                st.text_area("Open questions / follow-ups", key="hotwash_open_questions", height=120)
                st.text_area("Additional hotwash notes (freeform)", key="notes_hotwash", height=160)

                with st.expander("Scoring (internal)", expanded=False):
                    st.caption("Score each dimension from 1 (low readiness) to 5 (high readiness) and add concrete examples.")
                    for dimension_id, label in scoring_dimensions():
                        score_value = int(st.session_state["scoring"].get(dimension_id, {}).get("score", 3))
                        evidence_value = str(st.session_state["scoring"].get(dimension_id, {}).get("evidence", ""))
                        st.markdown(f"### {label}")
                        score_val = st.slider("Score (1-5)", min_value=1, max_value=5, value=score_value, key=f"score_{dimension_id}")
                        evidence_val = st.text_area("2–4 concrete examples (bullets)", value=evidence_value, key=f"score_evidence_{dimension_id}", height=100)
                        st.session_state["scoring"][dimension_id] = {"label": label, "score": int(score_val), "evidence": evidence_val}

                    score_snapshot = scoring_snapshot()
                    st.markdown(f"**Overall average readiness score:** {scoring_overall_avg(score_snapshot)}")
                    gaps = scoring_priority_gaps(score_snapshot)
                    if gaps:
                        st.markdown("**Priority gaps (score <= 2):**")
                        for gap in gaps:
                            st.write(f"- {gap}")
                    else:
                        st.caption("No priority gaps (all dimensions scored above 2).")
                    st.checkbox("Hide numeric scores in markdown export", key="hide_numeric_scores_in_md")

                    scoring_model_path = REPO_ROOT / "dfir_backend" / "ttx" / "scoring_model.md"
                    with st.expander("View scoring model"):
                        if scoring_model_path.exists():
                            st.markdown(scoring_model_path.read_text(encoding="utf-8"))
                        else:
                            st.warning("Scoring model not found at dfir_backend/ttx/scoring_model.md")

else:
    st.error("Unknown page.")
