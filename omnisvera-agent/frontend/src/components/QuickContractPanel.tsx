import { useEffect, useMemo, useRef, useState } from "react";
import { AccessMode, ContractRecord, listContracts } from "../api";

function label(value?: string | null) {
  const labels: Record<string, string> = {
    published: "Disponível",
    accepted: "Aceito",
    active: "Em andamento",
    completed: "Concluído",
    failed: "Falhou",
    abandoned: "Abandonado",
    cancelled: "Cancelado",
  };
  return labels[value || ""] || value || "Sem status";
}

function progress(contract: ContractRecord | null) {
  const objective = contract?.objectives.find((item) => item.status === "active")
    || contract?.objectives.find((item) => item.status === "available");
  if (!objective) return { title: "Sem objetivo ativo", value: "Narrativo" };
  if (objective.progress_current == null || objective.progress_target == null) return { title: objective.title, value: "Narrativo" };
  return { title: objective.title, value: `${objective.progress_current}/${objective.progress_target}` };
}

export default function QuickContractPanel({
  hidden,
  triggerHidden,
  mode,
  onOpenContract,
  onOpenScene,
}: {
  hidden?: boolean;
  triggerHidden?: boolean;
  mode: AccessMode;
  onOpenContract: (contractId?: number) => void;
  onOpenScene: (sceneId?: number) => void;
}) {
  const [contracts, setContracts] = useState<ContractRecord[]>([]);
  const [open, setOpen] = useState(false);
  const closeButton = useRef<HTMLButtonElement>(null);

  async function refresh() {
    try { setContracts(await listContracts()); } catch { setContracts([]); }
  }

  useEffect(() => {
    void refresh();
    const update = () => void refresh();
    const interval = window.setInterval(update, 12000);
    window.addEventListener("omnisvera-contract-updated", update);
    window.addEventListener("omnisvera-scene-updated", update);
    const show = () => setOpen(true);
    window.addEventListener("omnisvera-open-quick-contract", show);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("omnisvera-contract-updated", update);
      window.removeEventListener("omnisvera-scene-updated", update);
      window.removeEventListener("omnisvera-open-quick-contract", show);
    };
  }, [mode]);

  useEffect(() => {
    if (!open) return;
    closeButton.current?.focus();
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [open]);

  const contract = useMemo(() => contracts.find((item) => item.status === "active")
    || contracts.find((item) => item.status === "accepted")
    || contracts.find((item) => item.status === "published")
    || null, [contracts]);
  const objective = progress(contract);
  const reward = contract?.rewards.find((item) => item.visibility === "table");
  const scene = contract?.scene_links.find((item) => item.scene_status === "active") || contract?.scene_links[0];

  if (hidden) return null;
  return <aside className={`quick-contract-panel ${open ? "open" : ""}`} aria-label="Contrato rápido">
    {!open ? !triggerHidden && <button className="quick-contract-trigger" onClick={() => setOpen(true)} aria-label="Abrir contrato rápido">
      <span aria-hidden="true">Contrato</span>
      <strong>{contract?.title || "Sem contrato ativo"}</strong>
      {contract && <small>{label(contract.status)}</small>}
    </button> : <div className="quick-contract-drawer" role="dialog" aria-modal="true" aria-label="Contrato ativo">
      <header>
        <div><small>{contract ? label(contract.status) : "Conclave dos Errantes"}</small><strong>{contract?.title || "Nenhum contrato ativo"}</strong></div>
        <button ref={closeButton} className="quick-contract-close" onClick={() => setOpen(false)} aria-label="Fechar contrato rápido">×</button>
      </header>
      {!contract ? <p className="sheet-empty">{mode === "gm" ? "Nenhum contrato publicado. Crie um contrato no hub." : "Nenhum contrato disponível no momento."}</p> : <>
        <p className="quick-contract-objective"><small>Objetivo principal</small><strong>{objective.title}</strong><span>{objective.value}</span></p>
        <p className="quick-contract-reward"><small>Recompensa pública</small><strong>{reward?.label || "Recompensa ainda não revelada."}</strong></p>
        {scene && <button className="quick-contract-scene" onClick={() => { setOpen(false); onOpenScene(scene.scene_id); }}>Abrir cena relacionada</button>}
      </>}
      <button className="quick-contract-open-full" onClick={() => { setOpen(false); onOpenContract(contract?.id); }}>Abrir Conclave</button>
    </div>}
  </aside>;
}
