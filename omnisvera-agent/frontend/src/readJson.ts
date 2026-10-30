/** Bounded reads, shared only while pending and only for the same credentials. */
const pendingReads = new Map<string, Promise<unknown>>();

export class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function readJson<T>(url: string, headers: Record<string, string>, message: string, timeoutMs = 10_000): Promise<T> {
  const key = JSON.stringify([url, Object.entries(headers).sort(([a], [b]) => a.localeCompare(b)), timeoutMs]);
  let pending = pendingReads.get(key);
  if (!pending) {
    pending = boundedRead<T>(url, headers, message, timeoutMs);
    pendingReads.set(key, pending);
  }
  try {
    // Callers must not mutate another panel's snapshot.
    return JSON.parse(JSON.stringify(await pending)) as T;
  } finally {
    if (pendingReads.get(key) === pending) pendingReads.delete(key);
  }
}

async function boundedRead<T>(url: string, headers: Record<string, string>, message: string, timeoutMs: number): Promise<T> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      reject(new Error(`${message}: conexão demorou demais. Tentaremos atualizar novamente.`));
      controller.abort();
    }, timeoutMs);
  });
  try {
    return await Promise.race([
      (async () => {
        const response = await fetch(url, { headers, signal: controller.signal, priority: 'high' });
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new HttpError(response.status, body?.detail || message);
        }
        return await response.json() as T;
      })(),
      deadline,
    ]);
  } finally {
    clearTimeout(timer);
  }
}
