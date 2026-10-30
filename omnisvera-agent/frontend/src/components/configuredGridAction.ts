import type { GridRingTarget, NativeActionContract } from '../api';

// Binding allowlist only. Endpoint, range, dice and costs are never client rules.
export function configuredGridCommand(contract: NativeActionContract | undefined, mapId: string, ids: string[]) {
  if (!mapId || (contract && (contract.schema_version !== 1 || contract.executor.binding !== 'dorn_relampago'
      || contract.ref !== 'technique:dorn7:relampago' || !contract.revision)))
    throw new Error('Contrato de ação não suportado. Atualize a ficha.');
  // Rolling deployment only: old backend continues enforcing its original rule.
  const limits=contract?.targeting || {min_targets:1,max_targets:3};
  if (ids.length < limits.min_targets || ids.length > limits.max_targets
      || new Set(ids).size !== ids.length)
    throw new Error('Seleção de alvos inválida.');
  return { action: 'dorn_spell_cast', payload: {
    spell_id: 'relampago', grid_selection: true,
    ...(contract ? {map_id:mapId,definition_revision:contract.revision} : {}),
    targets: ids.map(id => ({ type: 'token', id })),
  } };
}

export function selectionPinId(selected: string[], id: string, targets: GridRingTarget[]) {
  const identity = targets.find(target => target.id === id)?.entity_key;
  return identity ? selected.find(pin => targets.find(target => target.id === pin)?.entity_key === identity) || id : id;
}
