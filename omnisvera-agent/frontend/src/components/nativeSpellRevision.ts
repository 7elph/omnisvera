import type { NativeActionContract } from '../api';

const BINDINGS: Record<string, string> = {
  reflexos: 'dorn_reflexos', teia: 'dorn_teia',
  'forca-arcana': 'dorn_forca_arcana', 'dissipar-magia': 'dorn_dissipar_magia',
};

// Only definition identity travels here. Native handlers own every RPG calculation.
export function nativeSpellRevision(spell: string, contract?: NativeActionContract) {
  if (!contract) return {}; // Old backend during rolling activation.
  if (!BINDINGS[spell] || contract.schema_version !== 1
      || contract.ref !== `technique:dorn7:${spell}`
      || contract.executor.binding !== BINDINGS[spell]
      || !/^[a-z0-9-]{8,100}$/.test(contract.revision))
    throw new Error('Contrato de ação não suportado. Atualize a ficha.');
  return { definition_revision: contract.revision };
}
