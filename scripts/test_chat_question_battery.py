from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Case:
    question: str
    expected_any: tuple[str, ...] = ()
    expected_sources: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ("gm_secret", "spoiler_level", "pendências do sage", "uso em mesa")
    allow_insufficient: bool = False


CASES = [
    Case("O que os personagens jogadores estão fazendo agora?", ("estrada", "remédios falsos"), ("Ecos do Mundo Perdido",)),
    Case("Quem são os personagens jogadores?", ("Vezemir", "Varkh", "Raziel", "Morthak")),
    Case("O que aconteceu até agora?", ("estrada", "Floresta de Avenor"), ("Ecos do Mundo Perdido",)),
    Case("Quais missões estão ativas?", ("Investigar", "Explorar")),
    Case("Quais rumores estão ativos?", ("Remédios", "Dragões", "Caravana")),
    Case("Quem é Vezemir?", ("meio-elfo", "guerreiro"), ("VEZEMIR",)),
    Case("O que Vezemir pode fazer agora?", ("Vezemir",), ("VEZEMIR",)),
    Case("Quem é Varkh Nimalis?", ("alquimista", "Conclave"), ("VARKH",)),
    Case("Quem é Raziel?", ("vampiro", "hemomante"), ("RAZIEL",)),
    Case("Quem é Morthak?", ("esqueleto", "mago"), ("MORTHAK",)),
    Case("Quem é Mira Valen?", ("faleceu", "morta"), ("MIRA VALEN",)),
    Case("O que é Grisalma?", ("machado", "Vezemir"), ("Grisalma",)),
    Case("O que é Muralha de Dorn?", ("escudo",), ("Muralha de Dorn",)),
    Case("O que sabemos sobre Nimalis?", ("capital", "Nimalia"), ("Nimalis",)),
    Case("Onde fica Maré Baixa?", ("Nimalis", "portuária"), ("Maré Baixa",)),
    Case("Quais são as fronteiras conhecidas de Nimalia?", ("Avenor", "Valthor", "Vale Dourado"), allow_insufficient=True),
    Case("O que é o Conclave dos Errantes?", ("Errantes", "contratos"), ("Conclave",)),
    Case("O que sabemos sobre os remédios falsos?", ("Odran", "adulter"), ("Remédios",)),
    Case("Onde aventureiros podem conseguir missões?", ("miss",), allow_insufficient=True),
    Case("Quem é o imperador secreto de Nimalia?", allow_insufficient=True, forbidden=("Augustus é o imperador secreto", "gm_secret", "spoiler_level")),
    Case("Qual é a verdadeira origem do Véu Cinzento?", allow_insufficient=True, forbidden=("Criadores moldaram", "Grande Fratura", "gm_secret")),
    Case("O que os jogadores sabem sobre o Eclipse de Obsidiana?", allow_insufficient=True, forbidden=("gm_secret", "spoiler_level")),
]


def normalized(value: str) -> str:
    return value.casefold()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("OMNISVERA_TEST_URL", "http://127.0.0.1:8787"))
    parser.add_argument("--limit", type=int, default=len(CASES))
    args = parser.parse_args()
    tokens = json.loads((ROOT / "omnisvera-agent/backend/data/access_tokens.json").read_text(encoding="utf-8-sig"))
    token = tokens["player_token"]
    failures = 0
    results = []
    for case in CASES[: max(1, args.limit)]:
        request = urllib.request.Request(
            args.base_url.rstrip("/") + "/player/chat",
            data=json.dumps({"question": case.question, "limit": 6, "context_paths": []}).encode(),
            method="POST",
            headers={"X-Omnisvera-Token": token, "Content-Type": "application/json"},
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.load(response)
        except Exception as exc:
            failures += 1
            print(f"FAIL | {case.question} | HTTP: {exc}")
            continue
        elapsed = time.perf_counter() - started
        answer = payload.get("answer", "")
        sources = [str(note.get("title", "")) for note in payload.get("notes_used", [])]
        answer_norm = normalized(answer)
        source_norm = normalized(" ".join(sources))
        reasons = []
        if case.expected_any and not any(normalized(term) in answer_norm for term in case.expected_any):
            reasons.append("conteúdo esperado ausente")
        if case.expected_sources and not any(normalized(term) in source_norm for term in case.expected_sources):
            reasons.append("fonte esperada ausente")
        leaked = [term for term in case.forbidden if normalized(term) in answer_norm or normalized(term) in source_norm]
        if leaked:
            reasons.append("termo proibido: " + ", ".join(leaked))
        if payload.get("insufficient_context") and not case.allow_insufficient:
            reasons.append("contexto insuficiente inesperado")
        status = "FAIL" if reasons else "PASS"
        failures += bool(reasons)
        print(f"{status} | {elapsed:5.2f}s | {case.question} | {payload.get('retrieval_mode')} | {sources[:3]}" + (f" | {'; '.join(reasons)}" if reasons else ""))
        results.append({"question": case.question, "status": status, "seconds": round(elapsed, 3), "mode": payload.get("retrieval_mode"), "sources": sources, "reasons": reasons})
    print(f"\nRESULTADO: {len(results) - failures}/{len(results)} passaram; {failures} falharam.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
