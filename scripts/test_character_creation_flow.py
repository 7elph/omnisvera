from __future__ import annotations

import tempfile
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "omnisvera-agent" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app import character_creation


def sample_note() -> dict:
    return {
        "path": "Characters/Individual/Teste.md",
        "title": "Teste",
        "frontmatter": {"race": "Humano", "class": "Guerreiro", "level": 1, "alignment": "Neutro"},
        "content": """
# Teste

## Atributos
| Status | Valor |
|---|---|
| Força | 13 |
| Destreza | 12 |
| Constituição | 11 |
| Inteligência | 10 |
| Sabedoria | 9 |
| Carisma | 8 |

| Combate e recursos | Valor |
|---|---|
| Classe de Armadura | 14 |
| Pontos de Vida | 8 |
| Bônus de Ataque | +1 |
| Movimento | 9 m |
| Ouro inicial | 80 PO |

## História
Um antigo guarda decidiu se tornar aventureiro.

## Aparência
Alto, de cabelos escuros e armadura usada.

## Personalidade
Paciente, leal e desconfiado.

## Situação Atual
Quer descobrir quem atacou sua vila.
""",
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "test.sqlite3"
        sheet = character_creation.get_or_create_sheet(
            database,
            profile_id="teste",
            character_path="Characters/Individual/Teste.md",
            character_title="Teste",
            note=sample_note(),
        )
        assert sheet["completion_count"] >= 3
        attributes = next(step for step in sheet["steps"] if step["key"] == "attributes")
        assert attributes["status"] == "complete"
        assert attributes["fields"]["strength"] == 13

        updated = character_creation.update_sheet_step(
            database,
            profile_id="teste",
            step_key="languages",
            fields={"spoken_languages": "Comum", "written_languages": "Comum"},
        )
        assert updated is not None
        languages = next(step for step in updated["steps"] if step["key"] == "languages")
        assert languages["status"] == "complete"

        try:
            character_creation.submit_sheet(database, profile_id="teste")
        except ValueError as error:
            assert "dez etapas" in str(error)
        else:
            raise AssertionError("Ficha incompleta não pode ser entregue")

    print("CHARACTER_CREATION_FLOW_PASS")


if __name__ == "__main__":
    main()
