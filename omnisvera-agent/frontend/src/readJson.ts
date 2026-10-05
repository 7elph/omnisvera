/** Bounded, cancellable reads only. Never retries domain mutations. */
export async function readJson<T>(url: string, headers: Record<string, string>, message: string, timeoutMs = 10_000): Promise<T> {
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
        const response = await fetch(url, { headers, signal: controller.signal });
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.detail || message);
        }
        return await response.json() as T;
      })(),
      deadline,
    ]);
  } finally {
    clearTimeout(timer);
  }
}
