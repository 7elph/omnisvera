"""Read terminal MCP evidence without starting jobs, acquiring leases or running proposals.

Only bounded local TEMP JSON is read. The returned summary deliberately excludes
scenario text, notes, private snapshots, filesystem paths and logs. It is evidence
about EXISTING code, never certification that proposal JSON was executed.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile


RUN_ID_RE = re.compile(r"test-[0-9a-f]{32}")
MAX_JOB_BYTES = 1_000_000
MAX_REPORT_BYTES = 8_000_000
ACTORS = {"raziel", "morthak", "vezemir", "dorn7"}
SCOPE = "existing_code_only_not_proposal_execution"


def default_test_root() -> Path:
    checkout = Path(__file__).resolve().parents[2]
    digest = hashlib.sha256(str(checkout).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / ("omnisvera-ai-tests-" + digest)


def _safe_file(root: Path, relative: str) -> Path:
    path = root
    for part in Path(relative).parts:
        path = path / part
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Referência de evidência insegura")
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Referência de evidência insegura")
    return resolved


def _object(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("Campo JSON duplicado")
        value[key] = child
    return value


def _invalid_constant(value):
    raise ValueError("Valor JSON não finito")


def _read_json(path: Path, maximum: int) -> tuple[dict, bytes]:
    if not path.is_file():
        raise FileNotFoundError("Ensaio ou relatório não encontrado")
    if path.stat().st_size > maximum:
        raise ValueError("Evidência excede o limite de tamanho")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Evidência excede o limite de tamanho")
    try:
        payload = json.loads(raw, parse_constant=_invalid_constant, object_pairs_hook=_object)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("JSON de evidência inválido") from error
    if not isinstance(payload, dict):
        raise ValueError("Objeto de evidência inválido")
    return payload, raw


def read_test_run_evidence(run_id: str, *, root: Path | None = None) -> dict:
    if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id inválido")
    temporary = Path(tempfile.gettempdir()).resolve()
    raw_root = Path(root) if root is not None else default_test_root()
    raw_root = raw_root.absolute()
    resolved_root = raw_root.resolve()
    if not raw_root.is_relative_to(temporary) or not resolved_root.is_relative_to(temporary) or resolved_root == temporary:
        raise ValueError("Evidência deve permanecer em TEMP")
    for component in (raw_root, *raw_root.parents):
        if component == temporary:
            break
        if component.is_symlink() or (hasattr(component, "is_junction") and component.is_junction()):
            raise ValueError("Raiz de evidência insegura")
    job, _ = _read_json(_safe_file(resolved_root, run_id + "/job.json"), MAX_JOB_BYTES)
    report, raw_report = _read_json(_safe_file(resolved_root, run_id + "/evidence/sheet-test-report.json"), MAX_REPORT_BYTES)
    if (type(job.get("schema_version")) is not int or job["schema_version"] != 1
            or job.get("run_id") != run_id or job.get("state") != "COMPLETED"
            or job.get("verdict") not in {"PASS", "FAIL"}):
        raise ValueError("Ensaio não possui resultado terminal válido")
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1 or report.get("kind") != "sheet_test_evidence":
        raise ValueError("Formato de relatório não suportado")
    actors = job.get("actors")
    if (not isinstance(actors, list) or not actors or len(actors) > 4
            or any(not isinstance(actor, str) or actor not in ACTORS for actor in actors)
            or len(set(actors)) != len(actors)):
        raise ValueError("Atores de evidência inválidos")
    characters = report.get("characters")
    if not isinstance(characters, dict) or set(characters) != set(actors):
        raise ValueError("Atores do relatório não correspondem ao ensaio")
    coverage_statuses = {"PASS", "FAIL", "PENDING", "ASSISTED", "RULE_BLOCKED", "UNAVAILABLE"}
    for character in characters.values():
        if not isinstance(character, dict) or not isinstance(character.get("entries"), list):
            raise ValueError("Cobertura de personagem inválida")
        if any(not isinstance(entry, dict) or entry.get("status") not in coverage_statuses
               for entry in character["entries"]):
            raise ValueError("Cobertura de ação inválida")
        character_counts = character.get("counts")
        if (not isinstance(character_counts, dict) or any(key not in coverage_statuses or type(value) is not int
                or value < 0 for key, value in character_counts.items())
                or {key: value for key, value in character_counts.items() if value}
                != dict(Counter(entry["status"] for entry in character["entries"]))):
            raise ValueError("Contagens da ficha não correspondem à cobertura")
    counts, scenarios = report.get("scenario_counts"), report.get("scenarios")
    if (not isinstance(counts, dict) or any(key not in {"PASS", "FAIL", "EXPECTED_BLOCK"}
            or type(value) is not int or value < 0 for key, value in counts.items())
            or not isinstance(scenarios, list) or not scenarios):
        raise ValueError("Contagens de cenário inválidas")
    if any(not isinstance(scenario, dict) or scenario.get("status") not in {"PASS", "FAIL", "EXPECTED_BLOCK"}
           or scenario.get("actor") not in actors for scenario in scenarios):
        raise ValueError("Cenário de evidência inválido")
    if {key: value for key, value in counts.items() if value} != dict(Counter(scenario["status"] for scenario in scenarios)):
        raise ValueError("Contagens não correspondem aos cenários executados")
    ui = report.get("ui_smoke") or {}
    if not isinstance(ui, dict) or ui.get("status") not in {None, "PASS", "FAIL", "INCONCLUSIVE", "SKIPPED", "NOT_RUN"}:
        raise ValueError("Evidência visual inválida")
    requested_ui = job.get("ui", False)
    if type(requested_ui) is not bool:
        raise ValueError("Configuração de ensaio inválida")
    suite = job.get("ui_suite", "full")
    if suite not in {"full", "combat", "lightning", "hemomancy", "vampiric", "necromancy", "rest", "passives", "summon_turns", "friday", "oct24"}:
        raise ValueError("Lote de ensaio inválido")
    if ui.get("suite") is not None and ui["suite"] != suite:
        raise ValueError("Lote visual não corresponde ao ensaio")
    ui_status = ui.get("status") or "NOT_RUN"
    if requested_ui and ui_status not in {"PASS", "FAIL"} and not counts.get("FAIL"):
        raise ValueError("Ensaio sem evidência visual conclusiva")
    failed = bool(counts.get("FAIL")) or (requested_ui and ui_status == "FAIL")
    if (type(job.get("exit_code")) is not int or job["exit_code"] != (1 if failed else 0)
            or job["verdict"] != ("FAIL" if failed else "PASS")):
        raise ValueError("Resultado e código de saída inconsistentes")
    return {"run_id": run_id, "state": "COMPLETED", "verdict": job["verdict"],
            "scenario_counts": {key: value for key, value in counts.items() if value},
            "actors": sorted(actors), "ui_suite": suite, "ui_status": ui_status,
            "certification_ready": False, "scope": SCOPE,
            "report_sha256": hashlib.sha256(raw_report).hexdigest()}
