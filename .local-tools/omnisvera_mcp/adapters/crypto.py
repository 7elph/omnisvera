"""Crypto World Adapter v0.1

Real-world crypto data via CoinGecko free API (no key required).
Proves the Universal World Contract works for financial/time-series data.

Hourly observation → prediction → resolution cycle.
All crypto semantics live here. The Core only sees WorldObservation.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from ..world import WorldDescriptor, WorldObservation, WorldSignal, utc_now

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Data Provider — interface for crypto data
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CryptoData:
    """Raw crypto data from any provider."""
    coin_id: str
    symbol: str
    name: str
    price_usd: float
    market_cap_usd: float
    volume_24h_usd: float
    price_change_24h_pct: float | None = None
    last_updated: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class CryptoDataProvider(Protocol):
    """Protocol for crypto data providers."""

    def get_prices(self, coin_ids: list[str]) -> list[CryptoData]:
        """Return current prices for requested coins."""
        ...


# ---------------------------------------------------------------------------
#  CoinGecko Provider — free API, no key required
# ---------------------------------------------------------------------------

class CoinGeckoProvider:
    """Real crypto data provider using CoinGecko free API.

    Rate limits: ~10-30 calls/min without API key.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"
    REQUEST_TIMEOUT = 15  # seconds

    # CoinGecko coin IDs → our normalized IDs
    COIN_MAP = {
        "bitcoin": {"id": "btc", "symbol": "BTC", "name": "Bitcoin"},
        "ethereum": {"id": "eth", "symbol": "ETH", "name": "Ethereum"},
        "solana": {"id": "sol", "symbol": "SOL", "name": "Solana"},
        "binancecoin": {"id": "bnb", "symbol": "BNB", "name": "BNB"},
        "ripple": {"id": "xrp", "symbol": "XRP", "name": "XRP"},
        "cardano": {"id": "ada", "symbol": "ADA", "name": "Cardano"},
        "dogecoin": {"id": "doge", "symbol": "DOGE", "name": "Dogecoin"},
        "polkadot": {"id": "dot", "symbol": "DOT", "name": "Polkadot"},
    }

    def __init__(
        self,
        coin_ids: list[str] | None = None,
        *,
        requester: Any = None,
    ) -> None:
        self._gecko_ids = list(coin_ids or ["bitcoin", "ethereum"])
        self._requester = requester
        self._cache: dict[str, CryptoData] = {}
        self._status = ProviderStatus(state="healthy")

    @property
    def status(self) -> ProviderStatus:
        return self._status

    def _request(self, url: str) -> dict[str, Any]:
        """Make HTTP request. Raises on failure."""
        if self._requester is not None:
            return self._requester(url)
        import urllib.request
        import json as _json
        req = urllib.request.Request(url, headers={"User-Agent": "Omnisvera/1.0"})
        with urllib.request.urlopen(req, timeout=self.REQUEST_TIMEOUT) as resp:
            return _json.loads(resp.read().decode())

    def get_prices(self, coin_ids: list[str] | None = None) -> list[CryptoData]:
        """Fetch current prices from CoinGecko."""
        targets = coin_ids or self._gecko_ids
        ids_param = ",".join(targets)

        try:
            url = (
                f"{self.BASE_URL}/simple/price"
                f"?ids={ids_param}"
                f"&vs_currencies=usd"
                f"&include_24hr_vol=true"
                f"&include_market_cap=true"
                f"&include_24hr_change=true"
            )
            data = self._request(url)

            results: list[CryptoData] = []
            for gecko_id in targets:
                if gecko_id not in data:
                    continue
                coin_data = data[gecko_id]
                meta = self.COIN_MAP.get(gecko_id, {})

                crypto = CryptoData(
                    coin_id=meta.get("id", gecko_id),
                    symbol=meta.get("symbol", gecko_id[:4].upper()),
                    name=meta.get("name", gecko_id.title()),
                    price_usd=coin_data.get("usd", 0.0),
                    market_cap_usd=coin_data.get("usd_market_cap", 0.0),
                    volume_24h_usd=coin_data.get("usd_24h_vol", 0.0),
                    price_change_24h_pct=coin_data.get("usd_24h_change"),
                    last_updated=datetime.now(timezone.utc).isoformat(),
                )
                results.append(crypto)
                self._cache[crypto.coin_id] = crypto

            self._status = ProviderStatus(
                state="healthy",
                last_success=time.time(),
            )
            return results

        except Exception as e:
            logger.warning("CoinGecko fetch failed: %s", e)
            self._status = ProviderStatus(
                state="degraded",
                message=str(e),
                consecutive_failures=self._status.consecutive_failures + 1,
            )
            return list(self._cache.values())


# ---------------------------------------------------------------------------
#  Provider Status
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ProviderStatus:
    """Operational status of a data provider."""
    state: str  # "healthy", "degraded", "offline"
    message: str = ""
    last_success: float | None = None
    consecutive_failures: int = 0


# ---------------------------------------------------------------------------
#  Crypto World Adapter
# ---------------------------------------------------------------------------

class CryptoWorldAdapter:
    """WorldAdapter for crypto market data.

    Proves the Universal World Contract works for:
    - Numeric/financial data
    - High-frequency updates (hourly)
    - Time series with clear resolution

    Prediction cycle: observe → predict price → resolve with actual price.
    """

    WORLD_ID = "crypto"
    WORLD_TYPE = "finance.crypto"
    ADAPTER_ID = "crypto.coingecko.v1"

    def __init__(self, provider: CryptoDataProvider | None = None) -> None:
        self._provider = provider or CoinGeckoProvider()

    def describe(self) -> WorldDescriptor:
        metadata: dict[str, Any] = {"provider": type(self._provider).__name__}
        if isinstance(self._provider, CoinGeckoProvider):
            metadata["provider_state"] = self._provider.status.state
            metadata["coins"] = self._provider._gecko_ids
        return WorldDescriptor(
            world_id=self.WORLD_ID,
            world_type=self.WORLD_TYPE,
            name="Crypto Market",
            adapter_id=self.ADAPTER_ID,
            capabilities=["observe", "history", "model"],
            schemas=["crypto.price.v1"],
            metadata=metadata,
        )

    def health(self) -> dict[str, Any]:
        if isinstance(self._provider, CoinGeckoProvider):
            status = self._provider.status
            return {
                "status": status.state,
                "freshness": "fresh" if status.state == "healthy" else "stale",
                "provider": type(self._provider).__name__,
                "message": status.message,
                "last_success": status.last_success,
                "consecutive_failures": status.consecutive_failures,
            }
        return {"status": "healthy", "freshness": "fresh", "provider": type(self._provider).__name__}

    def observe(self, query: dict[str, Any] | None = None) -> WorldObservation:
        """Observe crypto market state.

        Query options:
          - coin_ids: list of specific coins to observe
        """
        coin_ids = (query or {}).get("coin_ids")
        coins = self._provider.get_prices(coin_ids)

        state = {
            "coins": [c.as_dict() for c in coins],
            "coin_count": len(coins),
        }

        provenance: dict[str, Any] = {
            "adapter": self.ADAPTER_ID,
            "provider": type(self._provider).__name__,
        }
        if isinstance(self._provider, CoinGeckoProvider):
            status = self._provider.status
            provenance["provider_state"] = status.state
            provenance["last_success"] = status.last_success

        return WorldObservation(
            world_id=self.WORLD_ID,
            observed_at=utc_now(),
            schema="crypto.price.v1",
            state=state,
            sources=[{"source_type": "crypto_api", "source_ref": self.ADAPTER_ID}],
            provenance=provenance,
        )

    def signals(self, observation: WorldObservation | None = None) -> list[WorldSignal]:
        """Extract universal signals from crypto state.

        Each coin produces:
        - crypto.price.usd — current price
        - crypto.volume.24h — 24h trading volume
        - crypto.market_cap — market capitalization
        - crypto.price_change.24h_pct — 24h price change percentage
        """
        if observation is None:
            observation = self.observe()

        coins = observation.state.get("coins", [])
        signals: list[WorldSignal] = []
        observed_at = observation.observed_at

        # Global signal
        signals.append(WorldSignal(
            signal_id="crypto.observation.coin_count",
            world_id=self.WORLD_ID,
            schema=observation.schema,
            name="coin_count",
            value=len(coins),
            value_type="number",
            observed_at=observed_at,
            unit="count",
            source={"observation_world_id": observation.world_id, "derivation": "deterministic"},
        ))

        # Per-coin signals
        for coin in coins:
            coin_id = coin.get("coin_id", "unknown")
            entity_ref = f"coin:{coin_id}"

            # Price
            price = coin.get("price_usd", 0.0)
            if price > 0:
                signals.append(WorldSignal(
                    signal_id="crypto.price.usd",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="price_usd",
                    value=price,
                    value_type="number",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    unit="usd",
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                    metadata={"symbol": coin.get("symbol"), "name": coin.get("name")},
                ))

            # Volume 24h
            volume = coin.get("volume_24h_usd", 0.0)
            if volume > 0:
                signals.append(WorldSignal(
                    signal_id="crypto.volume.24h",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="volume_24h",
                    value=volume,
                    value_type="number",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    unit="usd",
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                ))

            # Market cap
            mcap = coin.get("market_cap_usd", 0.0)
            if mcap > 0:
                signals.append(WorldSignal(
                    signal_id="crypto.market_cap",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="market_cap",
                    value=mcap,
                    value_type="number",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    unit="usd",
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                ))

            # 24h price change
            change = coin.get("price_change_24h_pct")
            if change is not None:
                signals.append(WorldSignal(
                    signal_id="crypto.price_change.24h_pct",
                    world_id=self.WORLD_ID,
                    schema=observation.schema,
                    name="price_change_24h",
                    value=change,
                    value_type="number",
                    observed_at=observed_at,
                    entity_ref=entity_ref,
                    unit="percent",
                    source={"observation_world_id": observation.world_id, "derivation": "direct"},
                ))

        return signals
