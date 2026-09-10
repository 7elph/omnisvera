"""BTC/USD evidence from closed Coinbase candles. No trading endpoints."""
import json
import math
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE = "https://api.exchange.coinbase.com/products/BTC-USD/candles"


def timestamp(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("UTC offset required")
    return dt.timestamp()


def iso(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def candles(start, end, granularity=3600, requester=None):
    if granularity not in (60, 3600) or not 0 < end - start <= 299 * granularity:
        raise ValueError("invalid candle range")
    url = SOURCE + "?" + urlencode(dict(start=iso(start), end=iso(end), granularity=granularity))
    if requester:
        rows = requester(url)
    else:
        with urlopen(Request(url, headers={"User-Agent": "Omnisvera-Crypto-PoC/1.0"}), timeout=20) as response:
            rows = json.load(response)
    if not isinstance(rows, list):
        raise ValueError("invalid candle response")
    selected = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError("invalid candle row")
        t, close = row[0], row[4]
        if not math.isfinite(float(close)) or float(close) <= 0 or int(t) != t:
            raise ValueError("invalid candle price/time")
        if start <= t < end:
            if t in selected and selected[t] != row:
                raise ValueError("conflicting duplicate candles")
            selected[t] = row
    return [selected[t] for t in sorted(selected)]


def validate_rule(rule, horizon):
    expected = dict(type="price_direction", coin_id="bitcoin", quote="usd",
                    comparison="horizon_price_gt_reference", source=SOURCE,
                    resolver_id="crypto.btc.direction.v1", price_basis="closed_1m_candle")
    if not isinstance(rule, dict) or any(rule.get(k) != v for k, v in expected.items()):
        raise ValueError("BTC rule requires bitcoin/usd, Coinbase source, closed_1m_candle and crypto.btc.direction.v1 resolver")
    reference = float(rule["reference_price"])
    t0, t1 = timestamp(rule["reference_observed_at"]), timestamp(horizon)
    if not math.isfinite(reference) or reference <= 0 or t0 % 60 or t1 % 60 or t1 <= t0:
        raise ValueError("positive price and increasing minute-aligned UTC timestamps required")
    return reference, t0, t1


def canonicalize_minimal(rule, horizon):
    """Enrich minimal semantic rule server-side and canonicalize horizon.

    AI may supply:
      horizon = "PT1H" (intent: 1 hour ahead) OR absolute ISO timestamp
    AI supplies only minimal semantic:
      {type: price_direction, coin_id: bitcoin, quote: usd,
       comparison: horizon_price_gt_reference, resolver_id: crypto.btc.direction.v1}
    Server fills source/price_basis/reference and, if needed, absolute horizon.
    Returns (enriched_rule, canonical_horizon).
    """
    minimal = dict(type="price_direction", coin_id="bitcoin", quote="usd",
                   comparison="horizon_price_gt_reference",
                   resolver_id="crypto.btc.direction.v1")
    if not isinstance(rule, dict):
        raise ValueError("resolution_rule must be object with type price_direction")
    for k, v in minimal.items():
        if rule.get(k) != v:
            raise ValueError(f"crypto minimal requires {k}={v}; got {rule.get(k)!r}. Provide {minimal} and server will enrich source/price_basis/reference")
    # Detect unsupported relative duration early for discoverability
    horizon_str = str(horizon).strip() if horizon is not None else ""
    if horizon_str.startswith("PT") and horizon_str != "PT1H":
        raise ValueError("horizon must be an absolute ISO-8601 timestamp or supported relative duration such as PT1H")
    # fetch trusted reference
    ref = reference_observation()
    enriched = dict(minimal)
    enriched.update(dict(source=SOURCE, price_basis="closed_1m_candle",
                         reference_price=ref["reference_price"],
                         reference_observed_at=ref["reference_observed_at"]))
    # Handle horizon: support absolute ISO or PT1H
    canonical_horizon = horizon_str
    if horizon_str == "PT1H":
        t0 = timestamp(ref["reference_observed_at"])
        canonical_horizon = iso(t0 + 3600)
    # validate
    try:
        validate_rule(enriched, canonical_horizon)
    except Exception as e:
        if horizon_str == "PT1H":
            raise
        if "horizon" in str(e).lower() or "timestamp" in str(e).lower() or "positive price" in str(e).lower():
            raise ValueError(f"{e} — horizon must be absolute ISO-8601 timestamp or PT1H")
        raise
    return enriched, canonical_horizon


def reference_observation(*, now=None, fetch=candles):
    end = int(now or datetime.now(timezone.utc).timestamp()) // 60 * 60 - 60
    rows = fetch(end - 60, end, 60)
    if len(rows) != 1 or rows[0][0] != end - 60:
        raise ValueError("closed reference candle unavailable")
    return dict(type="price_direction", coin_id="bitcoin", quote="usd",
                reference_price=float(rows[0][4]), reference_observed_at=iso(end),
                comparison="horizon_price_gt_reference", source=SOURCE,
                resolver_id="crypto.btc.direction.v1", price_basis="closed_1m_candle")


def resolve_direction(prediction, *, now=None, fetch=candles):
    rule = prediction["resolution_rule"]
    reference, t0, t1 = validate_rule(rule, prediction["horizon"])
    current = timestamp(now) if now else datetime.now(timezone.utc).timestamp()
    if t0 > timestamp(prediction["created_at"]):
        raise ValueError("reference observed after prediction creation")
    if current < t1 + 60:
        return None  # Allow the exchange to finalize the horizon candle.
    def close_at(end):
        rows = fetch(end - 60, end, 60)
        if len(rows) != 1 or rows[0][0] != end - 60:
            return None
        return float(rows[0][4])
    verified_reference, horizon_price = close_at(t0), close_at(t1)
    if verified_reference is None or horizon_price is None:
        return None
    if verified_reference != reference:
        raise ValueError("reference_price does not match source candle")
    evidence = dict(reference_price=reference, horizon_price=horizon_price,
                    reference_observed_at=iso(t0), horizon_observed_at=iso(t1),
                    source=SOURCE, price_basis="closed_1m_candle")
    return dict(outcome=int(horizon_price > reference), evidence=evidence)
