# pw-sdk

The PlaceholderWorks SDK. It is the one package a client installs: it holds the core (standard records, adapter contract, shared contracts and helpers), and brings in the brain, the tools and the channels as extras.

```toml
dependencies = ["pw-sdk[llm,tools,channel]"]
```

## How it fits together

```
            CLIENT'S SERVER (everything runs here)
 ┌───────────────────────────────────────────────────────────────┐
 │  <client>-adapter repo  (client-owned)                         │
 │    adapter.py   client webhook  ──►  CustomerRecord            │
 │    pw.toml      providers, branding, intakes, journeys         │
 │    .env         all keys and secrets                           │
 │                        │ depends on                            │
 │                        ▼                                       │
 │  pw-sdk  (core)                                                │
 │    models · Adapter · contracts · registry · config · utils    │
 │    ├── [llm]      pw-llm      brain: chat, voice turns, studio  │
 │    ├── [tools]    pw-tools    agent tools                       │
 │    └── [channel]  pw-channel  intake, journey scheduler,        │
 │                               channels/voice · whatsapp · email │
 └───────────────────────────────────────────────────────────────┘
```

### One record, end to end

1. The client's site posts its own JSON to `POST /api/intake/<intake>/records`.
2. The client's adapter turns it into a `CustomerRecord` (customer, journey stage, cart items, resume link, facts).
3. pw-channel validates and stores it (raw and canonical together), then starts the journey named in `pw.toml`.
4. The worker runs each step when it is due and its dependencies are met: WhatsApp, then a call, then email, and so on. Before each step it checks contact hours, consent, opt-outs, DND and daily limits.
5. Calls go through the telephony provider; each turn asks pw-llm, which uses pw-tools (cart details, discount, resume link, transfer, end call).
6. Outcomes and events come back: call answered or missed, WhatsApp reply, link click, opt-out, and the client's own `payment.succeeded` / `booking.confirmed` on `POST /api/intake/<intake>/events`. Rules in `pw.toml` decide what happens next: complete, stop, cancel a step, pause, reschedule, or start another journey.

All journey state is in Postgres, so several workers can run and nothing is lost on restart.

## What is in the core

| Module | What it holds |
|---|---|
| `pw_sdk.models` | `CustomerRecord` v1 and `OutcomeEvent` v1: the only formats the platform reads |
| `pw_sdk.adapter` | `Adapter` base class, `map_batch`, `SkipItem`, `RejectItem` |
| `pw_sdk.contracts` | `RuntimeContext` (what voice, brain and tools share during a call), voice actions, task outcomes |
| `pw_sdk.registry` | `ProviderRegistry`: every provider family is registered by name |
| `pw_sdk.config` | loads the client's `pw.toml` and `.env` |
| `pw_sdk.utils` | phone (E.164), auth, time and contact hours, HTTP with retries |
| `pw_sdk.testkit` | `pw-adapter check`, `pw-adapter schema`, `pw-adapter new` |

## Setup

Run these in the client's adapter repo:

```bash
cp .env.example .env              # keys: database, LLM, STT/TTS, telephony, WhatsApp, SMTP
uv sync
uv run pw-adapter check fixtures/ # the adapter maps sample payloads correctly
uv run <client> check             # pw.toml, adapters and journeys are valid
uv run <client> migrate           # database tables and intakes
uv run <client> llm               # brain on :8010
uv run <client> channel           # intake, webhooks, voice, dashboard on :8420
uv run <client> worker            # journey scheduler
```

Postgres is required. Redis is needed only for WhatsApp sessions.

## Current client: Adam Vacations

`adam-vacations-adapter` maps Adam's cart webhook (customer, lines, cart value, payment status, deep link) and Adam's payment and booking events. Its `pw.toml` runs:

1. WhatsApp resume link 5 minutes after the cart is abandoned.
2. No reply in 30 minutes: a call, retried once.
3. No answer: an email 2 hours later.

A booking or payment stops the journey, a failed payment starts a payment-retry journey, and a reply, click or opt-out changes the plan as configured. The adapter currently runs on dummy payloads until Adam shares real samples.

## A new client

```bash
uv run pw-adapter new acme_travel   # creates acme-travel-adapter/
```

Then:

1. Describe their webhook in `payload.py`.
2. Map it in `adapter.py`.
3. Add sample payloads under `fixtures/`.
4. Set providers, copy and journeys in `pw.toml`.

The core does not change. Client code is named after the client (`acme_travel`, `AcmeTravelCartAdapter`); everything in the platform stays generic.

## Channels and providers

| Add | Where (in pw-channel) | Base class |
|---|---|---|
| a channel (e.g. SMS) | `pw_channel/channels/<name>/channel.py` | `Channel` |
| a telephony provider | `channels/voice/telephony/<name>/` | `TelephonyProvider` |
| an STT / TTS / VAD provider | `channels/voice/stt|tts|vad/<name>.py` | `STTProvider` / `TTSProvider` / `VADProvider` |
| a WhatsApp provider | `channels/whatsapp/providers/<name>.py` | `WhatsAppProvider` |
| an email provider | `channels/email/providers/<name>.py` | `EmailProvider` |
| an LLM provider | `pw_llm/providers/<name>.py` (pw-llm) | `LLMProvider` |
| an agent tool | `pw_tools/...` (pw-tools) | `BaseTool` |

Each is one file plus one registry line, or an entry point in the client's adapter repo. A client picks providers by name in `pw.toml`.

## Releases

- **Local development:** path sources.
- **Release:** git tags; the adapter repo carries `release-sources.toml`.
- **Later:** compiled wheels for pw-llm, pw-tools and pw-channel from a private index. Only the sources change, never the dependency names.
