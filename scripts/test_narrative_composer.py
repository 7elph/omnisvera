from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.narrative_composer import (  # noqa: E402
    build_factual_card,
    card_as_payload,
    deterministic_narrative,
    validate_narrative,
)


def main() -> None:
    source = "Characters/Individual/Vezemir.md"
    result = {
        "answer": (
            "Vezemir foi encontrado ainda bebê nas ruínas de uma Antiga Estrada Esquecida. "
            "É meio-elfo e guerreiro.\n\n"
            "Atualmente, Vezemir está na Floresta de Avenor e mantém vínculo com o Conclave dos Errantes."
        ),
        "notes_used": [{"path": source, "title": "Vezemir", "type": "character"}],
        "informacoes_insuficientes": ["Parte de seu passado ainda não foi revelada."],
    }
    card = build_factual_card("Conte-me naturalmente sobre Vezemir.", result)
    assert card["entidade"] == "Vezemir"
    assert source in card["fontes"]
    assert len(card["fatos_confirmados"]) + len(card["eventos_confirmados"]) >= 2

    raw = (
        "Vezemir foi encontrado ainda bebê nas ruínas de uma Antiga Estrada Esquecida. "
        "Ele é meio-elfo e guerreiro, mas secretamente trabalha para o rei. "
        "Ainda há detalhes sobre seu passado que não foram revelados."
    )
    validated, accepted, rejected = validate_narrative(raw, card)
    assert any("meio-elfo" in item["texto"] for item in accepted)
    assert "trabalha para o rei" not in validated
    assert any("relation" in item["motivo"] for item in rejected)
    assert accepted

    fallback = deterministic_narrative(card)
    assert "Vezemir" in fallback
    assert "vault" not in fallback.casefold()
    payload = card_as_payload(card, fallback)
    assert payload["fontes_usadas"] == [source]
    assert payload["fatos_confirmados"]
    print("narrative composer: PASS")


if __name__ == "__main__":
    main()
