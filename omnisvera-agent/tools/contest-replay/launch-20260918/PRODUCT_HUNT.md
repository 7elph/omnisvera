# OMNISVERA — launch package

## Name
OMNISVERA

## Tagline
Keep AI experience when you change models

## Website
https://omnisvera-continuity.deliberalithiaguin.chatgpt.site

Public access enabled with explicit user approval on 2026-09-18.

## Description
OMNISVERA preserves experience outside the AI model. Watch an audited replay of a fresh GPT-6 Astra session recovering persisted state and continuing through a validated, governed commit—without receiving the previous state in its prompt.

## First maker comment
Hi Product Hunt! I built Omnisvera around a frustration: when I start a new AI session or change models, I don't want to explain my project all over again.

This launch is a developer proof of concept, not a finished universal memory service. Omnisvera keeps versioned experience, evidence and provenance outside the model, and exposes them through MCP.

For this experiment, a fresh GPT-6 Astra session received just one instruction: continue the work using the experience persisted in Omnisvera and discover what it needs through the system. No World, predictor, Experience ID, version, hash or snapshot was supplied in the prompt.

The first run recovered the experience but stopped without issuing a prediction when the evidence was insufficient. In the later run, with evidence available and legitimate read scopes corrected, Astra recovered the experience, created a candidate, validated it and committed Prediction #17 to a test database.

You can play the audited replay and inspect the tool sequence, hashes, timestamps and limitations. It is explicitly NOT LIVE. The market data is real Coinbase data held in a fixed fixture; this is not a trading product or a claim of predictive accuracy. The previous model's identity is not established, and full OS isolation was not demonstrated.

What I want to explore next is practical continuity: what should survive when you change the AI you work with?

If you build agents or long-running AI workflows, where do you currently lose the most context? I'd love concrete examples and criticism.

## Topics to select if available
Developer Tools; Artificial Intelligence; Productivity.

## Product status
Developer proof of concept / experimental demo. Do not represent as a generally available hosted backend.

## Gallery order
1. gallery-01.png — the continuity proposition.
2. gallery-02.png — the two observed outcomes.
3. gallery-03.png — inspect the evidence and limitations.

## Video
demo.mp4 is an editorial, captioned presentation of the audited experiment, not a live run. Upload as public or unlisted to the owner's YouTube account only if authorized access is available; Product Hunt accepts a full YouTube URL. Video is optional: do not delay the launch if upload is blocked.

## Short sharing text
I built OMNISVERA to explore a simple question: why should changing AI models mean starting over?

A fresh Astra session recovered persisted experience and continued through a governed commit, without receiving the previous state in its prompt.

The demo is an audited replay, not a live run. Explore the evidence and tell me what you'd want your next AI to inherit.

## Boundaries
No claim of Claude-to-Astra identity proof, universal model compatibility, live market operation, guaranteed financial returns, independent cryptographic attestation or complete OS isolation. Do not upload raw traces, operational databases, credentials or the private forensic archive.
