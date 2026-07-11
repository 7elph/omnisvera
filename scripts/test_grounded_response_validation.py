from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.rag import _extract_json_object, _validate_grounded_payload  # noqa: E402


SOURCE = "Characters/Individual/Vezemir.md"
EVIDENCE = "Vezemir é um meio-elfo guerreiro conhecido como Bastardo de Ferro."


def main() -> None:
    valid = _validate_grounded_payload(
        {
            "fatos": [{"texto": "Vezemir é um meio-elfo guerreiro.", "fonte": SOURCE, "evidencia": EVIDENCE}],
            "teorias": [],
            "informacoes_insuficientes": [],
            "fontes_usadas": [SOURCE],
            "resposta_ao_usuario": "Vezemir é um meio-elfo guerreiro conhecido como Bastardo de Ferro.",
        },
        {SOURCE},
        {SOURCE: EVIDENCE},
        strict_evidence=True,
        access_mode="player",
    )
    assert valid and len(valid["fatos_confirmados"]) == 1
    assert valid["fontes_usadas"] == [SOURCE]

    invented_path = _validate_grounded_payload(
        {
            "fatos": [{"texto": "Existe um imperador.", "fonte": "Segredo.md", "evidencia": "Existe um imperador."}],
            "informacoes_insuficientes": ["Não há evidência sobre um imperador secreto."],
            "resposta_ao_usuario": "O imperador secreto governa Nimalia.",
        },
        {SOURCE},
        {SOURCE: EVIDENCE},
        strict_evidence=True,
        access_mode="player",
    )
    assert invented_path
    assert invented_path["fatos_confirmados"] == []
    assert "governa Nimalia" not in invented_path["resposta_ao_jogador"]

    wrong_evidence = _validate_grounded_payload(
        {
            "fatos": [{"texto": "Vezemir é rei.", "fonte": SOURCE, "evidencia": "Vezemir é rei."}],
            "informacoes_insuficientes": ["A realeza de Vezemir não foi confirmada."],
            "resposta_ao_usuario": "Vezemir é rei.",
        },
        {SOURCE},
        {SOURCE: EVIDENCE},
        strict_evidence=True,
        access_mode="player",
    )
    assert wrong_evidence and wrong_evidence["fatos_confirmados"] == []
    assert "Vezemir é rei" not in wrong_evidence["resposta_ao_jogador"]

    theory = _validate_grounded_payload(
        {
            "fatos": [],
            "teorias": [{"texto": "Pode haver uma ligação.", "fontes": [SOURCE, "GM.md"]}],
            "informacoes_insuficientes": [],
            "resposta_ao_usuario": "Pode haver uma ligação.",
        },
        {SOURCE},
        {SOURCE: EVIDENCE},
        strict_evidence=True,
        access_mode="player",
    )
    assert theory and theory["teorias"][0]["base"] == [SOURCE]

    assert _extract_json_object("não é JSON") is None
    print("grounded validation: PASS")


if __name__ == "__main__":
    main()
