import { useEffect, useMemo, useRef, useState } from "react";
import {
  declareSceneAction,
  GameScene,
  getActiveScene,
  mediaUrlFromVaultPath,
  newSceneRequestId,
} from "../api";

const QUICK_ACTIONS = [
  ["investigate", "Investigar"],
  ["observe", "Observar"],
  ["talk", "Conversar"],
  ["interact", "Interagir"],
];

export default function QuickScenePanel({
  hidden,
  triggerHidden,
  mode,
  onOpen,
}: {
  hidden?: boolean;
  triggerHidden?: boolean;
  mode: "gm" | "player";
  onOpen: () => void;
}) {
  const [scene, setScene] = useState<GameScene | null>(null);
  const [open, setOpen] = useState(false);
  const [actionType, setActionType] = useState("investigate");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const closeButton = useRef<HTMLButtonElement>(null);

  async function refresh() {
    try { setScene(await getActiveScene()); } catch { setScene(null); }
  }

  useEffect(() => {
    void refresh();
    const update = () => void refresh();
    const interval = window.setInterval(update, 12000);
    window.addEventListener("omnisvera-scene-updated", update);
    window.addEventListener("omnisvera-roll-created", update);
    const show = () => setOpen(true);
    window.addEventListener("omnisvera-open-quick-scene", show);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("omnisvera-scene-updated", update);
      window.removeEventListener("omnisvera-roll-created", update);
      window.removeEventListener("omnisvera-open-quick-scene", show);
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    closeButton.current?.focus();
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [open]);

  const recentEvents = useMemo(() => scene?.events.filter((event) => !event.voided).slice(0, 3) || [], [scene]);
  const visibleClues = useMemo(() => scene?.elements.filter((element) => element.element_type === "clue").slice(0, 3) || [], [scene]);

  async function declare() {
    if (!scene || !description.trim() || busy) return;
    setBusy(true); setMessage("");
    try {
      await declareSceneAction(scene.id, {
        request_id: newSceneRequestId("quick-action"),
        action_type: actionType,
        description,
        visibility: "table",
      });
      setDescription("");
      setMessage("Ação enviada ao Mestre.");
      await refresh();
      window.dispatchEvent(new CustomEvent("omnisvera-scene-updated"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível declarar a ação.");
    } finally { setBusy(false); }
  }

  if (hidden) return null;
  return <aside className={`quick-scene-panel ${open ? "open" : ""}`} aria-label="Cena rápida">
    {!open ? !triggerHidden && <button className="quick-scene-trigger" onClick={() => setOpen(true)} aria-label="Abrir cena rápida">
      <span aria-hidden="true">Cena</span>
      <strong>{scene?.title || "Sem cena ativa"}</strong>
      {scene && <small>{scene.location_name}</small>}
    </button> : <div className="quick-scene-drawer" role="dialog" aria-modal="true" aria-label="Cena atual">
      <header>
        <div><small>{scene ? `${scene.location_name} · ${scene.status}` : "Mesa"}</small><strong>{scene?.title || "Nenhuma cena ativa"}</strong></div>
        <button ref={closeButton} className="quick-scene-close" onClick={() => setOpen(false)} aria-label="Fechar cena rápida">×</button>
      </header>
      {!scene ? <p className="sheet-empty">{mode === "gm" ? "Crie ou ative uma cena no painel completo." : "O mestre ainda não iniciou uma cena."}</p> : <>
        <p className="quick-scene-objective"><small>Objetivo</small><strong>{scene.objective || "Não informado"}</strong></p>
        <div className="quick-scene-participants" aria-label="Participantes">
          {scene.participants.filter((item) => !item.left_at).map((participant) => {
            const portrait = mediaUrlFromVaultPath(participant.character?.portrait);
            return <button key={participant.id} disabled={!participant.character_id} onClick={() => participant.character_id && window.dispatchEvent(new CustomEvent("omnisvera-open-character", { detail: participant.character_id }))}>
              {portrait ? <img src={portrait} alt="" /> : <span aria-hidden="true">P</span>}
              <small>{participant.public_label}</small>
            </button>;
          })}
        </div>
        {!!visibleClues.length && <section className="quick-scene-clues"><strong>Pistas reveladas</strong>{visibleClues.map((clue) => <span key={clue.id}>{clue.title}</span>)}</section>}
        {!!recentEvents.length && <section className="quick-scene-events"><strong>Últimos eventos</strong>{recentEvents.map((event) => <span key={event.id}>{event.title}</span>)}</section>}
        {mode === "player" && scene.status === "active" && <section className="quick-scene-action">
          <select aria-label="Tipo de ação" value={actionType} onChange={(event) => setActionType(event.target.value)}>{QUICK_ACTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select>
          <textarea maxLength={600} aria-label="Ação do personagem" placeholder="O que seu personagem tenta fazer?" value={description} onChange={(event) => setDescription(event.target.value)} />
          <button disabled={busy || !description.trim()} onClick={() => void declare()}>Declarar ação</button>
        </section>}
        {message && <p className="quick-scene-message" role="status">{message}</p>}
      </>}
      <button className="quick-scene-open-full" onClick={() => { setOpen(false); onOpen(); }}>Abrir painel completo</button>
    </div>}
  </aside>;
}
