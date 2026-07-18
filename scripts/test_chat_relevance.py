from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402
from app.access import player_profile_scope  # noqa: E402
from app.hybrid_retrieval import _clean_excerpt, _excerpt  # noqa: E402
from app.rag import (  # noqa: E402
    _answer_comparison,
    _answer_explicit_relation,
    _answer_public_nimalia_king,
    _answer_priority_memory,
    _answer_known_route,
    _answer_campaign_territories,
    _answer_faction_conflicts,
    _answer_known_chronology,
    _answer_incomplete_chronology,
    _answer_targeted_rumor,
    _asks_relation_or_theory,
    _direct_entity_target,
    _find_direct_entity_note,
    _filter_results_by_query_entities,
    _fact_theory_subject,
    _looks_like_campaign_recap,
)


def main() -> None:
    settings = get_settings()
    database_path = settings.database_path

    assert _direct_entity_target(
        "Apresente Vezemir a um jogador que nunca ouviu falar de Omnisvera."
    ) == ("vezemir", "about")
    assert _direct_entity_target("Conte-me naturalmente quem é Varkh Nimalis.") == (
        "varkh nimalis",
        "about",
    )
    assert _direct_entity_target(
        "Quais motivações confirmadas conduzem Vezemir atualmente?"
    ) == ("vezemir", "motivation")
    assert _direct_entity_target(
        "Quem é Raziel e em qual parte da história ele aparece?"
    ) == ("raziel", "appearance")
    assert _direct_entity_target(
        "Quem é Augustus e qual é seu papel nos acontecimentos conhecidos?"
    ) == ("augustus", "role")
    assert _direct_entity_target(
        "Quais acontecimentos históricos moldaram Nimalia?"
    ) == ("nimalia", "history")
    assert _direct_entity_target(
        "O que existe de confirmado sobre o Santuário de Elaris?"
    ) == ("santuario de elaris", "about")
    assert not _looks_like_campaign_recap("Quem é Raziel e em qual parte da história ele aparece?")
    assert _looks_like_campaign_recap("O que aconteceu até agora na campanha?")

    for question in (
        "Como a morte de Mira Valen afetou Vezemir?",
        "Como a morte de Mira influenciou Vezemir?",
        "Por que Vezemir e Theron Elensar entram em conflito?",
        "Compare Vezemir e Varkh Nimalis sem inventar semelhanças.",
        "Quais motivações confirmadas conduzem Vezemir atualmente?",
    ):
        assert _asks_relation_or_theory(question)

    elarion = _answer_explicit_relation(
        database_path,
        "Qual é a relação entre Vezemir e Elarion Vaelthor?",
        "player",
    )
    assert elarion is not None
    assert "Associados Conhecidos:**" not in elarion["answer"]
    assert any(term in elarion["answer"].casefold() for term in ("adot", "ensin", "trein", "criou"))

    mira = _answer_explicit_relation(
        database_path,
        "Como a morte de Mira influenciou Vezemir?",
        "player",
    )
    assert mira is not None and not mira["insufficient_context"]
    assert "vingan" in mira["answer"].casefold()

    theron = _answer_explicit_relation(
        database_path,
        "Por que Vezemir e Theron Elensar entram em conflito?",
        "player",
    )
    assert theron is not None and theron["insufficient_context"]
    assert "Mira Valen" not in theron["answer"]

    theron_intro = _answer_explicit_relation(
        database_path,
        "Quem é Theron Elensar e qual é sua ligação com Vezemir?",
        "player",
    )
    assert theron_intro is not None and theron_intro["insufficient_context"]

    comparison = _answer_comparison(
        database_path,
        "Compare Vezemir e Varkh Nimalis sem inventar semelhanças.",
        "player",
    )
    assert comparison is not None and not comparison["insufficient_context"]
    assert "Vezemir" in comparison["answer"] and "Varkh Nimalis" in comparison["answer"]
    alias_comparison = _answer_comparison(
        database_path,
        "Earthropo e Eryndor são lugares diferentes ou nomes usados para a mesma região?",
        "player",
    )
    assert alias_comparison is not None and alias_comparison["insufficient_context"]
    assert "eryndor" in alias_comparison["answer"].casefold()

    king = _answer_public_nimalia_king(database_path, "player")
    assert king is not None
    assert "Augustus" in king["answer"] and "rei" in king["answer"].casefold()

    mar_rumor = _answer_targeted_rumor(
        database_path,
        "Quais rumores conhecidos circulam sobre o Mar da Neblina?",
        "player",
    )
    assert mar_rumor is not None and "Mar da Neblina" in mar_rumor["answer"]
    oric_rumor = _answer_targeted_rumor(
        database_path,
        "Existem rumores sobre o desaparecimento de Padre Oric?",
        "player",
    )
    assert oric_rumor is not None and oric_rumor["insufficient_context"]
    dragon_rumor = _answer_targeted_rumor(
        database_path,
        "O que se diz sobre o dragão verde relacionado à história de Vezemir?",
        "player",
    )
    assert dragon_rumor is not None and "drag" in dragon_rumor["answer"].casefold()
    assert "vezemir" in dragon_rumor["answer"].casefold()
    nimalia_rumor = _answer_targeted_rumor(
        database_path,
        "Conte um rumor existente sobre Nimalia, deixando claro que é apenas um rumor.",
        "player",
    )
    assert nimalia_rumor is not None and not nimalia_rumor["insufficient_context"]
    assert _direct_entity_target(
        "O que ainda permanece desconhecido sobre a Queda de Valthor?"
    ) == ("queda de valthor", "about")

    typo = _find_direct_entity_note(database_path, "Quem é Vezemyr?", "player")
    assert typo is not None and "vezemir" in typo["title"].casefold()

    unrelated = [
        {
            "title": "Fortaleza de Gharok",
            "path": "Locations/Fortaleza de Gharok.md",
            "aliases": [],
            "excerpt": "Uma fortaleza anã ao norte do reino.",
        }
    ]
    assert not _filter_results_by_query_entities("Descreva Ashmoor usando fatos confirmados.", unrelated)
    assert _fact_theory_subject(
        "Quais informações sobre Ashmoor são confirmadas e quais são apenas suspeitas?"
    ) == "Ashmoor"

    route = _answer_known_route(
        database_path,
        "Qual seria uma rota conhecida entre Avenor e Nimalia?",
        "player",
    )
    assert route is not None and "estrada" in route["answer"].casefold()
    territories = _answer_campaign_territories(database_path, "gm")
    assert territories is not None and territories["notes_used"]
    faction_conflicts = _answer_faction_conflicts(database_path, "gm")
    assert faction_conflicts is not None and faction_conflicts["answer"]
    chronology = _answer_known_chronology(database_path, "player")
    assert chronology is not None and chronology["answer"]
    incomplete_chronology = _answer_incomplete_chronology(database_path, "gm")
    assert incomplete_chronology is not None and incomplete_chronology["notes_used"]

    with player_profile_scope("vezemir"):
        personal_memory = _answer_priority_memory(
            database_path,
            "O que eu sei sobre Leth'valora?",
            ["CAMPANHA/Player_Knowledge/CONHECIMENTO - Vezemir.md"],
            "player",
        )
    assert personal_memory is not None and "Leth'valora" in personal_memory["answer"]

    raw = "# Pessoa\n\n**Localização Atual:** Cidade\n**Associados Conhecidos:** Alguém\n\nA pessoa protege a ponte."
    cleaned = _clean_excerpt(raw)
    assert "Localização Atual" not in cleaned and "Associados Conhecidos" not in cleaned
    clipped = _excerpt("Primeira frase completa. Localização importante perto da ponte.", ["ponte"], 32)
    assert not clipped.startswith("zação")

    print("chat relevance and compound questions: PASS")


if __name__ == "__main__":
    main()
