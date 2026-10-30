"""Parser determinístico do campo de movimento de monstros.

Este módulo apenas separa o texto bruto em modos declarados (andar, voo,
natação, escalada e escavação). Ele não calcula altura, paredes, terreno nem
orçamento de combate, e nunca soma modos ou inventa velocidades. Códigos
`V/N/E/C` seguem a notação declarada pelo catálogo Old Dragon 2; qualquer
outro código é devolvido como pendência explícita em :func:`movement_pending`.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

MODE_WALK = "walk"
MODE_FLY = "fly"
MODE_SWIM = "swim"
MODE_CLIMB = "climb"
MODE_BURROW = "burrow"

MODE_ORDER = (MODE_WALK, MODE_FLY, MODE_SWIM, MODE_CLIMB, MODE_BURROW)
_CODE_MODES = {
    "v": MODE_FLY,
    "n": MODE_SWIM,
    "e": MODE_CLIMB,
    "c": MODE_BURROW,
}

_ALIASES = {
    MODE_WALK: ("walk", "caminhada", "caminhar", "andar", "andando", "caminhando", "terrestre",
                "terrestrial", "deslocamento terrestre", "ground"),
    MODE_FLY: ("fly", "voo", "voar", "voando", "voador", "voadora", "flight", "aereo", "aerea"),
    MODE_SWIM: ("swim", "natacao", "nadar", "nadando", "nado", "aquatico", "aquatica"),
    MODE_CLIMB: ("climb", "escalada", "escalar", "escalando"),
    MODE_BURROW: ("burrow", "escavacao", "escavar", "escavando", "cavar", "cavando", "tunel", "tuneis",
                  "subterraneo", "subterranea"),
}

_ALIAS_TO_MODE: dict[str, str] = {}
for _mode, _mode_aliases in _ALIASES.items():
    _ALIAS_TO_MODE[_mode] = _mode
    for _alias in _mode_aliases:
        _ALIAS_TO_MODE[_alias] = _mode

_ALIAS_PATTERN = "|".join(
    re.escape(alias) for alias in sorted(_ALIAS_TO_MODE, key=lambda item: (-len(item), item))
)
_MODE_ALIAS_RE = re.compile(rf"\b(?:{_ALIAS_PATTERN})\b")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

_NUMBER = r"\d+(?:\.\d+)?"
_UNIT = r"m(?:etros?)?"
_DECIMAL_COMMA_RE = re.compile(
    rf"(?<=\d),(?=\d+(?:\s*(?:{_UNIT}))?(?!\s*[a-z])(?:\s|$|[,;]))"
)
_CLAUSE_BREAK_RE = re.compile(r"[;()\[\]|\n]+")
_CLAUSE_SPLIT_RE = re.compile(r"\s*[,;]\s*")
_LEADING_LABEL_RE = re.compile(
    r"^(?:mov(?:imento)?\.?|velocidade|deslocamento|movement|speed)\s*[:\-]?\s*"
)
_NUMERIC_CODE_RE = re.compile(
    rf"^(?P<num>{_NUMBER})\s*(?:{_UNIT})?\s*(?P<code>[a-z])?$"
)
_MODE_GROUP = rf"(?P<mode>\b(?:{_ALIAS_PATTERN})\b)"
_PAIR_NUMBER_MODE_RE = re.compile(
    rf"(?P<num>{_NUMBER})\s*(?:{_UNIT})?\s*(?:de|por|:|-)?\s*{_MODE_GROUP}"
)
_PAIR_MODE_NUMBER_RE = re.compile(
    rf"{_MODE_GROUP}\s*(?:de|por|:|-)?\s*(?P<num>{_NUMBER})\s*(?:{_UNIT})?"
)


def _normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii").casefold().strip()


def _mode_or_none(value: Any) -> str | None:
    return _ALIAS_TO_MODE.get(_normalized(value))


def _number(value: str) -> float:
    return float(value.replace(",", "."))


def _overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < other_end and other_start < end for other_start, other_end in spans)


def _assign(modes: dict[str, float], mode: str, value: float) -> None:
    if mode in modes:
        if modes[mode] != value:
            raise ValueError(
                f"Velocidades conflitantes para o modo {mode}: {modes[mode]} e {value}"
            )
        return
    modes[mode] = value


def _uncovered_numbers(clause: str, covered: list[tuple[int, int]]) -> list[str]:
    return [
        match.group(0)
        for match in _NUMBER_RE.finditer(clause)
        if not _overlaps(match.span(), covered)
    ]


def _pair_assignments(clause: str, pending: list[str]) -> tuple[dict[str, float], list[tuple[int, int]]]:
    assigned: dict[str, float] = {}
    covered_numbers: list[tuple[int, int]] = []
    covered_pairs: list[tuple[int, int]] = []
    for pattern in (_PAIR_NUMBER_MODE_RE, _PAIR_MODE_NUMBER_RE):
        for match in pattern.finditer(clause):
            if _overlaps(match.span(), covered_pairs):
                continue
            mode = _ALIAS_TO_MODE[match.group("mode")]
            value = _number(match.group("num"))
            if not math.isfinite(value) or value < 0:
                pending.append(clause)
                covered_pairs.append(match.span())
                continue
            _assign(assigned, mode, value)
            covered_pairs.append(match.span())
            covered_numbers.append(match.span("num"))
    return assigned, covered_numbers + covered_pairs


def _consume_clause(clause: str, modes: dict[str, float], pending: list[str]) -> None:
    clause = clause.strip(" \t.\u00b7-")
    clause = _LEADING_LABEL_RE.sub("", clause).strip()
    clause = re.sub(r"^(?:de|do|da|por)\s+", "", clause).strip()
    if not clause:
        return

    mode_matches = list(_MODE_ALIAS_RE.finditer(clause))
    if mode_matches:
        assigned, covered = _pair_assignments(clause, pending)
        covered_mode_spans = [
            match.span("mode")
            for pattern in (_PAIR_NUMBER_MODE_RE, _PAIR_MODE_NUMBER_RE)
            for match in pattern.finditer(clause)
        ]
        for match in mode_matches:
            if not _overlaps(match.span(), covered_mode_spans):
                pending.append(match.group(0))
        if assigned:
            for mode, value in assigned.items():
                _assign(modes, mode, value)
            for number in _uncovered_numbers(clause, covered):
                pending.append(number)
            return

        aliases = {_ALIAS_TO_MODE[match.group(0)] for match in mode_matches}
        numbers = [match.group(0) for match in _NUMBER_RE.finditer(clause)]
        if len(aliases) == 1 and len(numbers) == 1:
            _assign(modes, aliases.pop(), _number(numbers[0]))
            return
        pending.append(clause)
        return

    match = _NUMERIC_CODE_RE.fullmatch(clause)
    if match is None:
        pending.append(clause)
        return
    value = _number(match.group("num"))
    if not math.isfinite(value) or value < 0:
        pending.append(clause)
        return
    code = match.group("code")
    if code is None:
        _assign(modes, MODE_WALK, value)
        return
    mode = _CODE_MODES.get(code)
    if mode is None:
        pending.append(clause)
        return
    _assign(modes, mode, value)


def _parse(raw: Any) -> tuple[dict[str, float], list[str]]:
    if isinstance(raw, bool):
        raise ValueError("Movimento inválido na ficha")
    if isinstance(raw, (int, float)):
        value = float(raw)
        if not math.isfinite(value) or value < 0:
            raise ValueError("Movimento em metros inválido")
        return {MODE_WALK: value}, []

    text = _normalized(raw)
    if not text:
        return {}, []

    text = _DECIMAL_COMMA_RE.sub(".", text)
    text = _CLAUSE_BREAK_RE.sub(";", text)
    modes: dict[str, float] = {}
    pending: list[str] = []
    for clause in _CLAUSE_SPLIT_RE.split(text):
        _consume_clause(clause, modes, pending)
    ordered = {mode: modes[mode] for mode in MODE_ORDER if mode in modes}
    return ordered, pending


def movement_modes(raw: Any) -> dict[str, float]:
    """Devolve somente os modos com velocidade declarada, sem somar ou inferir.

    Aceita número, ``"9 m"``, listas SRD como ``"9, 21V"``/``"9,18V"`` e
    formatos textuais inequívocos. Um código desconhecido não vira velocidade;
    ele aparece em :func:`movement_pending`.
    """
    modes, _pending = _parse(raw)
    return modes


def movement_pending(raw: Any) -> list[str]:
    """Lista trechos/códigos que não puderam ser convertidos com segurança."""
    _modes, pending = _parse(raw)
    return pending


def selected_movement(raw: Any, mode: str | None = None) -> float:
    """Seleciona um único modo de movimento, sem misturar voo e caminhada.

    Sem ``mode``, usa ``walk`` quando disponível; caso contrário, aceita apenas
    um único modo claro. Modo ausente, inválido ou ambíguo é rejeitado.
    """
    modes = movement_modes(raw)
    if not modes:
        pending = movement_pending(raw)
        detail = ", ".join(pending) if pending else "não configurado"
        raise ValueError(f"Movimento sem modo conhecido: {detail}")

    if mode is None:
        if MODE_WALK in modes:
            return modes[MODE_WALK]
        if len(modes) == 1:
            return next(iter(modes.values()))
        raise ValueError("Movimento tem múltiplos modos; selecione um modo explicitamente")

    key = _mode_or_none(mode)
    if key is None or key not in modes:
        raise ValueError(f"Modo de movimento inválido ou ausente: {mode}")
    return modes[key]
