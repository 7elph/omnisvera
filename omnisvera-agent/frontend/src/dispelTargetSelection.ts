import type { DispelPreview } from './api';

/** The server owns eligibility, source level, range, JP/check and resource cost. */
export function gridDispelCommand(preview: DispelPreview, effectId: string | undefined) {
  if (!effectId || !preview.effects.some(effect => effect.id === effectId)) throw new Error('Escolha uma magia deste alvo.');
  return { action: 'dorn_spell_cast', payload: { spell_id: 'dissipar-magia', effect_id: effectId,
    target_token_id: preview.target_token_id, target_fingerprint: preview.fingerprint,
    definition_revision: preview.definition_revision }, expected_version: preview.version };
}
