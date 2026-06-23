# 📞 Escape Call

A tiny self-hosted "fake call" rescue tool. Tap a button → after a delay your phone
rings and a voice plays a chosen line, so you can say *"sorry, I have to take this"*
and walk out of a boring/awkward situation.

![Escape Call demo](docs/demo.gif)

Two ways to use it:
- **Full UI** — a standalone page (scenarios, multiple numbers, delay presets / custom).
- **One-div embed** — drop a single `<div>` + `embed.js` into any page to get a button.

Backend is **Python stdlib only** (no Twilio SDK) and calls the Twilio REST API directly.

---

## Setup

1. A Twilio account + a Twilio phone number (the caller). Trial works, but trial can
   only call **verified** numbers and plays a "trial" preamble — upgrade to remove both.
2. Configure credentials (never commit them):
   ```bash
   cp config.example.env .env      # then edit .env
   ```
   Required: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`,
   and destinations via `ESCAPE_NUMBERS="+91…,+91…"` (comma-separated E.164 list).
3. Run:
   ```bash
   python3 server.py
   # or reuse existing creds elsewhere:
   ESCAPE_CALL_ENV=~/.config/agent/secrets.env python3 server.py
   ```
   Open http://localhost:8500

> Calls/SMS within India need a domestic setup; a US (+1) Twilio number works but
> forwarding from an Indian mobile bills the forwarded leg at ISD rates.

## Embed it anywhere (one div)
```html
<div data-escape-call data-base="https://your-escape-call-host"></div>
<script src="https://your-escape-call-host/embed.js"></script>
```
Optional attributes: `data-delay` (seconds), `data-scenario`, `data-phone`, `data-label`.
See [`examples/embed-example.html`](examples/embed-example.html).

## Customize the lines
Edit `DEFAULT_SCENARIOS` in `server.py`, or drop a `scenarios.json`
(`{ "key": "what the caller says", … }`) next to it.

## API
- `GET  /config` → `{ scenarios[], numbers[], configured }`
- `POST /call` → `{ delay, scenario, phone }` → schedules the call (delay 0–6h)

## Security
- Credentials live only in `.env` (gitignored) — **never** in the repo or the client.
- The browser never sees your auth token; only the server talks to Twilio.

## License

Public domain — [Unlicense](LICENSE).
