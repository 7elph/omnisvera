type RecoveryStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
export type CommandRecoveryOptions = {
  storage: () => RecoveryStorage;
  scope: () => Promise<string>;
  digest: (value: string) => Promise<string>;
};

function readJournal(storage: RecoveryStorage, key: string): Record<string, string> {
  const raw = storage.getItem(key);
  if (raw === null) return {};
  if (raw.length > 16_384) throw new Error('Registro de recuperação inválido; nenhum comando foi enviado.');
  const journal = JSON.parse(raw);
  if (journal?.version !== 1 || !journal.pending || typeof journal.pending !== 'object' || Array.isArray(journal.pending)
      || Object.entries(journal.pending).some(([hash, id]) => !/^[a-f0-9]{64}$/.test(hash)
        || typeof id !== 'string' || !/^[A-Za-z0-9._:-]{1,120}$/.test(id))) {
    throw new Error('Registro de recuperação inválido; nenhum comando foi enviado.');
  }
  return journal.pending;
}

/** Persist only opaque digests and request IDs; never credentials or ficha payloads. */
export function createCommandRetry(makeId: () => string, recovery?: CommandRecoveryOptions) {
  let pending = false;
  let receipt: { intent: string; id: string; scope: string | null } | null = null;
  return {
    get pending() { return pending; },
    async run<T>(intent: unknown, sendAndSync: (requestId: string) => Promise<T>): Promise<T | undefined> {
      if (pending) return undefined;
      pending = true;
      try {
        const key = JSON.stringify(intent);
        if (key === undefined) throw new Error('Comando sem intenção definida.');
        const scope = recovery ? await recovery.scope() : null;
        const storage = recovery?.storage();
        const journalKey = scope ? `omnisvera:command:v1:${scope}` : '';
        const hash = recovery ? await recovery.digest(key) : '';
        const journal = storage ? readJournal(storage, journalKey) : {};
        if (!receipt || receipt.intent !== key || receipt.scope !== scope) {
          receipt = { intent: key, id: journal[hash] || makeId(), scope };
        }
        if (storage) {
          if (!journal[hash] && Object.keys(journal).length >= 32) {
            throw new Error('Há 32 comandos pendentes nesta aba. Recupere as confirmações antes de enviar outra ação.');
          }
          journal[hash] = receipt.id;
          const serialized = JSON.stringify({ version: 1, pending: journal });
          storage.setItem(journalKey, serialized);
          if (storage.getItem(journalKey) !== serialized) throw new Error('Não foi possível guardar a confirmação; nenhum comando foi enviado.');
          if (await recovery!.scope() !== scope) throw new Error('O acesso mudou; nenhum comando foi enviado.');
        }
        const result = await sendAndSync(receipt.id);
        if (storage) {
          if (await recovery!.scope() !== scope) throw new Error('O acesso mudou após a ação. A confirmação foi preservada.');
          const latest = readJournal(storage, journalKey);
          if (latest[hash] === receipt.id) {
            delete latest[hash];
            if (Object.keys(latest).length) storage.setItem(journalKey, JSON.stringify({ version: 1, pending: latest }));
            else storage.removeItem(journalKey);
          }
        }
        receipt = null;
        return result;
      } finally {
        pending = false;
      }
    },
  };
}
