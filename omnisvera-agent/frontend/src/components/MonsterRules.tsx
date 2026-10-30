import type { MonsterRulebook } from "../api";

const movementLabels: Record<string, string> = { walk: "Terrestre", fly: "Voo", swim: "Natação", climb: "Escalada", burrow: "Escavação" };
const rechargeLabels: Record<string, string> = { day: "dia", combat: "combate", at_will: "à vontade", every_n_attacks: "sequência de ataques" };
const shapeLabels: Record<string, string> = { cone: "Cone", radius: "Raio", line: "Linha", cloud: "Nuvem", distance: "Alcance" };

export default function MonsterRules({ book }: { book: MonsterRulebook }) {
  return <section className="monster-rulebook" aria-label={`Regras completas de ${book.name}`}>
    <header><strong>REGRAS DA CRIATURA</strong><small>{book.source.edition} · {book.source.license}</small></header>
    <div className="monster-rulebook-movement">{Object.entries(book.movement.modes).map(([mode, meters]) =>
      <span key={mode}>{movementLabels[mode] || mode}: {meters} m</span>)}</div>
    <p><small>{book.art.origin === "missing" ? "Sem imagem vinculada." : book.art.origin === "external_catalog"
      ? `Arte de catálogo externo · ${book.art.attribution || "fonte registrada"}.` : "Arte gerada vinculada ao catálogo."}</small></p>
    {(book.art.catalog_reuse_count || 0) > 1 && <p><small>Imagem compartilhada por {book.art.catalog_reuse_count} entradas do catálogo.</small></p>}
    {book.rules.filter((rule) => rule.category !== "attack").map((rule) => <details key={rule.id} className="monster-rule-card">
      <summary><strong>{rule.name}</strong><small>{rule.execution.status==='native_exposure'?'Contato visual confirmado':rule.execution.status==='native_breath'?'Automática':rule.execution.status==='native_on_hit'?'Automática ao acertar':rule.execution.status==='partial'?'Parcialmente automática':'Resolução assistida'}</small></summary>
      {rule.action_spec && <dl className="monster-rule-parameters">
        {rule.action_spec.damage_formula && <><dt>Dano</dt><dd>{rule.action_spec.damage_formula}{(rule.action_spec.damage_multiplier || 1) > 1 && ` ×${rule.action_spec.damage_multiplier}`}</dd></>}
        {rule.action_spec.save && <><dt>JP</dt><dd>{rule.action_spec.save}{rule.action_spec.save_effect === "halves" ? " · metade" : ""}</dd></>}
        {rule.action_spec.geometry.shape && <><dt>Área</dt><dd>{shapeLabels[rule.action_spec.geometry.shape] || rule.action_spec.geometry.shape}
          {rule.action_spec.geometry.depth_m != null && ` · alcance ${rule.action_spec.geometry.depth_m} m`}
          {rule.action_spec.geometry.width_m != null && ` · largura ${rule.action_spec.geometry.width_m} m`}
          {rule.action_spec.geometry.height_m != null && ` · altura ${rule.action_spec.geometry.height_m} m`}
          {rule.action_spec.geometry.radius_m != null && ` · raio ${rule.action_spec.geometry.radius_m} m`}</dd></>}
        {rule.action_spec.uses.recharge && <><dt>Usos</dt><dd>{rule.action_spec.uses.maximum != null ? `${rule.action_spec.uses.maximum}/` : ""}{rechargeLabels[rule.action_spec.uses.recharge] || rule.action_spec.uses.recharge}</dd></>}
      </dl>}
      <p className="monster-rule-source">{rule.text}</p>
      <ul>{rule.execution.gaps.map((gap) => <li key={gap}><small>{gap}</small></li>)}</ul>
    </details>)}
    <details className="monster-rule-card"><summary>Ficha original e fonte</summary>
      {Object.entries(book.source_record).filter(([, value]) => typeof value === "string" || typeof value === "number").map(([key, value]) =>
        <p key={key}><small><b>{fieldLabel(key)}:</b> {String(value)}</small></p>)}
      {book.source.url && <a href={book.source.url} target="_blank" rel="noreferrer">Consultar fonte das regras</a>}
      <p><small>{book.source.attribution}</small></p>
    </details>
  </section>;
}

function fieldLabel(key: string): string {
  const labels: Record<string, string> = { id: "Identificador", name: "Nome", category: "Categoria", size: "Tamanho", alignment: "Alinhamento", habitat: "Habitat", encounter: "Encontro", experience: "Experiência", experience_points: "XP", treasure: "Tesouro", movement: "Movimento", hit_dice: "Dados de vida", hit_points: "PV", average_hp: "PV médios", armor_class: "CA", saving_throw: "JP", morale: "Moral", source_url: "Fonte", image_path: "Imagem", image_attribution: "Autoria da imagem", image_license: "Licença da imagem", image_license_url: "Licença", image_source_url: "Fonte da imagem" };
  return labels[key] || key;
}
