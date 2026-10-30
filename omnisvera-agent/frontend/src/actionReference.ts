import type { NativeActionManifest, NativeActionEntry, PlayableCharacter, SessionActionCard } from './api';

export type ActionReferenceCard = SessionActionCard & { category: string; status: string };
export const searchText = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');

/** Bindings describe native integration, never certification or permission to execute. */
export function referenceWithManifest(cards: ActionReferenceCard[], manifest: NativeActionManifest | null): ActionReferenceCard[] {
  const status = (entry?: NativeActionEntry) => !entry ? 'Automação não verificada'
    : entry.automation_scope === 'passive' ? 'Passiva · aplicação a verificar'
    : entry.automation_scope === 'blocked' || ['unavailable', 'blocked'].includes(entry.availability.state) ? 'Indisponível agora'
    : entry.automation_scope === 'native' ? 'Comando integrado' : 'Requer arbitragem';
  const actions = manifest?.actions || [], owner = manifest?.character_id;
  const consumed = new Set<string>();
  const rows: ActionReferenceCard[] = [];
  const describe = (entry: NativeActionEntry, text: string) => [text, entry.availability.reason, ...entry.limitations].filter(Boolean).join('\n\n');
  for (const card of cards) {
    const ref = card.id.startsWith('attack:') ? `attack:${owner}:${card.id.slice(7)}` : `technique:${owner}:${card.id}`;
    const entry = actions.find(a => a.ref === ref || a.ref === `item:${owner}:${card.id}`);
    if (entry) consumed.add(entry.ref);
    if (entry?.visible_on_sheet === false) continue;
    rows.push({ ...card, status: card.id.startsWith('trait:') ? 'Consulta de regras' : status(entry),
      description: entry ? describe(entry, card.description) : card.description });
  }
  for (const entry of actions) {
    if (entry.visible_on_sheet === false || consumed.has(entry.ref) || rows.some(row => searchText(row.name) === searchText(entry.label))) continue;
    rows.push({ id: entry.ref, name: entry.label, image_path: entry.image_path,
      description: describe(entry, entry.description || 'Consulte a regra cadastrada na ficha.'),
      category: entry.automation_scope === 'passive' ? 'Passivas' : entry.kind === 'item' ? 'Itens e efeitos'
        : entry.kind === 'attack' ? 'Ataques' : entry.group || 'Habilidades', status: status(entry) });
  }
  return rows;
}

/** Read-only projection of the actual sheet. No new mechanics or execution. */
export function characterActionReference(character: PlayableCharacter): ActionReferenceCard[] {
  const rows: ActionReferenceCard[] = [], definition = character.definition;
  const seenIds = new Set<string>(), seenNames = new Set<string>();
  const add = (card: ActionReferenceCard) => {
    if (seenIds.has(card.id) || seenNames.has(searchText(card.name))) return;
    seenIds.add(card.id); seenNames.add(searchText(card.name)); rows.push(card);
  };
  const categories = { spell: 'Magias', attack: 'Ataques', technique: 'Técnicas', power: 'Poderes', resource: 'Recursos', ability: 'Habilidades', passive: 'Passivas' };
  for (const ability of definition.session_abilities || []) {
    if (ability.hidden) continue;
    const resource = character.state?.resources?.find(item => item.key === ability.uses?.resource_key);
    const equipmentMissing = ability.requires_equipped_item && !character.inventory.some(item => item.item_path === ability.requires_equipped_item && item.equipped);
    add({ id: ability.id, name: ability.name, category: categories[ability.kind] || 'Habilidades', image_path: ability.image_path,
      status: ability.blocked ? 'Bloqueada na ficha' : equipmentMissing ? 'Exige item equipado' : resource && resource.current < (ability.uses?.cost || 1) ? 'Sem usos nesta consulta' : ability.mechanics_status === 'partial' ? 'Regras parciais' : 'Regras cadastradas',
      description: [ability.description || 'Sem descrição cadastrada.',
        ability.circle ? `Círculo: ${ability.circle}.` : '',
        ability.uses ? `Custo cadastrado: ${ability.uses.cost ?? 1} · ${ability.uses.label || ability.uses.resource_key}.` : '',
        resource ? `Reserva na consulta: ${resource.current}/${resource.maximum}.` : '',
        ability.requires_target ? 'Requer alvo.' : '', equipmentMissing ? 'O item exigido não está equipado.' : '',
        ability.blocked ? 'Esta opção está bloqueada na ficha; consultar não a desbloqueia.' : '',
        ability.mechanics_status === 'partial' ? 'A ficha marca regras parciais; a consulta não automatiza o que depende do Mestre.' : '',
      ].filter(Boolean).join('\n\n') });
  }
  for (const attack of definition.attacks || []) {
    if (seenIds.has(attack.id)) continue;
    const weapon = attack.equipment?.find(item => item.role === 'weapon');
    add({ id: `attack:${attack.id}`, name: attack.name, category: 'Ataques', status: 'Ataque da ficha', image_path: weapon?.thumbnail || weapon?.cover,
      description: [attack.notes || definition.attack_notes || 'Ataque cadastrado na ficha.',
        attack.attack_bonus != null ? `Bônus de ataque: ${attack.attack_bonus >= 0 ? '+' : ''}${attack.attack_bonus}.` : '',
        attack.damage ? `Dano: ${attack.damage}.` : '', attack.range ? `Alcance: ${attack.range}.` : '',
        attack.attack_count ? `Ataques cadastrados: ${attack.attack_count}.` : '', weapon?.item_title ? `Arma: ${weapon.item_title}.` : '',
      ].filter(Boolean).join('\n\n') });
  }
  for (const [key, description] of Object.entries(definition.abilities || {})) {
    const labels: Record<string, string> = { class: 'Classe', racial: 'Traços raciais', race: 'Traços raciais', specialization: 'Especialização' };
    const name = labels[key] || key.replace(/_/g, ' ').replace(/^./, letter => letter.toLocaleUpperCase('pt-BR'));
    add({ id: `trait:${key}`, name, description, category: 'Traços e passivas', status: 'Descrição da ficha' });
  }
  for (const item of character.inventory || []) {
    if (item.quantity <= 0 || !(item.usable || item.equipped && item.effect_rules?.length)) continue;
    add({ id: item.item_path, name: item.item_title, category: 'Itens e efeitos', image_path: item.thumbnail || item.cover,
      status: item.equipped ? 'Equipado' : 'No inventário',
      description: [item.description || 'Sem descrição cadastrada.', ...(item.effects || []),
        ...(item.effect_rules || []).map(rule => rule.label || ''), `Quantidade na consulta: ${item.quantity}.`,
        item.charges_current != null ? `Cargas na consulta: ${item.charges_current}/${item.charges_max ?? '—'}.` : '',
      ].filter(Boolean).join('\n\n') });
  }
  return rows;
}

export type ActivityFilters = { actor: string; kind: 'all' | 'actions'; query: string };
export function filterActivity<T extends { actorId?: string | null; actor?: string; kind: string; title: string; detail?: string; cards?: SessionActionCard[] }>(entries: T[], filters: ActivityFilters): T[] {
  const query = searchText(filters.query.trim());
  return entries.filter(entry => (!filters.actor || (entry.actorId || entry.actor) === filters.actor) &&
    (filters.kind === 'all' || ['action', 'roll'].includes(entry.kind)) &&
    (!query || searchText([entry.title, entry.actor, entry.detail, ...(entry.cards || []).flatMap(card => [card.name, card.description])].filter(Boolean).join(' ')).includes(query)));
}
