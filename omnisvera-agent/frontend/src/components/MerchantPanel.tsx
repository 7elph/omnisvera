import { useEffect, useState } from "react";
import {
  addMerchantStock, buyFromMerchant, createMerchant, getPlayableCharacter, haggleMerchant, listCompendiumItems,
  listMerchants, removeMerchantStock, sellToMerchant,
  type CompendiumItemsResponse, type Merchant, type PlayableCharacter, type PlayableCharacterSummary,
} from "../api";

function purseOf(character: PlayableCharacter | null): Record<string, number> | null {
  if (!character?.state) return null;
  return {
    copper_coins: character.state.copper_coins || 0, silver_coins: character.state.silver_coins || 0,
    coins: character.state.coins || 0, platinum_coins: character.state.platinum_coins || 0,
  };
}

function purseText(purse: Record<string, number> | null): string {
  if (!purse) return "—";
  return `${purse.platinum_coins} PL · ${purse.coins} PO · ${purse.silver_coins} PP · ${purse.copper_coins} PC`;
}

export default function MerchantPanel({ characters }: { characters: PlayableCharacterSummary[] }) {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [items, setItems] = useState<CompendiumItemsResponse | null>(null);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [merchantId, setMerchantId] = useState("");
  const [stockItem, setStockItem] = useState("");
  const [stockQty, setStockQty] = useState("1");
  const [stockPrice, setStockPrice] = useState("");
  const [buyer, setBuyer] = useState("");
  const [buyerSheet, setBuyerSheet] = useState<PlayableCharacter | null>(null);
  const [stockId, setStockId] = useState("");
  const [qty, setQty] = useState("1");
  const [price, setPrice] = useState("");
  const [d20, setD20] = useState("");
  const [haggleInfo, setHaggleInfo] = useState("");
  const [sellItem, setSellItem] = useState("");
  const [sellPrice, setSellPrice] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const refresh = () => {
    void listMerchants().then(setMerchants).catch((reason) => setError(reason instanceof Error ? reason.message : "Falha"));
  };
  useEffect(() => {
    refresh();
    void listCompendiumItems().then(setItems).catch(() => {});
  }, []);
  useEffect(() => {
    setBuyerSheet(null);
    if (!buyer) return;
    void getPlayableCharacter(buyer).then(setBuyerSheet).catch(() => {});
  }, [buyer, merchants]);

  const merchant = merchants.find((entry) => entry.id === merchantId) || null;
  const line = merchant?.stock.find((entry) => entry.id === stockId) || null;
  const basePrice = (line?.price_po || 0) * Number(qty || 1);

  async function run<T>(task: () => Promise<T>, done: (result: T) => void) {
    setError(""); setStatus("");
    try { done(await task()); refresh(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha"); }
  }

  function doHaggle() {
    if (!merchant || !buyer || !line) return;
    const physical = d20.trim() !== "";
    void run(() => haggleMerchant(merchant.id, {
      character_id: buyer, base_price_po: basePrice || 0, roll_mode: physical ? "physical" : "digital",
      d20: physical ? Number(d20) : undefined,
    }), (result) => {
      setPrice(String(result.adjusted_price_po));
      setHaggleInfo(`1d20 ${result.d20}+${result.modifier}=${result.total} → ${result.tier} = ${result.adjusted_price_po} PO`);
    });
  }

  function doBuy() {
    if (!merchant || !buyer || !line || !price.trim()) return;
    void run(() => buyFromMerchant(merchant.id, {
      character_id: buyer, stock_id: line.id, quantity: Number(qty) || 1,
      final_price_po: Number(price), expected_purse: purseOf(buyerSheet),
    }), (result) => setStatus(`Vendido: ${result.quantity}× ${result.item} por ${result.paid_po} PO.`));
  }

  function doSell() {
    if (!merchant || !buyer || !sellItem || !sellPrice.trim()) return;
    void run(() => sellToMerchant(merchant.id, {
      character_id: buyer, item_path: sellItem, quantity: Number(qty) || 1,
      unit_price_po: Number(sellPrice), expected_purse: purseOf(buyerSheet),
    }), (result) => {
      setSellItem(""); setSellPrice("");
      setStatus(`Comprado do grupo: ${result.quantity}× ${result.item} por ${result.received_po} PO.`);
    });
  }

  return (
    <section className="workspace-monster-catalog">
      <header><strong>MERCADORES</strong><small>{merchants.length} na mesa · preços do compêndio · pechincha no Carisma</small></header>
      {error && <small>{error}</small>}
      {status && <small>{status}</small>}
      <div>
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Nome do mercador" />
        <input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Local (opcional)" />
        <button type="button" disabled={!name.trim()} onClick={() => void run(() => createMerchant({ name: name.trim(), location: location.trim() }), () => { setName(""); setLocation(""); setStatus("Mercador aberto."); })}>Abrir mercador</button>
      </div>
      <select aria-label="Mercador" value={merchantId} onChange={(event) => { setMerchantId(event.target.value); setStockId(""); }}>
        <option value="">Selecione um mercador…</option>
        {merchants.map((entry) => <option key={entry.id} value={entry.id}>{entry.name}{entry.location ? ` · ${entry.location}` : ""}</option>)}
      </select>
      {merchant && <>
        <div>
          <select aria-label="Item do compêndio" value={stockItem} onChange={(event) => setStockItem(event.target.value)}>
            <option value="">Por no estoque… ({items?.total || "…"})</option>
            {(items?.items || []).filter((entry) => entry.preco_po != null && entry.catalog_entry_kind !== 'reference').map((entry) => <option key={entry.id} value={entry.id}>{entry.name} · {entry.preco}</option>)}
          </select>
          <input value={stockQty} onChange={(event) => setStockQty(event.target.value)} placeholder="qtd (-1 inf.)" />
          <input value={stockPrice} onChange={(event) => setStockPrice(event.target.value)} placeholder="preço do Mestre (PO, opcional)" />
          <button type="button" disabled={!stockItem} onClick={() => void run(() => addMerchantStock(merchant.id, {
            compendium_item_id: stockItem, quantity: Number(stockQty) || 1,
            price_override_po: stockPrice.trim() ? Number(stockPrice) : null,
          }), () => { setStockItem(""); setStockQty("1"); setStockPrice(""); })}>Estocar</button>
        </div>
        {merchant.stock.map((entry) => <p key={entry.id}><small>
          <b>{entry.name}</b> · {entry.quantity === -1 ? "∞" : `${entry.quantity}×`} · {entry.price_po != null ? `${entry.price_po} PO` : "sem preço"}
          {entry.price_override_po != null && " (Mestre)"} <button type="button" onClick={() => void run(() => removeMerchantStock(merchant.id, entry.id), () => {})}>tirar</button>
        </small></p>)}
        <div>
          <select aria-label="Comprador" value={buyer} onChange={(event) => setBuyer(event.target.value)}>
            <option value="">Quem compra/vende…</option>
            {characters.map((character) => <option key={character.id} value={character.id}>{character.name}</option>)}
          </select>
          {buyerSheet && <small>Bolsa: {purseText(purseOf(buyerSheet))}</small>}
        </div>
        <div>
          <select aria-label="Item do estoque" value={stockId} onChange={(event) => { setStockId(event.target.value); setHaggleInfo(""); }}>
            <option value="">Comprar…</option>
            {merchant.stock.filter((entry) => entry.price_po != null).map((entry) => <option key={entry.id} value={entry.id}>{entry.name} · {entry.price_po} PO</option>)}
          </select>
          <input value={qty} onChange={(event) => setQty(event.target.value)} placeholder="qtd" />
          <input value={price} onChange={(event) => setPrice(event.target.value)} placeholder={`preço final (${basePrice || "—"} PO base)`} />
          <input value={d20} onChange={(event) => setD20(event.target.value)} placeholder="d20 físico (opcional)" />
          <button type="button" disabled={!buyer || !line} onClick={doHaggle}>Pechinchar</button>
          <button type="button" disabled={!buyer || !line || !price.trim()} onClick={doBuy}>Confirmar compra</button>
          {haggleInfo && <small>{haggleInfo}</small>}
        </div>
        <div>
          <select aria-label="Item do personagem" value={sellItem} onChange={(event) => setSellItem(event.target.value)}>
            <option value="">Vender…</option>
            {(buyerSheet?.inventory || []).filter((entry) => entry.quantity > 0).map((entry) => <option key={entry.item_path} value={entry.item_path}>{entry.quantity}× {entry.item_title}</option>)}
          </select>
          <input value={sellPrice} onChange={(event) => setSellPrice(event.target.value)} placeholder="preço unitário (PO)" />
          <button type="button" disabled={!buyer || !sellItem || !sellPrice.trim()} onClick={doSell}>Confirmar venda</button>
        </div>
      </>}
      <small>Compra baixa a bolsa (cobre/prata/ouro/platina com troco automático) e entrega o item; venda paga em ouro. Saldo com guarda anti-concorrência. Sem preço no livro → o Mestre precifica no estoque.</small>
    </section>
  );
}
