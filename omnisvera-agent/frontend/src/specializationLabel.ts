/** Display terminology only; preserve persisted specialization IDs and rules. */
export function specializationLabel(id?: string | null, name?: string | null): string {
  if (id === 'guerreiro-arma') return 'Especialista em Armas';
  return name || id || 'Sem especialização';
}
