# OMNISVERA — Claude web connector

Run `.local-tools/start_claude_connector.ps1` once when port 8767 is free.
It launches a dedicated loopback MCP server and Cloudflare quick tunnel;
the existing ChatGPT bridge on 8765 is not changed.

The current public origin is stored in
`.assistant-runtime/claude-connector/config.json`. Append `/mcp`.
Quick tunnel URLs are temporary: recreating the tunnel requires updating the
Claude connector. Both local processes and the computer must remain running.

In Claude web: Settings > Connectors > Add custom connector.
Name: `OMNISVERA`. Remote MCP URL: the HTTPS URL ending in `/mcp`.
Leave advanced OAuth client credentials empty (dynamic public registration).
Connect and authorize on the OMNISVERA login screen using the password in
`.assistant-runtime/claude-connector/login-password.txt`.
Never paste that password into a conversation or commit it.

OAuth uses PKCE S256, short-lived access tokens and rotating refresh tokens.
Runtime credentials are Git-ignored and protected with Windows ACLs.
Default transport identity is `actor=claude.observer`, `client=claude`,
`caller_class=external-ai`. Provider/model identity is not invented.
The remote tool inventory is unchanged, but this principal is read-only:
write tools remain discoverable and policy denies their execution.
To authorize the Crypto experiment, reconnect and explicitly check
the `crypto.btc.direction` consent checkbox on the local OAuth login screen.
The server stores a fixed Crypto profile in the code and tokens; this maps to
`actor=crypto.btc.direction`, `client=claude`. Only `commit_candidate` and
`snapshot_from_model` scoped to `world_id=crypto` receive the Core write scope,
and the existing Core predictor binding rejects other predictors/worlds.
Resolution and other writes remain blocked.
Existing observer tokens remain read-only. Refresh preserves the granted profile.
This setup does not run a handoff or create an operational Prediction.

Validation: run `.omnisvera-tools/Scripts/python.exe -m unittest discover
-s .local-tools/tests -p test_claude_connector.py` and explicitly run
`.local-tools/tests/claude_https_smoke.py` with the same interpreter.
The latter authenticates over HTTPS, performs only reads, checks tool parity,
identity injection denial, domain-table fingerprints and secret leakage.
It does not open Claude or execute a cold handoff.
