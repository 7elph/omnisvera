import { useEffect, useState } from 'react';

export function workersQuotaReset(now: number): number {
  const date = new Date(now);
  return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 1);
}

export function quotaCountdown(now: number): string {
  const seconds = Math.max(0, Math.ceil((workersQuotaReset(now) - now) / 1000));
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
    .map(value => String(value).padStart(2, '0')).join(':');
}

export default function WorkersQuotaClock() {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, []);
  return <div className="workers-quota-clock">
    <strong>Renovação prevista em <time>{quotaCountdown(now)}</time></strong>
    <small>21h de Brasília · 00:00 UTC. Relógio estimado, não saldo consultado. 4B e 9B compartilham a franquia; a liberação depende do provider.</small>
  </div>;
}
