#!/usr/bin/env python3
"""Generate Omnisvera content development queue and briefs.

The script is read-only for campaign notes. It writes only under
Workflow/Content_Development/.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".obsidian",
    "zz_media",
    "node_modules",
    ".tmp_refs",
    ".omnisvera-tools",
    ".codex-tools",
}
SKIP_PREFIXES = (
    "Workflow/_audit/",
    "Workflow/_archive/",
    "Workflow/Legacy/",
    "Workflow/RPG_SYSTEM_DESIGN/",
    "Workflow/COMPATIBILITY_LAYER/",
    "Workflow/_audit",
)
CONTENT_DIR = Path("Workflow/Content_Development")
BRIEF_DIR = CONTENT_DIR / "Briefs"

IMPORTANT_NOTES = {
    "Locations/Nimalis.md": 120,
    "Locations/Maré Baixa.md": 120,
    "Locations/O Frasco Afogado.md": 130,
    "Locations/Porto de Nimalia.md": 110,
    "Factions/Coroa de Nimalia.md": 110,
    "Factions/Culto dos Sussurrantes.md": 105,
    "Factions/Guilda dos Mercadores.md": 105,
    "Characters/Individual/Varkh Nimalis.md": 100,
    "Characters/Individual/Raziel.md": 100,
    "CAMPANHA/ESTADO_DA_CAMPANHA.md": 115,
}
HIGH_VALUE_TYPES = {"location", "faction", "character", "story", "lore", "territory"}
USEFUL_SECTIONS = {
    "Resumo",
    "Visão Geral",
    "Descrição",
    "Atmosfera",
    "Função em jogo",
    "Uso em Mesa",
    "Rumores",
    "Ganchos de aventura",
    "Segredos do Mestre",
    "Relações",
}


@dataclass
class NoteInfo:
    path: Path
    rel: str
    title: str
    frontmatter: dict[str, object]
    body: str
    body_len: int
    links: list[str]
    sections: list[str]
    backlinks: int = 0
    score: int = 0
    priority: str = "low"
    reasons: list[str] = field(default_factory=list)
    action: str = "Revisar quando houver tempo."

    @property
    def type(self) -> str:
        value = self.frontmatter.get("type", "")
        return str(value) if value is not None else ""

    @property
    def subtype(self) -> str:
        value = self.frontmatter.get("subtype", "")
        return str(value) if value is not None else ""


def strip_accents(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(ch)
    )


def slug(value: str) -> str:
    value = strip_accents(value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value or "Nota"


def read_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip("\n")
    body = text[text.find("\n", end + 1) + 1 :]
    data: dict[str, object] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s*-\s+", line) and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(line.split("-", 1)[1].strip().strip('"'))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        current_key = key
        if value == "":
            data[key] = []
        else:
            data[key] = value.strip('"')
    return data, body


def should_skip(path: Path, root: Path) -> bool:
    rel_path = path.relative_to(root)
    rel = rel_path.as_posix()
    if any(part in SKIP_DIRS for part in rel_path.parts):
        return True
    if any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in SKIP_PREFIXES):
        return True
    if rel.startswith("Workflow/Content_Development/Briefs/"):
        return True
    if rel.startswith("Workflow/Content_Development/"):
        return True
    if path.suffix.lower() != ".md":
        return True
    return False


def wikilinks(text: str) -> list[str]:
    result = []
    for match in re.finditer(r"\[\[([^\]]+)\]\]", text):
        target = match.group(1).split("|", 1)[0].strip()
        if target:
            result.append(target)
    return result


def headings(body: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^#{2,3}\s+(.+)$", body, re.M)]


def title_from_note(path: Path, body: str) -> str:
    m = re.search(r"^#\s+(.+)$", body, re.M)
    if m:
        return m.group(1).strip()
    return path.stem


def infer_type(rel: str, fm: dict[str, object]) -> str:
    if fm.get("type"):
        return str(fm["type"])
    first = rel.split("/", 1)[0]
    return {
        "Characters": "character",
        "Locations": "location",
        "Factions": "faction",
        "Items": "item",
        "Territories": "territory",
        "Lore": "lore",
        "Religion": "religion",
        "Races": "race",
        "Classes": "class",
        "CAMPANHA": "story",
        "EARTHROPO": "story",
    }.get(first, "")


def analyze_note(path: Path, root: Path) -> NoteInfo:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = read_frontmatter(text)
    rel = path.relative_to(root).as_posix()
    if "type" not in fm:
        inferred = infer_type(rel, fm)
        if inferred:
            fm["type"] = inferred
    info = NoteInfo(
        path=path,
        rel=rel,
        title=title_from_note(path, body),
        frontmatter=fm,
        body=body,
        body_len=len(re.sub(r"\s+", "", body)),
        links=wikilinks(text),
        sections=headings(body),
    )
    return info


def compute_backlinks(notes: list[NoteInfo]) -> None:
    by_stem: dict[str, NoteInfo] = {n.path.stem: n for n in notes}
    by_title: dict[str, NoteInfo] = {n.title: n for n in notes}
    for note in notes:
        for link in note.links:
            target = link.split("#", 1)[0].split("/", 1)[-1]
            linked = by_stem.get(target) or by_title.get(target)
            if linked and linked.rel != note.rel:
                linked.backlinks += 1


def score_note(note: NoteInfo) -> None:
    score = 0
    reasons: list[str] = []
    if note.rel in IMPORTANT_NOTES:
        score += IMPORTANT_NOTES[note.rel]
        reasons.append("nota indicada como prioridade inicial")
    if note.type in HIGH_VALUE_TYPES:
        score += 20
    if note.type in {"location", "faction"}:
        score += 10
    if note.backlinks >= 8:
        score += 35
        reasons.append(f"muitas referências internas ({note.backlinks})")
    elif note.backlinks >= 4:
        score += 20
        reasons.append(f"referenciada por outras notas ({note.backlinks})")
    if note.body_len < 1200:
        score += 25
        reasons.append("corpo ainda curto")
    elif note.body_len < 2500:
        score += 10
        reasons.append("corpo pode ganhar detalhe jogável")
    text = (note.body + "\n" + str(note.frontmatter)).lower()
    if any(term in text for term in ["pendente", "em aberto", "revisão", "placeholder", "todo"]):
        score += 25
        reasons.append("possui pendências ou marcadores de revisão")
    useful_present = {s for s in note.sections if s in USEFUL_SECTIONS}
    if len(useful_present) < 4 and note.type in HIGH_VALUE_TYPES:
        score += 15
        reasons.append("faltam seções jogáveis")
    if str(note.frontmatter.get("requires_review", "")).lower() == "true":
        score += 10
        reasons.append("marcada como requires_review")
    status_text = " ".join(
        str(note.frontmatter.get(k, "")) for k in ("work_status", "canon_status", "campaign_status", "NoteStatus")
    ).lower()
    if any(term in status_text for term in ["draft", "desenvolvimento", "revisão", "pending"]):
        score += 10
        reasons.append("status editorial indica desenvolvimento")

    note.score = score
    note.reasons = reasons or ["nota útil para desenvolvimento futuro"]
    if score >= 85:
        note.priority = "high"
        note.action = "Criar brief e responder perguntas do Sage."
    elif score >= 45:
        note.priority = "medium"
        note.action = "Desenvolver após prioridades altas."
    else:
        note.priority = "low"
        note.action = "Manter em observação."


def questions_for(note_type: str) -> list[str]:
    bank = {
        "character": [
            "Quem é este personagem em uma frase?",
            "O que ele quer agora?",
            "O que ele sabe que os jogadores não sabem?",
            "Como ele entra em cena?",
            "Que rumor existe sobre ele?",
        ],
        "location": [
            "Que tipo de lugar é e onde fica exatamente?",
            "Qual a primeira impressão ao chegar?",
            "Quem vive, trabalha ou circula ali?",
            "O que os jogadores podem fazer ali?",
            "Que perigo, rumor ou segredo existe no local?",
        ],
        "faction": [
            "O que esta facção quer?",
            "Quem a lidera ou representa?",
            "Como ela aparece para o povo?",
            "Como pode ajudar ou atrapalhar os jogadores?",
            "Que segredo ou conflito interno ela esconde?",
        ],
        "item": [
            "O que é este item?",
            "Quem criou, usou ou deseja o item?",
            "Qual função ele tem em jogo?",
            "Que risco, custo ou segredo carrega?",
            "Como ele entra em cena?",
        ],
        "lore": [
            "Qual é a ideia central?",
            "O que o povo sabe?",
            "O que é segredo do mestre?",
            "Como isso afeta a campanha?",
            "Que cena pode revelar essa informação?",
        ],
        "territory": [
            "Que área ampla este território representa?",
            "Quais locais importantes ficam ali?",
            "Quem governa ou disputa a região?",
            "Qual perigo ou oportunidade define o território?",
            "O que só o mestre sabe?",
        ],
        "story": [
            "Qual é o foco desta parte da campanha?",
            "Quais personagens e locais precisam aparecer?",
            "Quais pistas ou revelações podem surgir?",
            "Que escolha importante os jogadores podem fazer?",
            "O que muda depois deste capítulo?",
        ],
    }
    return bank.get(note_type, bank["lore"])


def summarize_known(note: NoteInfo) -> list[str]:
    items: list[str] = []
    for key in ("type", "subtype", "status", "campaign_status", "visibility", "location", "territory", "faction", "role", "description", "info"):
        value = note.frontmatter.get(key)
        if value:
            items.append(f"- `{key}`: {value}")
    first_paragraphs = []
    for paragraph in re.split(r"\n\s*\n", note.body):
        clean = paragraph.strip()
        if not clean or clean.startswith("#") or clean.startswith(">") or clean.startswith("```"):
            continue
        if len(clean) > 60:
            first_paragraphs.append(clean.replace("\n", " "))
        if len(first_paragraphs) >= 2:
            break
    for paragraph in first_paragraphs:
        items.append(f"- {paragraph[:350]}{'...' if len(paragraph) > 350 else ''}")
    return items or ["- Ainda há pouca informação consolidada nesta nota."]


def write_queue(root: Path, notes: list[NoteInfo]) -> None:
    path = root / CONTENT_DIR / "CONTENT_CREATION_QUEUE.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    grouped = {
        "high": [n for n in notes if n.priority == "high"],
        "medium": [n for n in notes if n.priority == "medium"],
        "low": [n for n in notes if n.priority == "low"],
    }
    for key in grouped:
        grouped[key].sort(key=lambda n: (-n.score, n.rel))
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Fila de Criação de Conteúdo — Omnisvera\n\n")
        f.write("> [!NOTE]\n")
        f.write("> Arquivo gerado por `scripts/generate_content_queue.py`.\n")
        f.write("> Use esta fila para escolher quais notas responder primeiro no `SAGE_CONTENT_INBOX.md`.\n\n")
        for title, key in (("Prioridade Alta", "high"), ("Prioridade Média", "medium"), ("Prioridade Baixa", "low")):
            f.write(f"## {title}\n\n")
            f.write("| Nota | Tipo | Subtipo | Motivo | Próxima ação |\n")
            f.write("|---|---|---|---|---|\n")
            limit = 40 if key != "low" else 30
            for note in grouped[key][:limit]:
                reason = "; ".join(note.reasons[:3])
                link = f"[[{note.path.stem}]]"
                f.write(f"| {link} | `{note.type}` | `{note.subtype}` | {reason} | {note.action} |\n")
            f.write("\n")
        f.write("## Observações\n\n")
        f.write("- Prioridade alta não significa que a nota está errada; significa que ela é útil para jogo e merece desenvolvimento.\n")
        f.write("- Relatórios, auditorias e arquivos históricos são ignorados pelo gerador.\n")


def write_brief(root: Path, note: NoteInfo, all_notes: list[NoteInfo]) -> None:
    out = root / BRIEF_DIR / f"{slug(note.path.stem)}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    linked_titles = sorted(set(note.links))[:20]
    related_backlinks = sorted(
        [n for n in all_notes if any(link.split("|", 1)[0].split("#", 1)[0].endswith(note.path.stem) for link in n.links)],
        key=lambda n: n.rel,
    )[:15]
    questions = questions_for(note.type)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Brief de Desenvolvimento — {note.path.stem}\n\n")
        f.write("## Nota alvo\n\n")
        f.write(f"[[{note.path.stem}]]\n\n")
        f.write("## O que já sabemos pelo vault\n\n")
        for line in summarize_known(note):
            f.write(f"{line}\n")
        f.write("\n## Relações detectadas\n\n")
        if linked_titles:
            for link in linked_titles:
                f.write(f"- [[{link}]]\n")
        else:
            f.write("- Nenhum wikilink direto detectado.\n")
        if related_backlinks:
            f.write("\n### Notas que apontam para esta nota\n\n")
            for backlink in related_backlinks:
                f.write(f"- [[{backlink.path.stem}]] (`{backlink.rel}`)\n")
        f.write("\n## Lacunas\n\n")
        for reason in note.reasons:
            f.write(f"- {reason}\n")
        f.write("\n## Perguntas para o Sage\n\n")
        for i, question in enumerate(questions, 1):
            f.write(f"{i}. {question}\n")
        f.write("\n## Sugestão de estrutura da nota\n\n")
        f.write("```md\n")
        f.write(f"# {note.path.stem}\n\n")
        f.write("## Resumo\n\n")
        f.write("## O que os jogadores podem perceber\n\n")
        f.write("## Descrição\n\n")
        f.write("## Pessoas ou grupos ligados\n\n")
        f.write("## Rumores\n\n")
        f.write("## Ganchos de aventura\n\n")
        f.write("## Segredos do Mestre\n\n")
        f.write("## Relações\n\n")
        f.write("## Uso em jogo\n")
        f.write("```\n\n")
        f.write("## Prompt de geração futura\n\n")
        f.write("```text\n")
        f.write(f"Desenvolva a nota [[{note.path.stem}]] usando as respostas do Sage, o conteúdo existente da nota e as relações detectadas neste brief. Preserve frontmatter, links, tags e cânone existente. Separe informação pública de segredo do mestre. Gere conteúdo útil para mesa de RPG, sem inventar canon pesado sem marcar como sugestão.\n")
        f.write("```\n")


def write_report(root: Path, notes: list[NoteInfo], brief_notes: list[NoteInfo], migrated: bool) -> None:
    report = root / CONTENT_DIR / "CONTENT_SYSTEM_REPORT.md"
    high = sorted([n for n in notes if n.priority == "high"], key=lambda n: (-n.score, n.rel))
    with report.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Relatório do Sistema de Desenvolvimento de Conteúdo\n\n")
        f.write("## Arquivos criados/atualizados\n\n")
        f.write("- `Workflow/Content_Development/CONTENT_CREATION_QUEUE.md`\n")
        f.write("- `Workflow/Content_Development/NOTE_DEVELOPMENT_QUESTIONS.md`\n")
        f.write("- `Workflow/Content_Development/SAGE_CONTENT_INBOX.md`\n")
        f.write("- `Workflow/Content_Development/CONTENT_GENERATION_PROTOCOL.md`\n")
        f.write("- `Workflow/Content_Development/Briefs/`\n")
        f.write("- `scripts/generate_content_queue.py`\n\n")
        f.write("## Arquivos alterados pela migração pontual\n\n")
        f.write("- `Items/O Frasco Afogado.md` → `Locations/O Frasco Afogado.md`\n")
        f.write("- `Factions/Rede de Falsificadores de Maré Baixa.md`\n")
        f.write("- `Items/INDICE_DE_ITENS.md`\n")
        f.write("- `Workflow/MISSING_NOTES_BACKLOG.md`\n")
        f.write("- `scripts/audit_vault_standard.py`\n")
        f.write("- `scripts/plan_frontmatter_minimum.py`\n")
        f.write("- `Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md`\n\n")
        f.write("## Migração de O Frasco Afogado\n\n")
        f.write(f"- Status: {'migrado para `Locations/O Frasco Afogado.md`' if migrated else 'não detectado como migrado'}.\n")
        f.write("- `type` aplicado: `location`.\n")
        f.write("- `subtype` aplicado: `shop`.\n")
        f.write("- Link explícito antigo em `Factions/Rede de Falsificadores de Maré Baixa.md` atualizado para wikilink simples.\n")
        f.write("- `Items/INDICE_DE_ITENS.md` atualizado para não listar o Frasco como item pendente.\n\n")
        f.write("## Top 10 notas recomendadas para o Sage desenvolver primeiro\n\n")
        f.write("| ordem | nota | tipo | subtipo | motivo |\n")
        f.write("|---:|---|---|---|---|\n")
        for i, note in enumerate(high[:10], 1):
            f.write(f"| {i} | [[{note.path.stem}]] | `{note.type}` | `{note.subtype}` | {'; '.join(note.reasons[:3])} |\n")
        f.write("\n## Briefs criados\n\n")
        for note in brief_notes:
            f.write(f"- `Workflow/Content_Development/Briefs/{slug(note.path.stem)}.md` para [[{note.path.stem}]]\n")
        f.write("\n## Dúvidas ou ambiguidades\n\n")
        f.write("- Prioridades são heurísticas; o Sage pode promover ou rebaixar qualquer nota.\n")
        f.write("- Notas com muitos backlinks podem ser importantes mesmo quando o corpo já parece longo.\n")
        f.write("- Segredos de mestre devem continuar centralizados em notas de mestre quando houver risco de spoiler.\n\n")
        f.write("## Recomendações para próxima etapa\n\n")
        f.write("1. Sage escolher de 3 a 5 briefs de alta prioridade.\n")
        f.write("2. Sage responder no `SAGE_CONTENT_INBOX.md`.\n")
        f.write("3. IA/Codex desenvolver as notas uma por vez usando o protocolo.\n")
        f.write("4. Validar links, Dataview/DataCards e visibilidade após cada lote.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--brief-limit", type=int, default=15)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    notes = [analyze_note(p, root) for p in root.rglob("*.md") if not should_skip(p, root)]
    compute_backlinks(notes)
    for note in notes:
        score_note(note)
    write_queue(root, notes)
    high = sorted([n for n in notes if n.priority == "high"], key=lambda n: (-n.score, n.rel))
    brief_notes = high[: args.brief_limit]
    for note in brief_notes:
        write_brief(root, note, notes)
    migrated = (root / "Locations/O Frasco Afogado.md").exists() and not (root / "Items/O Frasco Afogado.md").exists()
    write_report(root, notes, brief_notes, migrated)
    print(f"Notas analisadas: {len(notes)}")
    print(f"Alta prioridade: {sum(1 for n in notes if n.priority == 'high')}")
    print(f"Média prioridade: {sum(1 for n in notes if n.priority == 'medium')}")
    print(f"Baixa prioridade: {sum(1 for n in notes if n.priority == 'low')}")
    print(f"Briefs criados: {len(brief_notes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
