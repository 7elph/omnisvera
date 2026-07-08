from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("OMNISVERA_COMPANION_URL", "http://127.0.0.1:8787")
TOKEN = os.environ.get("OMNISVERA_PLAYER_TOKEN", "player-6c0d00be2aaa453aada62308")


@dataclass(frozen=True)
class Case:
    question: str
    expected_path: str | None = None
    expected_phrase: str | None = None


CASES = [
    Case("Quem é Vezemir?", "Characters/Individual/Vezemir.md", "personagem jogador"),
    Case("Quem é Raziel?", "Characters/Individual/Raziel.md", "personagem jogador"),
    Case("Quem é Varkh?", "Characters/Individual/Varkh Nimalis.md", "personagem jogador"),
    Case("Quem é Morthak?", "Characters/Individual/Morthak.md", "personagem jogador"),
    Case("O que é Muralha de Dorn?", "Items/Muralha de Dorn.md", "portador"),
    Case("O que é Grisalma?", "Items/Grisalma.md", "portador"),
    Case("O que sabemos sobre Nimalis?", "Locations/Nimalis.md", None),
    Case("Quais missões estão ativas?", "CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md", "Missões"),
    Case("Quais rumores estão ativos?", "CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md", "Rumores"),
    Case("Quem são os personagens jogadores?", "Characters/Individual/Vezemir.md", "Personagens jogadores"),
    Case("Onde fica O Frasco Afogado?", None, "não está liberada"),
    Case("O que aconteceu até agora?", "EARTHROPO/01 - Ecos do Mundo Perdido.md", "Resumo público"),
]


def ask(question: str) -> dict:
    payload = json.dumps({"question": question, "limit": 6}).encode("utf-8")
    request = Request(
        f"{BASE_URL}/player/chat",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Omnisvera-Token": TOKEN,
            "ngrok-skip-browser-warning": "true",
        },
    )
    with urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    failures = 0
    for case in CASES:
        result = ask(case.question)
        answer = result.get("answer", "")
        paths = result.get("note_paths", [])
        ok_path = case.expected_path is None or case.expected_path in paths
        ok_phrase = case.expected_phrase is None or case.expected_phrase.lower() in answer.lower()
        ok = ok_path and ok_phrase
        status = "OK" if ok else "FAIL"
        print(f"\n[{status}] {case.question}")
        print(answer)
        print("paths:", paths)
        if not ok:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
