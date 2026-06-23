# AGENTS.md — quick ops for this repo

## What this is
Self-hosted fake-call rescue. After a delay, Twilio rings a chosen number and plays a TTS line so the user can exit an awkward situation.

## End-to-end usage

**1. Configure** — gitignored `.env` or exported env vars (never commit):
```bash
cp config.example.env .env
```
Required for web UI: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `ESCAPE_NUMBERS="+91…,+1…"`.
CLI only needs the three Twilio vars + a destination (`--to`, `ESCAPE_TO`, or stdin).
Optional: `ESCAPE_VOICE` (default `Polly.Aditi`), `PORT` (default `8500`), `ESCAPE_CALL_ENV`.

**2. Web UI**
```bash
python3 server.py              # → http://localhost:8500
```
Select scenario, phone (shown masked), delay (Now / 15s / 2m / 5m / Custom), tap **Call me**.

**3. CLI** (no server needed — fires a call directly)
```bash
python3 server.py call --to +91XXXXXXXXXX --delay 0 --scenario boss
# destination fallback: --to → ESCAPE_TO → first ESCAPE_NUMBERS → stdin
echo +91XXXXXXXXXX | python3 server.py call
```
Exit `0` on success, `1` on Twilio error.

**4. Embed** (one div on any page)
```html
<div data-escape-call data-base="https://host"></div>
<script src="https://host/embed.js"></script>
```

## Scenarios
Built-in keys: `generic`, `mom`, `boss`, `reminder`.
Override with a `scenarios.json` next to `server.py`: `{ "key": "message text", … }`.

## Rules
- **Never commit secrets.** Browser never sees Twilio auth token.
- Twilio **trial**: verified numbers only + recorded trial preamble.

## More detail
Architecture, full config table, API, CLI options, embed attrs, deploy → **[DEV.md](DEV.md)**
