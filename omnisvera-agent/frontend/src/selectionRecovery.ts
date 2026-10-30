/** Optional same-tab selector convenience; never sends or authorizes an action. */
type SelectionOptions = { scope: () => Promise<string>; storage: () => Pick<Storage, 'getItem' | 'setItem'> };
const fields = ['spell', 'caster', 'target', 'tradition', 'circle', 'die'];
function sanitize(value: unknown): Record<string, string> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const result: Record<string, string> = {};
  for (const key of fields) {
    const field = (value as Record<string, unknown>)[key];
    if (typeof field === 'string' && field.length <= 200 && !/[\u0000-\u001f]/.test(field)) result[key] = field;
  }
  return result;
}
export async function loadSelection(options: SelectionOptions): Promise<Record<string, string> | null> {
  try {
    const scope = await options.scope(), raw = options.storage().getItem(`omnisvera:selection:v1:${scope}`);
    if (!raw || raw.length > 2048 || await options.scope() !== scope) return null;
    return sanitize(JSON.parse(raw));
  } catch { return null; }
}
export async function saveSelection(options: SelectionOptions, value: unknown, current: () => boolean): Promise<void> {
  try {
    const scope = await options.scope(), safe = sanitize(value);
    if (safe && current() && await options.scope() === scope && current()) {
      options.storage().setItem(`omnisvera:selection:v1:${scope}`, JSON.stringify(safe));
    }
  } catch { /* Optional selector recovery cannot bypass the command journal. */ }
}
