import { useEffect, useState } from "react";
import { getCompendiumMonsterActions, listWorkspaceMonsterCatalog, type MonsterActionMap } from "../api";
import ActionCard from "./ActionCard";
import MonsterRules from "./MonsterRules";

export default function MonsterActionMap() {
  const [names, setNames] = useState<{ id: string; name: string }[]>([]);
  const [selected, setSelected] = useState("");
  const [map, setMap] = useState<MonsterActionMap | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void listWorkspaceMonsterCatalog()
      .then((catalog) => { if (active) setNames(catalog.monsters.map((monster) => ({ id: monster.id, name: monster.name }))); })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar o bestiário"); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selected) { setMap(null); return; }
    let active = true;
    setError("");
    setMap(null);
    void getCompendiumMonsterActions(selected)
      .then((result) => { if (active) setMap(result); })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar as ações"); });
    return () => { active = false; };
  }, [selected]);

  return (
    <section className="workspace-monster-catalog">
      <header><strong>AÇÕES DE MONSTROS E NPCs</strong><small>{map ? `${map.summary.attacks_ready}/${map.summary.attacks} ataques prontos · ${map.summary.active_abilities} usáveis · ${map.summary.spellcasting} conjurações · ${map.summary.blockers} pendências` : "tudo que a criatura pode fazer"}</small></header>
      {error && <small>{error}</small>}
      <select aria-label="Criatura do bestiário" value={selected} onChange={(event) => setSelected(event.target.value)}>
        <option value="">Selecione uma criatura… ({names.length})</option>
        {names.map((entry) => <option key={entry.id} value={entry.id}>{entry.name}</option>)}
      </select>
      {map && <>
        {map.blockers.length > 0 && <article><strong>Pendências do Mestre</strong>{map.blockers.map((blocker) => <p key={blocker}><small>{blocker}</small></p>)}</article>}
        <article><strong>Ataques ({map.attacks.length})</strong>
          {map.attacks.length === 0 && <p><small>Nenhum ataque cadastrado.</small></p>}
          {map.attacks.map((attack) => <ActionCard key={attack.index} actionRef={`monster:${selected}:attack:${attack.index}`} />)}
        </article>
        {map.rulebook && <MonsterRules book={map.rulebook} />}
        {!map.rulebook && map.spellcasting.length > 0 && <article><strong>Conjuração ({map.spellcasting.length})</strong>
          {map.spellcasting.map((entry) => <ActionCard key={entry.name} actionRef={`monster:${selected}:ability:${entry.name}`} />)}
        </article>}
        {!map.rulebook && map.active_abilities.length > 0 && <article><strong>Usáveis ({map.active_abilities.length})</strong>
          {map.active_abilities.map((entry) => <ActionCard key={entry.name} actionRef={`monster:${selected}:ability:${entry.name}`} />)}
        </article>}
        {!map.rulebook && map.passive_abilities.length > 0 && <details><summary><small>Passivas ({map.passive_abilities.length})</small></summary>
          {map.passive_abilities.map((entry) => <p key={entry.name}><small><b>{entry.name}:</b> {entry.description}</small></p>)}
        </details>}
      </>}
      <small>Cada ação acima é um bloco da biblioteca (ataque, JP, dano, manual). Pine a criatura para executar no turno; incompletos dizem o que falta.</small>
    </section>
  );
}
