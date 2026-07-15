import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import {
  CharacterSheet,
  CharacterSheetStep,
  getPlayerCharacterSheet,
  listGmCharacterSheets,
  reviewCharacterSheet,
  savePlayerCharacterSheetStep,
  submitPlayerCharacterSheet,
} from "../api";

type FieldDefinition = {
  key: string;
  label: string;
  kind?: "number" | "textarea" | "select";
  help?: string;
  options?: Array<{ value: string; label: string }>;
};

const FIELD_DEFINITIONS: Record<string, FieldDefinition[]> = {
  attributes: [
    { key: "strength", label: "Força", kind: "number" },
    { key: "dexterity", label: "Destreza", kind: "number" },
    { key: "constitution", label: "Constituição", kind: "number" },
    { key: "intelligence", label: "Inteligência", kind: "number" },
    { key: "wisdom", label: "Sabedoria", kind: "number" },
    { key: "charisma", label: "Carisma", kind: "number" },
  ],
  race: [
    { key: "race", label: "Raça" },
    { key: "movement", label: "Movimento", help: "Ex.: 9 m" },
    { key: "racial_abilities", label: "Habilidades raciais", kind: "textarea" },
  ],
  character_class: [
    { key: "class_name", label: "Classe" },
    { key: "level", label: "Nível", kind: "number" },
    { key: "hit_points", label: "Pontos de Vida", kind: "number" },
    { key: "saving_throw", label: "Jogada de Proteção", help: "Anote o valor usado na ficha." },
    { key: "base_attack", label: "Base de Ataque", kind: "number" },
    { key: "experience", label: "Experiência", kind: "number" },
    { key: "class_abilities", label: "Habilidades de classe", kind: "textarea" },
  ],
  attacks: [
    { key: "melee_bonus", label: "Bônus corpo a corpo", kind: "number" },
    { key: "ranged_bonus", label: "Bônus à distância", kind: "number" },
    { key: "attack_notes", label: "Armas, dano e observações", kind: "textarea" },
  ],
  languages: [
    { key: "spoken_languages", label: "Idiomas falados", kind: "textarea" },
    { key: "written_languages", label: "Idiomas lidos ou escritos", kind: "textarea" },
  ],
  alignment: [
    {
      key: "alignment", label: "Alinhamento", kind: "select", options: [
        { value: "", label: "Escolha..." },
        { value: "Ordeiro", label: "Ordeiro" },
        { value: "Neutro", label: "Neutro" },
        { value: "Caótico", label: "Caótico" },
      ],
    },
  ],
  equipment: [
    { key: "equipment_list", label: "Equipamentos", kind: "textarea" },
    { key: "starting_gold", label: "Ouro disponível", kind: "number" },
    { key: "carried_weight", label: "Peso carregado", kind: "number" },
    {
      key: "load_status", label: "Condição de carga", kind: "select", options: [
        { value: "", label: "Calcular..." },
        { value: "leve", label: "Carga leve" },
        { value: "media", label: "Carga média" },
        { value: "pesada", label: "Carga pesada" },
      ],
    },
  ],
  armor: [
    { key: "armor_class", label: "Classe de Armadura", kind: "number" },
    { key: "armor_breakdown", label: "Cálculo da defesa", kind: "textarea", help: "Base, Destreza, armadura, escudo e outros bônus." },
  ],
  magic: [
    {
      key: "magic_mode", label: "Fonte de magia ou poderes", kind: "select", options: [
        { value: "", label: "Escolha..." },
        { value: "none", label: "Não se aplica" },
        { value: "arcane", label: "Magia arcana" },
        { value: "divine", label: "Magia divina" },
        { value: "alchemical", label: "Fórmulas alquímicas" },
        { value: "blood", label: "Hemomancia" },
        { value: "special", label: "Poder especial" },
      ],
    },
    { key: "known_magic", label: "Magias, fórmulas ou técnicas conhecidas", kind: "textarea" },
    { key: "magic_notes", label: "Memorização, usos e observações", kind: "textarea" },
  ],
  details: [
    { key: "physical_description", label: "Aparência física", kind: "textarea" },
    { key: "personality", label: "Personalidade", kind: "textarea" },
    { key: "background", label: "Histórico antes da aventura", kind: "textarea" },
    { key: "goals", label: "Objetivos e motivações", kind: "textarea" },
  ],
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Em preenchimento",
  submitted: "Entregue ao Mestre",
  approved: "Aprovada",
  changes_requested: "Ajustes solicitados",
};

function valueForInput(value: string | number | null | undefined) {
  return value === null || value === undefined ? "" : String(value);
}

function StepGuide({ step }: { step: CharacterSheetStep }) {
  const guide = step.guide || {};
  const sources = guide.sources || [];
  if (!guide.instruction && !sources.length) return null;
  return (
    <aside className="sheet-rule-guide">
      <div className="sheet-rule-intro">
        <span className="sheet-rule-icon">✦</span>
        <div><small>Como concluir esta etapa</small><p>{guide.instruction}</p></div>
      </div>
      {!!guide.calculations?.length && (
        <div className="sheet-calculations">
          {guide.calculations.map((calculation) => <strong key={calculation}>{calculation}</strong>)}
        </div>
      )}
      {!!guide.checklist?.length && (
        <ul className="sheet-rule-checklist">
          {guide.checklist.map((item) => <li key={item}>{item}</li>)}
        </ul>
      )}
      {sources.map((source) => {
        const extraTables = (source.tables || []).slice(source.rules?.length ? 1 : 0);
        return (
          <details className="sheet-source-card" key={`${source.kind}-${source.title}`} open={step.key === "race" || step.key === "character_class"}>
            <summary><span>{source.kind === "race" ? "Raça" : "Classe"}</span><strong>{source.title}</strong><b>consultar regras</b></summary>
            <div className="sheet-source-content">
              {source.intro && <p>{source.intro}</p>}
              {!!source.rules?.length && (
                <dl className="sheet-rule-list">
                  {source.rules.map((rule) => <div key={`${rule.label}-${rule.value}`}><dt>{rule.label}</dt><dd>{rule.value}</dd></div>)}
                </dl>
              )}
              {!!Object.keys(source.level_one || {}).length && (
                <div className="sheet-level-one">
                  <small>Progressão no nível atual</small>
                  <div>{Object.entries(source.level_one || {}).map(([label, value]) => <span key={label}><b>{label}</b><strong>{value}</strong></span>)}</div>
                </div>
              )}
              {extraTables.map((table, tableIndex) => (
                <div className="sheet-reference-table" key={`${source.title}-table-${tableIndex}`}>
                  <table><thead><tr>{table.headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{table.rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={`${cellIndex}-${cell}`}>{cell}</td>)}</tr>)}</tbody></table>
                </div>
              ))}
              {!!source.abilities?.length && (
                <div className="sheet-abilities">
                  {source.abilities.map((ability) => <article key={ability.title}><strong>{ability.title}</strong><p>{ability.text}</p></article>)}
                </div>
              )}
            </div>
          </details>
        );
      })}
    </aside>
  );
}

function StepEditor({
  step,
  readOnly,
  onSave,
}: {
  step: CharacterSheetStep;
  readOnly: boolean;
  onSave: (fields: Record<string, string | number | null>) => Promise<void>;
}) {
  const [draft, setDraft] = useState<Record<string, string | number | null>>(step.fields);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState("");

  useEffect(() => setDraft(step.fields), [step]);
  const fields = FIELD_DEFINITIONS[step.key] || [];
  const dirty = JSON.stringify(draft) !== JSON.stringify(step.fields);

  async function save() {
    setSaving(true);
    setFeedback("");
    try {
      await onSave(draft);
      setFeedback("Etapa salva.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Não foi possível salvar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="sheet-step-form">
      <div className={`sheet-fields sheet-fields-${step.key}`}>
        {fields.map((field) => {
          const value = valueForInput(draft[field.key]);
          const missing = step.missing_fields.includes(field.key);
          return (
            <label key={field.key} className={missing ? "missing" : ""}>
              <span>{field.label}{missing && <em>pendente</em>}</span>
              {field.kind === "textarea" ? (
                <textarea
                  value={value}
                  disabled={readOnly}
                  rows={field.key === "background" ? 9 : 4}
                  onChange={(event) => setDraft({ ...draft, [field.key]: event.target.value })}
                />
              ) : field.kind === "select" ? (
                <select value={value} disabled={readOnly} onChange={(event) => setDraft({ ...draft, [field.key]: event.target.value })}>
                  {value && !field.options?.some((option) => option.value === value) && <option value={value}>{value} — valor atual; confirme com o Mestre</option>}
                  {field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              ) : (
                <input
                  value={value}
                  disabled={readOnly}
                  inputMode={field.kind === "number" ? "numeric" : "text"}
                  type={field.kind === "number" ? "number" : "text"}
                  onChange={(event) => setDraft({ ...draft, [field.key]: field.kind === "number" ? (event.target.value === "" ? null : Number(event.target.value)) : event.target.value })}
                />
              )}
              {field.help && <small>{field.help}</small>}
            </label>
          );
        })}
      </div>
      {!readOnly && (
        <div className="sheet-save-row">
          <span>{feedback}</span>
          <button disabled={!dirty || saving} onClick={() => void save()}>{saving ? "Salvando..." : "Salvar etapa"}</button>
        </div>
      )}
    </div>
  );
}

function SheetView({ sheet, readOnly, onChange }: { sheet: CharacterSheet; readOnly: boolean; onChange: (sheet: CharacterSheet) => void }) {
  const [openStep, setOpenStep] = useState(sheet.steps.find((step) => step.status === "pending")?.key || sheet.steps[0]?.key || "");
  const [feedback, setFeedback] = useState("");
  const percent = Math.round((sheet.completion_count / sheet.total_steps) * 100);
  const stepFields = (key: string) => sheet.steps.find((step) => step.key === key)?.fields || {};
  const classFields = stepFields("character_class");
  const attackFields = stepFields("attacks");
  const armorFields = stepFields("armor");
  const raceFields = stepFields("race");
  const equipmentFields = stepFields("equipment");
  const quickStats = [
    ["Nível", classFields.level],
    ["PV", classFields.hit_points],
    ["CA", armorFields.armor_class],
    ["BA", classFields.base_attack],
    ["Ataque corpo a corpo", attackFields.melee_bonus],
    ["Ataque à distância", attackFields.ranged_bonus],
    ["Movimento", raceFields.movement],
    ["Carga", equipmentFields.load_status],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "");

  async function saveStep(stepKey: string, fields: Record<string, string | number | null>) {
    const updated = await savePlayerCharacterSheetStep(stepKey, fields);
    onChange(updated);
  }

  async function submit() {
    setFeedback("");
    try {
      const updated = await submitPlayerCharacterSheet();
      onChange(updated);
      setFeedback("Ficha entregue ao Mestre.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Não foi possível entregar a ficha.");
    }
  }

  return (
    <div className="character-sheet-shell">
      <header className="sheet-overview">
        <div>
          <p className="eyebrow">Personagem em 10 etapas</p>
          <h2>{sheet.character_title}</h2>
          <span className={`sheet-status status-${sheet.status}`}>{STATUS_LABELS[sheet.status] || sheet.status}</span>
        </div>
        <div className="sheet-progress-ring" style={{ "--sheet-progress": `${percent * 3.6}deg` } as CSSProperties}>
          <strong>{sheet.completion_count}/{sheet.total_steps}</strong>
          <small>concluídas</small>
        </div>
      </header>
      <div className="sheet-progress-bar"><span style={{ width: `${percent}%` }} /></div>
      <section className="sheet-quick-summary">
        <div><p className="eyebrow">Resumo mecânico</p><small>Atualizado conforme as etapas são salvas.</small></div>
        <div>{quickStats.map(([label, value]) => <span key={String(label)}><small>{label}</small><strong>{String(value)}</strong></span>)}</div>
      </section>
      {sheet.gm_feedback && <blockquote className="sheet-feedback"><strong>Retorno do Mestre</strong>{sheet.gm_feedback}</blockquote>}

      <div className="sheet-steps">
        {sheet.steps.map((step) => {
          const open = openStep === step.key;
          return (
            <section key={step.key} className={`sheet-step ${step.status} ${open ? "open" : ""}`}>
              <button className="sheet-step-heading" onClick={() => setOpenStep(open ? "" : step.key)}>
                <span className="sheet-step-state">{step.status === "complete" ? "✓" : "!"}</span>
                <span><strong>{step.title}</strong><small>{step.status === "complete" ? "Concluído" : `${step.missing_fields.length} campo(s) pendente(s)`}</small></span>
                <b>{open ? "−" : "+"}</b>
              </button>
              {open && <><p className="sheet-step-summary">{step.summary}</p><StepGuide step={step} /><StepEditor step={step} readOnly={readOnly} onSave={(fields) => saveStep(step.key, fields)} /></>}
            </section>
          );
        })}
      </div>

      {!readOnly && (
        <footer className="sheet-submit-panel">
          <div><strong>{sheet.completion_count === sheet.total_steps ? "Sua ficha está pronta para entrega." : "Ainda existem etapas pendentes."}</strong><small>A entrega não altera automaticamente a nota do vault. O Mestre revisa primeiro.</small></div>
          <button disabled={sheet.completion_count !== sheet.total_steps || sheet.status === "submitted" || sheet.status === "approved"} onClick={() => void submit()}>
            {sheet.status === "submitted" ? "Aguardando Mestre" : sheet.status === "approved" ? "Ficha aprovada" : "Entregar ficha"}
          </button>
          {feedback && <p>{feedback}</p>}
        </footer>
      )}
    </div>
  );
}

export default function CharacterSheetBuilder({ mode }: { mode: "player" | "gm" }) {
  const [sheets, setSheets] = useState<CharacterSheet[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reviewFeedback, setReviewFeedback] = useState("");
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    setLoading(true);
    const request = mode === "gm" ? listGmCharacterSheets() : getPlayerCharacterSheet().then((sheet) => [sheet]);
    request
      .then((items) => {
        setSheets(items);
        setSelectedProfile((current) => current || items[0]?.profile_id || "");
        setError("");
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Não foi possível carregar as fichas."))
      .finally(() => setLoading(false));
  }, [mode]);

  const selected = useMemo(() => sheets.find((sheet) => sheet.profile_id === selectedProfile) || sheets[0] || null, [sheets, selectedProfile]);

  function replaceSheet(updated: CharacterSheet) {
    setSheets((current) => current.map((sheet) => sheet.profile_id === updated.profile_id ? updated : sheet));
  }

  async function review(status: "approved" | "changes_requested") {
    if (!selected) return;
    setReviewing(true);
    setError("");
    try {
      replaceSheet(await reviewCharacterSheet(selected.profile_id, status, reviewFeedback));
      setReviewFeedback("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível revisar a ficha.");
    } finally {
      setReviewing(false);
    }
  }

  if (loading) return <section className="panel"><p className="muted">Preparando fichas...</p></section>;
  if (error && !selected) return <section className="panel"><p className="warning-text">{error}</p></section>;

  return (
    <section className="panel character-sheet-page">
      {mode === "gm" && (
        <div className="gm-sheet-roster">
          <div><p className="eyebrow">Mesa</p><h2>Fichas dos jogadores</h2><p>Acompanhe o que está completo e devolva ajustes antes de consolidar no vault.</p></div>
          <div className="gm-sheet-tabs">
            {sheets.map((sheet) => <button key={sheet.profile_id} className={selected?.profile_id === sheet.profile_id ? "active" : ""} onClick={() => setSelectedProfile(sheet.profile_id)}><strong>{sheet.character_title}</strong><small>{sheet.completion_count}/{sheet.total_steps} · {STATUS_LABELS[sheet.status]}</small></button>)}
          </div>
        </div>
      )}

      {selected && <SheetView sheet={selected} readOnly={mode === "gm"} onChange={replaceSheet} />}

      {mode === "gm" && selected && (
        <div className="gm-sheet-review">
          <label>Retorno para o jogador<textarea value={reviewFeedback} rows={4} placeholder="O que precisa ser corrigido ou confirmado?" onChange={(event) => setReviewFeedback(event.target.value)} /></label>
          <div><button className="secondary-button" disabled={reviewing} onClick={() => void review("changes_requested")}>Solicitar ajustes</button><button disabled={reviewing || selected.completion_count !== selected.total_steps} onClick={() => void review("approved")}>Aprovar ficha</button></div>
        </div>
      )}
      {error && <p className="warning-text">{error}</p>}
    </section>
  );
}
