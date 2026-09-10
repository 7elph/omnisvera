# BTC direction PoC

Crypto uses a separate server-side Console profile (`start-crypto.ps1`, loopback
port 8791). Its secret is `.assistant-runtime/omnisvera-mcp/ai-console-crypto-token`.
The Bridge loads this file at startup and maps it to `crypto.btc.direction`.
The original token/profile remains `football.elo`; wrong tokens retain the
existing MIA fallback. No actor can be supplied through tool arguments.

The seed command is `seed_crypto_btc.py --db <memory.db> --artifacts <directory>`.
It fetches 240 consecutive closed hourly Coinbase BTC-USD candles, counts 239
directions, stores the dataset hash/path/source and returns the existing seed on
retry. No prediction or AI call is made. Equal closes count as down.

Discover the reference query with `world.describe("crypto")`. Use
`world.observe(world_id="crypto", query={"coin_ids":["bitcoin"],"btc_direction":true})`
and copy `state.btc_direction_reference` into `resolution_rule`.
The horizon must include UTC offset and be minute-aligned, about one hour ahead.
The price means the close of the Coinbase one-minute candle ending at that time.
The reference candle is already closed; the resolver re-fetches both reference
and horizon candles. Missing evidence waits; mismatched reference fails.

The existing DB observed_value column is numeric: it stores horizon_price.
The same resolution row's notes stores structured JSON with both prices,
timestamps, source and price basis; sources_json carries the source URL.
No schema migration is needed.

Only the dedicated BTC resolver runs for `crypto.btc.direction.v1`. It calls
the existing atomic resolution method, then the existing Experience runtime.
Dry run fetches/checks evidence but writes nothing. Runtime v2 tests use temporary
databases; production remains v1 until a separately authorized real handoff.

Source contract: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
