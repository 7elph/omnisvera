import { useEffect, useRef, useState } from "react";
import { getNpc, getNpcSummary, mediaUrlFromVaultPath, NpcRecord } from "../api";

type Props = { mode: "gm" | "player"; onOpen: (npcId: number) => void };

export default function QuickNpcPanel({ mode, onOpen }: Props) {
  const [npc, setNpc] = useState<NpcRecord | null>(null);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const closeRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    const listener = (event: Event) => {
      const id = Number((event as CustomEvent<number>).detail);
      if (!Number.isFinite(id) || id <= 0) return;
      setMessage(""); setOpen(true);
      getNpc(id).then(setNpc).catch((error) => setMessage(error instanceof Error ? error.message : String(error)));
    };
    window.addEventListener("omnisvera-open-npc", listener);
    return () => window.removeEventListener("omnisvera-open-npc", listener);
  }, []);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  if (!open) return null;
  const image = mediaUrlFromVaultPath(npc?.portrait_path);
  const publicRelationship = npc?.relationships?.find((item) => item.visible_to_players);
  const obligations = npc?.memories?.filter((item) => ["promise", "debt", "favor", "agreement"].includes(item.memory_type) && item.status === "active") || [];
  const priorities = npc?.memories?.filter((item) => ["critical", "high"].includes(item.importance) && item.status === "active").slice(0, 3) || [];

  async function copySummary() {
    if (!npc) return;
    const summary = await getNpcSummary(npc.id);
    await navigator.clipboard.writeText(JSON.stringify(summary, null, 2));
    setMessage("Resumo autorizado copiado. Ele não foi enviado automaticamente ao chat.");
  }

  return <div className="quick-npc-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}>
    <aside className="quick-npc-drawer" role="dialog" aria-modal="true" aria-label="Painel rápido do NPC">
      <header>
        {image ? <img src={image} alt={`Retrato de ${npc?.name || "NPC"}`} /> : <span aria-hidden="true">◉</span>}
        <div><small>{npc?.class_or_role || npc?.occupation || "NPC"}</small><strong>{npc?.name || "Carregando..."}</strong><em>{npc?.current_location || "Localização não informada"}</em></div>
        <button ref={closeRef} aria-label="Fechar painel do NPC" onClick={() => setOpen(false)}>×</button>
      </header>
      {message && <p role="status">{message}</p>}
      {npc && <>
        <section><small>Estado</small><p>{npc.public_status || "Estado público não informado."}</p></section>
        <section><small>Relação observável</small><strong>{publicRelationship?.public_label || "Ainda não revelada"}</strong></section>
        <section><small>Último encontro</small><strong>{npc.encounters?.[0]?.title || "Não registrado"}</strong></section>
        {obligations.length > 0 && <section><small>Promessas e dívidas visíveis</small>{obligations.slice(0,3).map((item) => <span key={item.id}>{item.title}</span>)}</section>}
        {mode === "gm" && <section className="quick-npc-private"><small>Prioridades do Mestre</small><strong>{npc.disposition_summary || "Disposição não registrada"}</strong>{priorities.map((item) => <span key={item.id}>{item.title}</span>)}</section>}
        <div className="quick-npc-actions"><button onClick={() => { onOpen(npc.id); setOpen(false); }}>Abrir perfil completo</button>{mode === "gm" && <button className="secondary-button" onClick={copySummary}>Copiar resumo autorizado</button>}</div>
      </>}
    </aside>
  </div>;
}
