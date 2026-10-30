import { useEffect, useMemo, useRef, useState } from "react";
import { createCommandRetry } from "../commandRetry";
import { spellTargetOutcome } from '../spellOutcome';
import { loadSelection, saveSelection } from '../selectionRecovery';
import MonsterActionMap from "./MonsterActionMap";
import TargetSelect from "./TargetSelect";
import {
  castCompendiumSpell, commandRecoveryOptions,
  newDiceRequestId,
  listCompendiumAbilities,
  listCompendiumItems,
  listCompendiumSpells,
  type CompendiumAbilitiesResponse,
  type CompendiumItemsResponse,
  type CompendiumSpellsResponse,
  type PlayableCharacterSummary,
  type SpellCastResult,
  type WorkspaceToken,
} from "../api";

function norm(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

export default function CompendiumPanel({ characters = [], tokens = [] }: { characters?: PlayableCharacterSummary[]; tokens?: WorkspaceToken[] }) {
  const [tab, setTab] = useState<"spells" | "abilities" | "items" | "actions">("spells");
  const [spells, setSpells] = useState<CompendiumSpellsResponse | null>(null);
  const [abilities, setAbilities] = useState<CompendiumAbilitiesResponse | null>(null);
  const [items, setItems] = useState<CompendiumItemsResponse | null>(null);
  const [search, setSearch] = useState("");
  const [tradition, setTradition] = useState("");
  const [circle, setCircle] = useState("");
  const [abilitySpec, setAbilitySpec] = useState("");
  const [itemCategory, setItemCategory] = useState("");
  const [selectedSpell, setSelectedSpell] = useState("");
  const [selectedAbility, setSelectedAbility] = useState("");
  const [selectedItem, setSelectedItem] = useState("");
  const [caster, setCaster] = useState("");
  const [castTarget, setCastTarget] = useState("");
  const [castDie, setCastDie] = useState("");
  const [castResult, setCastResult] = useState<SpellCastResult | null>(null);
  const [error, setError] = useState("");
  const [casting, setCasting] = useState(false);
  const commands = useRef(createCommandRetry(() => newDiceRequestId("compendium-spell"), commandRecoveryOptions("compendium-spell")));
  const selection = useRef({ restored: false, changed: 0 });
  useEffect(() => {
    if (!spells || selection.current.restored) return;
    let active = true;
    const revision = selection.current.changed;
    void loadSelection(commandRecoveryOptions('compendium-selection')).then(saved => {
      if (!active) return;
      if (!saved || revision !== selection.current.changed) { selection.current.restored = true; return; }
      const allowed = new Set([...characters.map(entry => entry.id), ...tokens.filter(entry => entry.token_type === 'monster').map(entry => 'token:' + entry.id)]);
      // Catalogue and workspace arrive independently. Do not discard valid
      // saved targets just because the workspace DTO has not arrived yet.
      if ([saved.caster, saved.target].some(value => value && !allowed.has(value))) return;
      selection.current.restored = true;
      if (spells.spells.some(entry => entry.id === saved.spell)) setSelectedSpell(saved.spell);
      if (allowed.has(saved.caster)) setCaster(saved.caster);
      if (allowed.has(saved.target)) setCastTarget(saved.target);
      if (['', 'arcana', 'divina'].includes(saved.tradition)) setTradition(saved.tradition);
      if (/^[1-9]?$/.test(saved.circle || '')) setCircle(saved.circle || '');
      if (/^(?:[1-9]|1[0-9]|20)$/.test(saved.die || '')) setCastDie(saved.die);
    });
    return () => { active = false; };
  }, [spells, characters, tokens]);
  function remember(key: string, value: string) {
    const revision = ++selection.current.changed;
    void saveSelection(commandRecoveryOptions('compendium-selection'), {
      spell: selectedSpell, caster, target: castTarget, tradition, circle, die: castDie, [key]: value,
    }, () => revision === selection.current.changed);
  }

  const targetOptions = [
    ...characters.map((character) => ({ id: character.id, name: `${character.name} (jogador)` })),
    ...tokens.filter((token) => token.token_type === "monster").map((token) => ({ id: `token:${token.id}`, name: `${token.name} (criatura)` })),
  ];
  function parseTarget(value: string): { type: "character" | "token"; id: string } {
    return value.startsWith("token:") ? { type: "token", id: value.slice(6) } : { type: "character", id: value };
  }

  useEffect(() => {
    let active = true;
    void listCompendiumSpells().then((catalog) => { if (active) setSpells(catalog); }).catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar o grimório"); });
    void listCompendiumAbilities().then((catalog) => { if (active) setAbilities(catalog); }).catch(() => {});
    void listCompendiumItems().then((catalog) => { if (active) setItems(catalog); }).catch(() => {});
    return () => { active = false; };
  }, []);

  const filteredSpells = useMemo(() => {
    const key = norm(search.trim());
    return (spells?.spells || []).filter((spell) =>
      (!tradition || spell.tradition === tradition) &&
      (!circle || String(spell.circle) === circle) &&
      (!key || norm(`${spell.name} ${spell.school} ${spell.description.slice(0, 500)}`).includes(key)));
  }, [spells, search, tradition, circle]);

  const filteredAbilities = useMemo(() => {
    const key = norm(search.trim());
    return (abilities?.abilities || []).filter((ability) =>
      (!abilitySpec || ability.spec === abilitySpec) &&
      (!key || norm(`${ability.title} ${ability.spec} ${ability.description.slice(0, 500)}`).includes(key)));
  }, [abilities, search, abilitySpec]);

  const filteredItems = useMemo(() => {
    const key = norm(search.trim());
    return (items?.items || []).filter((item) =>
      (!itemCategory || item.category === itemCategory) &&
      (!key || norm(`${item.name} ${item.description.slice(0, 500)}`).includes(key)));
  }, [items, search, itemCategory]);

  const spell = spells?.spells.find((entry) => entry.id === selectedSpell) || null;
  const ability = abilities?.abilities.find((entry) => entry.id === selectedAbility) || null;
  const item = items?.items.find((entry) => entry.id === selectedItem) || null;
  async function conjureSpell() {
    if (!spell || spell.automation?.status === 'blocked' || !caster || !castTarget || commands.current.pending) return;
    setError(""); setCasting(true); setCastResult(null);
    const parsedCaster = parseTarget(caster);
    const manualDice = Boolean(castDie.trim()) && !['healing_hp', 'condition_cure'].includes(spell.automation?.family || '');
    const payload = { caster_type: parsedCaster.type, caster_id: parsedCaster.id, targets: [parseTarget(castTarget)],
      roll_mode: manualDice ? "physical" as const : "digital" as const,
      d20: manualDice ? [Number(castDie)] : undefined };
    try {
      await commands.current.run({ spellId: spell.id, payload }, async request_id => {
        const result = await castCompendiumSpell(spell.id, { ...payload, request_id });
        setCastResult(result);
        return result;
      });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao conjurar"); }
    finally { setCasting(false); }
  }
  const abilitySpecs = useMemo(() => [...new Set((abilities?.abilities || []).map((entry) => entry.spec))].sort(), [abilities]);
  const itemCategories = useMemo(() => [...new Set((items?.items || []).map((entry) => entry.category))].sort(), [items]);

  return (
    <section className="workspace-monster-catalog workspace-compendium">
      <header><strong>GRIMÓRIO E COMPÊNDIOS</strong><small>{spells ? `${spells.total} magias · ${abilities?.total || "…"} habilidades · ${items?.total || "…"} itens` : "Carregando compêndios…"}</small></header>
      {error && <small>{error}</small>}
      <div role="group" aria-label="Tipo de compêndio">
        <button type="button" className={tab === "spells" ? "active" : ""} onClick={() => setTab("spells")}>Magias</button>
        <button type="button" className={tab === "abilities" ? "active" : ""} onClick={() => setTab("abilities")}>Habilidades</button>
        <button type="button" className={tab === "items" ? "active" : ""} onClick={() => setTab("items")}>Itens</button>
        <button type="button" className={tab === "actions" ? "active" : ""} onClick={() => setTab("actions")}>Ações de monstros</button>
      </div>
      {tab === "actions" && <MonsterActionMap />}
      {tab !== "actions" && <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={tab === "spells" ? "Buscar magia por nome, escola ou efeito" : tab === "abilities" ? "Buscar habilidade por nome ou efeito" : "Buscar item por nome ou efeito"} />}
      {tab === "spells" && (
        <div>
          <select aria-label="Tradição" value={tradition} onChange={(event) => { remember('tradition', event.target.value); setTradition(event.target.value); }}>
            <option value="">Arcana + Divina</option>
            <option value="arcana">Arcana</option>
            <option value="divina">Divina</option>
          </select>
          <select aria-label="Círculo" value={circle} onChange={(event) => { remember('circle', event.target.value); setCircle(event.target.value); }}>
            <option value="">Todos os círculos</option>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => <option key={level} value={String(level)}>{level}º círculo</option>)}
          </select>
          <select aria-label="Magia do grimório" value={selectedSpell} onChange={(event) => { remember('spell', event.target.value); setSelectedSpell(event.target.value); }}>
            <option value="">Selecione uma magia… ({filteredSpells.length})</option>
            {filteredSpells.slice(0, 600).map((entry) => <option key={entry.id} value={entry.id}>{entry.name} · {entry.circle}º · {entry.tradition}</option>)}
          </select>
        </div>
      )}
      {tab === "abilities" && (
        <div>
          <select aria-label="Especialização" value={abilitySpec} onChange={(event) => setAbilitySpec(event.target.value)}>
            <option value="">Todas as especializações</option>
            {abilitySpecs.map((spec) => <option key={spec} value={spec}>{spec}</option>)}
          </select>
          <select aria-label="Habilidade do compêndio" value={selectedAbility} onChange={(event) => setSelectedAbility(event.target.value)}>
            <option value="">Selecione uma habilidade… ({filteredAbilities.length})</option>
            {filteredAbilities.slice(0, 300).map((entry) => <option key={entry.id} value={entry.id}>{entry.title} · {entry.spec}</option>)}
          </select>
        </div>
      )}
      {tab === "items" && (
        <div>
          <select aria-label="Categoria" value={itemCategory} onChange={(event) => setItemCategory(event.target.value)}>
            <option value="">Todas as categorias</option>
            {itemCategories.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
          <select aria-label="Item do compêndio" value={selectedItem} onChange={(event) => setSelectedItem(event.target.value)}>
            <option value="">Selecione um item… ({filteredItems.length})</option>
            {filteredItems.slice(0, 600).map((entry) => <option key={entry.id} value={entry.id}>{entry.name}{entry.preco ? ` · ${entry.preco}` : ""}</option>)}
          </select>
        </div>
      )}
      {tab === "spells" && spell && (
        <article className="workspace-monster-catalog-preview">
          <div><strong>{spell.name}</strong><small>{spell.tradition === "arcana" ? "Arcana" : "Divina"} · {spell.circle}º círculo · {spell.school}</small>
            <small>Alcance: {spell.alcance || "—"} · Duração: {spell.duracao || "—"}{spell.jogada_protecao ? ` · JP: ${spell.jogada_protecao}` : ""}</small>
            {spell.automation && <small>{spell.automation.note}</small>}
            <p>{spell.description}</p><small>Fonte: {spell.source}</small></div>
          <div>
            <select aria-label="Conjurador" value={caster} onChange={(event) => { remember('caster', event.target.value); setCaster(event.target.value); }}>
              <option value="">Conjurador…</option>
              {targetOptions.map((option) => <option key={`c:${option.id}`} value={option.id}>{option.name}</option>)}
            </select>
            <TargetSelect label={`Alvo de ${spell.name}`} value={castTarget} onChange={value => { remember('target', value); setCastTarget(value); }} targets={targetOptions} />
            {!['healing_hp', 'condition_cure'].includes(spell.automation?.family || '') && <input value={castDie} onChange={(event) => { remember('die', event.target.value); setCastDie(event.target.value); }} placeholder="d20 físico (opcional)" />}
            <button type="button" disabled={casting || spell.automation?.status === 'blocked' || !caster || !castTarget} onClick={() => void conjureSpell()}>{casting ? "Confirmando…" : "Conjurar"}</button>
          </div>
          {castResult && <div role="status">{castResult.results.map((outcome, index) => <p key={index}><small>{spellTargetOutcome(outcome)}</small></p>)}{castResult.manual_note && <p><small>{castResult.manual_note}</small></p>}</div>}
        </article>
      )}
      {tab === "abilities" && ability && (
        <article className="workspace-monster-catalog-preview">
          <div><strong>{ability.title}</strong><small>{ability.spec}{ability.level ? ` · nv${ability.level}` : ""}</small>
            <p>{ability.description}</p><small>Fonte: {ability.source}</small></div>
        </article>
      )}
      {tab === "items" && item && (
        <article className="workspace-monster-catalog-preview">
          <div><strong>{item.name}</strong><small>{item.category}{item.preco ? ` · ${item.preco}` : ""}{item.preco_origem === "mesa" ? " (mesa)" : ""}{item.peso ? ` · ${item.peso}` : ""}{item.alinhamento ? ` · ${item.alinhamento}` : ""}{item.dano ? ` · ${item.dano}` : ""}</small>
            <p>{item.description}</p><small>Fonte: {item.source}</small></div>
        </article>
      )}
      <small>Grimório: Tomos de Magia Arcana e Divina (OD2, CC BY-SA 4.0) · Habilidades: Mestres do Arcano (material de fã) · Itens: Livro Básico Aprimorado + Expansão de Itens (Caio Mouriz, CC-BY-SA 4.0).</small>
    </section>
  );
}
