# AGENTS.md — context for an AI agent working on this repo

## What this is
**Escape Call** — a self-hosted "fake call" rescue tool. A button → after a delay,
Twilio rings the user's phone and a TTS voice plays a chosen line, so they can
excuse themselves from an awkward/boring situation.

## Architecture (no build step, no dependencies)
- **`server.py`** — Python **stdlib only**. Calls the Twilio REST API directly (no SDK).
  Serves: `GET /` (full UI), `GET /config`, `POST /call`, `GET /embed.js`, `GET /style.css`.
  Config from environment or a `.env` file. CORS is open on `/config` & `/call` so the
  widget works cross-origin.
- **`public/index.html`** — the full UI (scenario, destination number, delay presets /
  custom seconds / schedule-at-time).
- **`public/embed.js`** — a one-`<div>` embeddable button for any page.
- **`public/style.css`**, `examples/embed-example.html`.

## Run / test
```bash
cp config.example.env .env      # fill creds, then:
python3 server.py               # http://localhost:8500
# or reuse creds stored elsewhere:
ESCAPE_CALL_ENV=/path/to/secrets.env python3 server.py
```
Config keys: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`,
destinations via `ESCAPE_NUMBERS="Label:+e164,…"` **or** `MY_PHONE_NUMBER[_2/_3]`,
optional `ESCAPE_VOICE` (default `Polly.Aditi`), `PORT` (default 8500).

## API
- `GET /config` → `{ scenarios:[{key,label}], numbers:[{id,label}], configured }`
- `POST /call` `{ delay(sec 0–21600), scenario, phone(id) }` → schedules the call.

## Embed
```html
<div data-escape-call data-base="https://host"></div>
<script src="https://host/embed.js"></script>
```
Optional: `data-delay`, `data-scenario`, `data-phone`, `data-label`.

## Safety / conventions
- Credentials live ONLY in a gitignored `.env`. **Never commit secrets.** The browser
  never sees the auth token — only the server talks to Twilio.
- Twilio **trial** accounts can only call **verified** numbers and prepend a "trial"
  preamble; upgrade to remove both.

---

## Deploying on the owner's Raspberry Pi  (environment-specific — the pending task)

Context: a Raspberry Pi runs a tailnet-only **hub dashboard** at
`http://your-pi.your-tailnet.ts.net` (port 80). Personal apps are served on the Pi
and linked/embedded from that dashboard. Twilio creds already exist in
`~/.config/agent/secrets.env` (`TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM_NUMBER` +
`MY_PHONE_NUMBER`, `MY_PHONE_NUMBER_2`). **Twilio is a trial account.**

Goal: replace the dashboard's *built-in* escape-call with **this standalone repo**,
then delete the in-agent copy.

1. Repo is cloned at `~/escape-call`.
2. **Run as a service** on a free tailnet port (e.g. 8500). Escape Call does **not**
   need HTTPS (no mic/secure-context), so a plain port on the tailnet is enough — no
   `tailscale serve` required. Create a systemd **user** service (pattern matches the
   other agent services) running:
   ```
   ESCAPE_CALL_ENV=~/.config/agent/secrets.env PORT=8500 \
     python3 ~/escape-call/server.py
   ```
   It binds `0.0.0.0:8500` → reachable at `http://your-pi.your-tailnet.ts.net:8500`.
   (Ports already in use: 8443 STFU, 8444 encoder. Pick 8500/8445.)
3. **Dashboard embed:** in `~/hub/html/index.html`, replace the existing
   "Escape Call" card with the one-div embed pointing at the served URL:
   ```html
   <div data-escape-call data-base="http://your-pi.your-tailnet.ts.net:8500"></div>
   <script src="http://your-pi.your-tailnet.ts.net:8500/embed.js"></script>
   ```
   Mirror the change to `agent/docker/hub/html/index.html` and commit (personal-agent
   repo: batch commits, see its memory).
4. **Remove the in-agent integration** (decouple from personal-agent): delete the
   `/api/escape-call` route + the escape helpers (`SCENARIOS`, `place_call`,
   `schedule_call`, `phone_options`) from `~/control-panel/app.py`, plus the
   old escape-call card markup/JS in the dashboard html. Restart `control-panel`.
5. **Verify** with one test call (it will ring the phone).

Debug/screenshot any page: `bash ~/playwright-mcp/shot.sh <url> [out.png]`.
