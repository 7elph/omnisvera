import { useEffect, useRef, useState } from "react";
import { getPlayableCharacter, JourneyRecord, listJourneys, listWorldLocations, PlayableCharacter, WorldLocationRecord } from "../api";

type Destination = "sheet" | "scene" | "conclave" | "npcs" | "map";

export default function QuickAccessMenu({ onNavigate }: { onNavigate: (destination: Destination) => void }) {
  const [open, setOpen] = useState(false);
  const [journey, setJourney] = useState<JourneyRecord | null>(null);
  const [character, setCharacter] = useState<PlayableCharacter | null>(null);
  const [locations, setLocations] = useState<WorldLocationRecord[]>([]);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const refresh = () => void Promise.all([
      listJourneys(),
      listWorldLocations(),
      getPlayableCharacter(localStorage.getItem("omnisvera_selected_character") || "vezemir").catch(() => null),
    ]).then(([items, locationItems, currentCharacter]) => {
      setJourney(items.find((item) => item.status === "active" || item.status === "paused") || null);
      setLocations(locationItems);
      setCharacter(currentCharacter);
    }).catch(() => setJourney(null));
    refresh();
    window.addEventListener("omnisvera-journey-updated", refresh);
    return () => window.removeEventListener("omnisvera-journey-updated", refresh);
  }, []);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [open]);

  function action(callback: () => void) {
    setOpen(false);
    callback();
  }

  return <div className="quick-access-menu">
    <button className="quick-access-trigger secondary-button" onClick={() => setOpen(true)} aria-label="Abrir acesso rápido da mesa">
      <span aria-hidden="true">☰</span><span>Acesso rápido</span>
    </button>
    {open && <div className="quick-access-backdrop" onClick={(event) => event.target === event.currentTarget && setOpen(false)}>
      <section className="quick-access-drawer" role="dialog" aria-modal="true" aria-labelledby="quick-access-title">
        <header><div><small>Mesa</small><h2 id="quick-access-title">Acesso rápido</h2></div><button ref={closeRef} onClick={() => setOpen(false)} aria-label="Fechar acesso rápido">×</button></header>
        {journey && <button className="quick-journey-summary" onClick={() => action(() => onNavigate("map"))}>
          <span>{character?.state?.location || "Em viagem"} → {locations.find((item) => item.id === journey.destination_location_id)?.name || "Destino"}</span><strong>{journey.title}</strong><small>{journey.progress_current}/{journey.progress_target} · {journey.status === "paused" ? "pausada" : "em andamento"}</small>
        </button>}
        {!journey && character && <button className="quick-journey-summary idle" onClick={() => action(() => onNavigate("map"))}><span>Localização atual</span><strong>{character.state?.location || character.definition.location || "Não informada"}</strong><small>Abrir mapa e rotas conhecidas</small></button>}
        <div className="quick-access-grid">
          <button onClick={() => action(() => window.dispatchEvent(new CustomEvent("omnisvera-open-character", { detail: localStorage.getItem("omnisvera_selected_character") || "vezemir" })))}><span>♜</span><strong>Ficha rápida</strong></button>
          <button onClick={() => action(() => window.dispatchEvent(new CustomEvent("omnisvera-open-quick-scene")))}><span>◈</span><strong>Cena rápida</strong></button>
          <button onClick={() => action(() => window.dispatchEvent(new CustomEvent("omnisvera-open-quick-contract")))}><span>✦</span><strong>Contrato</strong></button>
          <button onClick={() => action(() => window.dispatchEvent(new CustomEvent("omnisvera-open-dice-tray")))}><span>⚄</span><strong>Dados</strong></button>
          <button onClick={() => action(() => onNavigate("map"))}><span>⌖</span><strong>Mapa e viagem</strong></button>
          <button onClick={() => action(() => onNavigate("npcs"))}><span>◉</span><strong>NPCs</strong></button>
        </div>
        <button className="quick-access-full" onClick={() => action(() => onNavigate("sheet"))}>Abrir ficha completa</button>
      </section>
    </div>}
  </div>;
}
