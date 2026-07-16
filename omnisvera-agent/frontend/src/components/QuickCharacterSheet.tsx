import { useEffect, useMemo, useState } from "react";
import { DiceRollEvent, getPlayableCharacter, listPlayableCharacters, mediaUrlFromVaultPath, newDiceRequestId, PlayableCharacter, PlayableCharacterSummary, rollCharacterAction } from "../api";

function stat(value: unknown) {
  return value === null || value === undefined || value === "" ? "—" : String(value);
}

export default function QuickCharacterSheet({ hidden, triggerHidden, onOpen }: { hidden?: boolean; triggerHidden?: boolean; onOpen: () => void }) {
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [selectedId, setSelectedId] = useState(localStorage.getItem("omnisvera_selected_character") || "");
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<PlayableCharacter | null>(null);
  const [rolling, setRolling] = useState(false);
  const [rollResult, setRollResult] = useState<DiceRollEvent | null>(null);
  const [rollError, setRollError] = useState("");

  async function load() {
    try {
      const items = await listPlayableCharacters();
      const ordered = [...items].sort((a, b) => Number(b.access_level === "owner") - Number(a.access_level === "owner"));
      setCharacters(ordered);
      const fallback = ordered.find((item) => item.access_level === "owner")?.id
        || ordered.find((item) => item.id === "vezemir")?.id
        || ordered[0]?.id
        || "";
      const preferred = ordered.some((item) => item.id === selectedId) ? selectedId : fallback;
      setSelectedId(preferred);
      if (preferred) localStorage.setItem("omnisvera_selected_character", preferred);
    } catch {
      setCharacters([]);
    }
  }

  useEffect(() => {
    void load();
    const refresh = () => void load();
    const openCharacter = (event: Event) => {
      const characterId = (event as CustomEvent<string>).detail;
      if (!characterId) return;
      setSelectedId(characterId);
      setDetail(null);
      setRollResult(null);
      localStorage.setItem("omnisvera_selected_character", characterId);
      setOpen(true);
    };
    window.addEventListener("omnisvera-character-state", refresh);
    window.addEventListener("omnisvera-open-character", openCharacter);
    return () => {
      window.removeEventListener("omnisvera-character-state", refresh);
      window.removeEventListener("omnisvera-open-character", openCharacter);
    };
  }, []);

  useEffect(() => {
    if (!open || !selectedId) return;
    void getPlayableCharacter(selectedId).then(setDetail).catch(() => setDetail(null));
  }, [open, selectedId]);

  async function quickRoll(rollType: string, sourceId?: string) {
    if (rolling || !selectedId) return;
    setRolling(true); setRollError("");
    try {
      const result = await rollCharacterAction(selectedId, { request_id: newDiceRequestId("quick"), roll_type: rollType, source_id: sourceId, visibility: "table" });
      setRollResult(result);
      window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: result }));
    } catch (reason) { setRollError(reason instanceof Error ? reason.message : "Não foi possível realizar a rolagem."); }
    finally { setRolling(false); }
  }

  const character = useMemo(() => characters.find((item) => item.id === selectedId) || characters[0], [characters, selectedId]);
  if (hidden || !character || character.access_level === "public") return null;
  const portrait = mediaUrlFromVaultPath(character.portrait);

  return <aside className={`quick-character-sheet ${open ? "open" : ""}`} aria-label="Ficha rápida">
    {!open ? !triggerHidden && <button className="quick-sheet-trigger" onClick={() => setOpen(true)} aria-label={`Abrir ficha rápida de ${character.name}`}>
      {portrait ? <img src={portrait} alt="" /> : <span aria-hidden="true">♙</span>}
      <strong>{character.name}</strong><em>{stat(character.current_hp)}/{stat(character.maximum_hp)} PV</em>
    </button> : <div className="quick-sheet-drawer">
      <header>{portrait ? <img src={portrait} alt={`Retrato de ${character.name}`} /> : <span aria-hidden="true">♙</span>}<div><small>Ficha rápida</small><strong>{character.name}</strong><em>{character.race} · {character.class_name}</em></div><button className="quick-sheet-close" onClick={() => setOpen(false)} aria-label="Fechar ficha rápida">×</button></header>
      {characters.length > 1 && <select aria-label="Personagem da ficha rápida" value={character.id} onChange={(event) => { setSelectedId(event.target.value); setDetail(null); setRollResult(null); localStorage.setItem("omnisvera_selected_character", event.target.value); }}>
        {characters.filter((item) => item.access_level !== "public").map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>}
      <div className="quick-sheet-stats"><span><small>PV</small><strong>{stat(character.current_hp)}/{stat(character.maximum_hp)}</strong></span><span><small>CA</small><strong>{stat(character.armor_class)}</strong></span><span><small>Iniciativa</small><strong>{character.initiative === null || character.initiative === undefined ? "N/C" : character.initiative >= 0 ? `+${character.initiative}` : character.initiative}</strong></span><span><small>Movimento</small><strong>{stat(character.movement)}</strong></span></div>
      {!!character.conditions.length && <div className="quick-condition-list">{character.conditions.map((condition) => <span key={condition}>{condition}</span>)}</div>}
      {!!character.resources.length && <div className="quick-resource-list">{character.resources.slice(0, 3).map((resource) => <span key={resource.key}><small>{resource.label}</small><strong>{resource.current}/{resource.maximum}</strong></span>)}</div>}
      <div className="quick-roll-actions"><button disabled={rolling || detail?.definition.attribute_modifiers?.strength == null} onClick={() => void quickRoll("attribute", "strength")}>Rolar FOR</button><button disabled={rolling || !detail?.definition.defenses?.saving_throw} onClick={() => void quickRoll("saving_throw")}>Rolar proteção</button><button disabled={rolling || !detail?.definition.attacks?.some((attack) => attack.attack_bonus != null)} onClick={() => void quickRoll("attack", detail?.definition.attacks?.find((attack) => attack.attack_bonus != null)?.id)}>Rolar ataque</button><button className="secondary-button" onClick={() => window.dispatchEvent(new Event("omnisvera-open-dice-tray"))}>⚄ Dados</button></div>
      {rollResult && <div className="quick-roll-result" aria-live="assertive"><small>{rollResult.label}</small><strong>{rollResult.total}</strong></div>}
      {rollError && <p className="warning-text" role="alert">{rollError}</p>}
      <button className="quick-sheet-open-full" onClick={() => { localStorage.setItem("omnisvera_selected_character", character.id); setOpen(false); onOpen(); }}>Abrir ficha completa</button>
    </div>}
  </aside>;
}
