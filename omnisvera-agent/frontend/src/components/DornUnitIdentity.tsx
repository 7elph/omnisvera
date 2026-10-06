import type { CombatEffectsState, InventoryItem, PlayableCharacter } from '../api';
import DornProtocolControls from './DornProtocolControls';

export function dornItemCategory(item: InventoryItem): string {
  const title = item.item_title.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  if (title === 'nucleo runico') return 'Sistema integrado · grimório';
  if (title === 'kit de reparo') return 'Ferramenta · sem cura instantânea';
  if (title === 'cristal de memoria danificado') return 'Componente narrativo';
  if (title === 'compartimento interno') return 'Equipamento · capacidade não definida';
  return item.item_type || 'Item sem classificação';
}

export default function DornUnitIdentity({ character, combat, onInspectItem, onOpenMagic, onProtocolChange }: {
  character: PlayableCharacter;
  combat: CombatEffectsState | null;
  onInspectItem: (item: InventoryItem) => void;
  onOpenMagic: () => void;
  onProtocolChange?: (state: CombatEffectsState) => Promise<void>;
}) {
  // This presentation never promotes Dorn or exposes GM-only identity to players.
  if (character.definition.id !== 'dorn7' || character.access_level !== 'gm') return null;
  const { definition, state, inventory } = character;
  const traits = definition.abilities?.racial;
  const components = inventory.filter(item => ['Núcleo Rúnico', 'Kit de Reparo', 'Cristal de Memória danificado', 'Compartimento interno'].includes(item.item_title));
  const core = components.find(item => item.item_title === 'Núcleo Rúnico');
  const memory = components.find(item => item.item_title === 'Cristal de Memória danificado');
  const effects = (combat?.effects || []).filter(effect => effect.target_type === 'character' && effect.target_id === 'dorn7');
  const protocols = (definition.session_abilities || []).filter(ability => ability.kind === 'technique' && ability.group === 'Ações / Protocolos');
  const modifierNames: Record<string, string> = { armor_class: 'CA', strength: 'Força', dexterity: 'Destreza', constitution: 'Constituição', intelligence: 'Inteligência', wisdom: 'Sabedoria', charisma: 'Carisma', attack_bonus: 'Ataque', saving_throw: 'Proteção' };
  return <section className="dorn-unit-identity" aria-label="Identidade da unidade DORN-7">
    <p>UNIDADE DORN-7 · {definition.race || 'Raça não registrada'} · controle do Mestre</p>
    <details><summary>TRAÇOS DE CONSTRUCTO</summary>
      {traits ? <ul>{traits.split(/(?<=\.)\s+/).filter(Boolean).map((trait, index) => <li key={index}>{trait}</li>)}</ul> : <p>Traços raciais ainda não registrados na ficha.</p>}
      <small>Referência da ficha aprovada. Imunidades, JP condicionais, cura e reparo continuam assistidos pelo Mestre; esta seção não aplica bônus.</small>
    </details>
    <details><summary>SISTEMAS DA UNIDADE</summary><dl>
      <dt>Integridade</dt><dd>{state?.current_hp ?? '—'} / {state?.maximum_hp ?? '—'} PV{state?.conditions.includes('desativado') ? ' · Desativado' : ''}</dd>
      <dt>Núcleo</dt><dd>{core ? `${core.item_title} · registrado no inventário` : 'Não registrado no inventário'}</dd>
      <dt>Memória</dt><dd>{memory?.item_title || 'Estado não registrado'}</dd>
      <dt>Comunicação</dt><dd>Estado formal não registrado</dd>
      <dt>Protocolo ativo</dt><dd>{effects.filter(e => e.protocol).map(e => e.label).join(' · ') || 'Nenhum protocolo ativo'}</dd>
      <dt>Condições registradas</dt><dd>{state?.conditions.length ? state.conditions.join(' · ') : 'Nenhuma condição registrada'}</dd>
    </dl></details>
    <details><summary>AÇÕES / PROTOCOLOS</summary>
      {onProtocolChange && protocols.length > 0 && <DornProtocolControls combat={combat} onChange={onProtocolChange} />}
      {!onProtocolChange && (protocols.length ? <p>{protocols.map(p => p.name).join(' · ')} · ações no catálogo da ficha</p> : <p>Nenhum protocolo próprio aprovado nesta ficha. Interposição, Guarda, Bloqueio e Vanguarda dependem de decisão do Mestre; não concedem ações ou bônus.</p>)}
      <button type="button" disabled={!(definition.session_abilities || []).some(ability => ability.kind === 'spell')} onClick={onOpenMagic}>Operar núcleo · abrir Magias</button>
    </details>
    <details><summary>COMPONENTES E FERRAMENTAS</summary>
      {components.map(item => <article key={item.id}><div><strong>{item.item_title}</strong><small>{dornItemCategory(item)}</small></div><button type="button" onClick={() => onInspectItem(item)}>Inspecionar</button></article>)}
      {!components.length && <p>Nenhum componente identificado no inventário atual.</p>}
      <small>Inspecionar abre o item existente. Não recupera PV, cria conteúdo no compartimento ou revela memórias.</small>
    </details>
    <details><summary>EFEITOS REGISTRADOS DA UNIDADE</summary>
      {effects.map(effect => <article key={effect.id}><strong>{effect.label}</strong><span>{effect.until || (effect.protocol === 'vanguard' ? 'Até desativar / fim de cena' : effect.rounds == null ? effect.duration : `${effect.rounds} rodada(s) restantes`)}</span><small>{Object.entries(effect.modifiers).map(([key, value]) => `${modifierNames[key] || key}: ${value >= 0 ? '+' : ''}${value}`).join(' · ')}</small></article>)}
      {!effects.length && <p>Nenhum efeito registrado para Dorn. Preparação consumida não comprova efeito ativo; duração em turnos de exploração pode continuar assistida.</p>}
    </details>
  </section>;
}
