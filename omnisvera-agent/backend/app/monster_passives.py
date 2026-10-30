"""Parser determinístico de passivas (apenas o que pode ser mapeado sem invenção).

Sem banco, sem rede, sem LLM. Retorna estrutura pura para revisão.
"""
from __future__ import annotations

import re
from typing import Any


SCHEMA_VERSION = 1

_DAMAGE_TYPES = ("fire", "cold", "acid", "lightning", "poison", "necrotic")

_TYPE_MAP = {
    r"\bfogo\b": "fire",
    r"\binc[êe]ndio\b": "fire",
    r"\bgelo\b": "cold",
    r"\bfrio\b": "cold",
    r"\b[áa]cido\b": "acid",
    r"\braio\b": "lightning",
    r"\brel[âa]mpago\b": "lightning",
    r"\bel[ée]tric(?:[oa]s?|idade)\b": "lightning",
    r"\bvenenos?\b": "poison",
    r"\bnecr[óo]tico\b": "necrotic",
    r"energia\s+necr[óo]tica": "necrotic",
}

_NEG_IMMUNE_RE = re.compile(r"n[ãa]o\s+[ée]\s+imun[ea]|nunca\s+[ée]\s+imun[ea]|n[ãa]o\s+possui\s+imunidade|isento\s+de\s+imunidade", re.IGNORECASE)
_NEG_REGEN_RE = re.compile(r"n[ãa]o\s+regenera|nunca\s+regenera", re.IGNORECASE)
_CONDITIONAL_RE = re.compile(r"\b(?:se|quando|enquanto|caso|somente|apenas|exceto|salvo)\b|desde\s+que|a\s+menos\s+que", re.IGNORECASE)
_MAGIC_IMM_RE = re.compile(r"imun[e]?\s+a\s+magia|imunidade\s+a\s+magia", re.IGNORECASE)
_NONMAGIC_WEAPONS_RE = re.compile(r"armas?\s+n[ãa]o\s+m[áa]gicas?|n[ãa]o\s+m[áa]gicas?", re.IGNORECASE)
_SAVE_ONLY_RE = re.compile(r"\bJP\s*[DCS]\b|\bJPC\b|\bJPD\b|\bJPS\b", re.IGNORECASE)
_REGEN_RE = re.compile(r"regener[ao]\w*\s+(\d+)\s+ponto[s]?\s+de\s+vida\s+a\s+cada\s+rodada", re.IGNORECASE)
_BLOCKED_BY_RE = re.compile(r"n[ãa]o\s+[ée]\s+capaz\s+de\s+regenerar\s+(?:nenhum\s+)?dano\s+causado\s+por\s+(.+?)(?:\.|$)", re.IGNORECASE)
_BLOCKED_BY_SPLIT_RE = re.compile(r"\bfogo\b|\b[áa]cido\b|\bacido\b", re.IGNORECASE)
_IMMUNE_RE = re.compile(r"imun[e]?\s+(?:a|ao|a\s+qualquer\s+efeito\s+de)\s+(.+?)(?:\.|$)", re.IGNORECASE)
_RESIST_Q_RE = re.compile(r"resist[eê]ncia.*?(?:metade|divide\s+por\s+2|/2|\d+\s*%)", re.IGNORECASE)
_RESIST_HALF_RE = re.compile(r"metade\s+do\s+dano|recebe\s+metade|reduz.*?metade", re.IGNORECASE)
_VULN_Q_RE = re.compile(r"vulner[áa]vel.*?(?:dobro|x\s*2|duplo)", re.IGNORECASE)
_VULN_DOUBLE_RE = re.compile(r"sofre\s+o\s+dobro|recebe\s+o\s+dobro|dano\s+em\s+dobro", re.IGNORECASE)


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def _map_types(text: str) -> list[str]:
    found = []
    for pat, canon in _TYPE_MAP.items():
        if re.search(pat, text, re.IGNORECASE):
            if canon not in found:
                found.append(canon)
    return found


def passive_specs(monster: dict) -> dict:
    if not isinstance(monster, dict):
        raise TypeError("monster deve ser um dicionário")
    monster_id = str(monster.get("id") or "")
    abilities = monster.get("abilities") or []
    sources = []
    damage_immunities = []
    damage_resistances = []
    damage_vulnerabilities = []
    regeneration = None
    pending = []

    for idx, ability in enumerate(abilities):
        name = str(ability.get("name") or "")
        text = str(ability.get("description") or "")
        if not text.strip():
            sources.append({"ability_index": idx, "name": name, "text": text})
            pending.append({"ability_index": idx, "name": name, "text": text, "reason": "texto_vazio_pendente"})
            continue
        sources.append({"ability_index": idx, "name": name, "text": text})
        full = f"{name} {text}"
        tnorm = _norm(full)

        supported = False

        # regeneration
        if re.search(r"regener", tnorm):
            if _NEG_REGEN_RE.search(full):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "regeneracao_negada_pendente"})
                continue
            if _CONDITIONAL_RE.search(full):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "regeneracao_condicional_pendente"})
                continue
            m = _REGEN_RE.search(text)
            if m and re.search(r'\b(?:não|nunca|jamais)\b',text[max(0,m.start()-45):m.start()],re.I):
                pending.append({"ability_index":idx,"name":name,"text":text,"reason":"regeneracao_negada_pendente"})
                continue
            if m and regeneration is None:
                amount = int(m.group(1))
                blocked = []
                bm = _BLOCKED_BY_RE.search(text)
                if bm:
                    bt = bm.group(1)
                    for part in _BLOCKED_BY_SPLIT_RE.findall(bt):
                        bmap = None
                        if re.search(r"\bfogo\b", part, re.I):
                            bmap = "fire"
                        elif re.search(r"\b[áa]cido\b|\bacido\b", part, re.I):
                            bmap = "acid"
                        if bmap and bmap not in blocked:
                            blocked.append(bmap)
                if amount > 0 and re.search(r"a\s+cada\s+rodada", tnorm):
                    regeneration = {"amount": amount, "interval": "round", "blocked_by": blocked,"source_ability_index":idx}
                    supported = True
                    continue
            pending.append({"ability_index": idx, "name": name, "text": text, "reason": "regeneracao_nao_determinista"})
            continue

        # immunities
        if re.search(r"imun", tnorm):
            if _NEG_IMMUNE_RE.search(full) or (re.search(r'\b(?:não|nunca|jamais)\b',full,re.I) and not _NONMAGIC_WEAPONS_RE.search(full)):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "imunidade_negada_pendente"})
                continue
            if _MAGIC_IMM_RE.search(full):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "imunidade_a_magia_com_excecoes_pendentes"})
                continue
            if _NONMAGIC_WEAPONS_RE.search(full):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "imunidade_apenas_armas_nao_magicas_pendente"})
                continue
            if _CONDITIONAL_RE.search(full):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "imunidade_condicional_pendente"})
                continue
            if _SAVE_ONLY_RE.search(full) and not re.search(r"dano", tnorm):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "somente_jp_nao_imunidade_dano"})
                continue
            im = _IMMUNE_RE.search(text)
            if im:
                body = im.group(1)
                ctypes = _map_types(body)
                if ctypes:
                    for ct in ctypes:
                        if ct in _DAMAGE_TYPES:
                            damage_immunities.append({"type": ct, "source_ability_index": idx, "source_name": name})
                    if ctypes:
                        supported = True
                        continue
            pending.append({"ability_index": idx, "name": name, "text": text, "reason": "tipo_imunidade_nao_mapeavel"})
            continue

        # resistances
        if re.search(r"resist", tnorm):
            if _CONDITIONAL_RE.search(full) or re.search(r'\b(?:não|nunca|jamais)\b',full,re.I):
                pending.append({"ability_index":idx,"name":name,"text":text,"reason":"resistencia_condicional_ou_negada"})
                continue
            if _SAVE_ONLY_RE.search(full):
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "resistencia_referida_a_jp_pendente"})
                continue
            if _RESIST_HALF_RE.search(full) and re.search(r'\bdano\b',full,re.I):
                body = full
                ctypes = _map_types(body)
                if len(ctypes) == 1:
                    damage_resistances.append({"type": ctypes[0], "factor": 0.5, "source_ability_index": idx})
                    supported = True
                    continue
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "resistencia_quantitativa_nao_inequivoca"})
                continue
            pending.append({"ability_index": idx, "name": name, "text": text, "reason": "fator_quantitativo_nao_explicitamente_dano"})
            continue

        # vulnerabilities
        if re.search(r"vulner", tnorm):
            if _CONDITIONAL_RE.search(full) or re.search(r'\b(?:não|nunca|jamais)\b',full,re.I):
                pending.append({"ability_index":idx,"name":name,"text":text,"reason":"vulnerabilidade_condicional_ou_negada"})
                continue
            if _VULN_Q_RE.search(full) or _VULN_DOUBLE_RE.search(full):
                ctypes = _map_types(full)
                if len(ctypes) == 1:
                    damage_vulnerabilities.append({"type": ctypes[0], "factor": 2.0, "source_ability_index": idx})
                    supported = True
                    continue
                pending.append({"ability_index": idx, "name": name, "text": text, "reason": "vulnerabilidade_quantitativa_nao_inequivoca"})
                continue
            pending.append({"ability_index": idx, "name": name, "text": text, "reason": "vulnerabilidade_sem_fator_quantitativo_pendente"})
            continue

        # No passive mapped - must go to pending
        pending.append({"ability_index": idx, "name": name, "text": text, "reason": "passiva_nao_suportada_pendente"})

    # deduplicate immunities
    seen = set()
    di = []
    for d in damage_immunities:
        if d["type"] not in seen:
            di.append(d)
            seen.add(d["type"])

    return {
        "schema_version": SCHEMA_VERSION,
        "monster_id": monster_id,
        "damage_immunities": di,
        "damage_resistances": damage_resistances,
        "damage_vulnerabilities": damage_vulnerabilities,
        "regeneration": regeneration,
        "sources": sources,
        "pending": pending,
        "coverage": {
            "family_complete": False,
            "partially_supported": bool(di or regeneration or damage_resistances or damage_vulnerabilities),
        },
    }
