import { useRef, useState } from 'react';
import { getAccessToken } from '../api';

export default function AssetAdjustmentForm({ imagePath, parentJobId, category = 'map', generationMode = 'official', onCreated }: {
  imagePath: string; parentJobId?: number; category?: 'map' | 'items'; generationMode?: 'official' | 'test'; onCreated: () => void;
}) {
  const [instruction, setInstruction] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const lock = useRef(false);
  const request = useRef<{ key: string; id: string } | null>(null);
  async function submit() {
    if (lock.current || !instruction.trim()) return;
    lock.current = true; setBusy(true); setMessage('Gerando ajuste… o fallback pode aguardar a fila do ZeroGPU.');
    const key = JSON.stringify([imagePath, instruction.trim(), parentJobId, category, generationMode]);
    if (request.current?.key !== key) request.current = { key, id: crypto.randomUUID() };
    try {
      const response = await fetch('/gm/assets/adjust', { method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Omnisvera-Token': getAccessToken() || '' },
        body: JSON.stringify({ image_path: imagePath, instruction: instruction.trim(),
          parent_job_id: parentJobId, category, generation_mode: generationMode, request_id: request.current.id }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Não foi possível solicitar o ajuste');
      if (result.status === 'failed') {
        setMessage(result.error); request.current = null;
      } else {
        setMessage('Nova versão criada. Compare Antes/Depois na lista e aprove se gostar. A anterior continua intacta.');
      }
      onCreated();
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <details className="asset-adjustment-form"><summary>Pedir ajuste</summary>
    <label>O que mudar?<textarea maxLength={2000} value={instruction} disabled={busy}
      placeholder="Ex.: tire a arma; mantenha o restante igual." onChange={event => setInstruction(event.target.value)} /></label>
    <small>A imagem atual será usada como referência. {generationMode === 'test' ? 'Teste: Klein 4B, sem troca automática de modelo.' : 'Oficial: Klein 9B; se indisponível, a referência e o pedido serão enviados ao Space ZeroGPU da Black Forest Labs. Ambas as rotas possuem cotas.'}</small>
    <button type="button" disabled={busy || !instruction.trim()} onClick={() => void submit()}>{busy ? 'Ajustando…' : 'Gerar nova versão'}</button>
    {message && <p role="status">{message}</p>}
  </details>;
}
