# DEV.md — development & integration reference

## Architecture

No build step, no pip installs — Python stdlib only.

| Path | Role |
|------|------|
| `server.py` | HTTP server + Twilio REST calls + CLI (`server.py call`) |
| `public/index.html` | Full web UI |
| `public/embed.js` | One-`<div>` embeddable button widget |
| `public/style.css` | Shared styles |
| `examples/embed-example.html` | Minimal embed usage sample |
| `scripts/capture-demo.py` | Regenerate `docs/demo.gif` |
| `config.example.env` | Template — copy to `.env`, never commit |

Served routes: `GET /` · `GET /config` · `POST /call` · `GET /embed.js` · `GET /style.css`.
CORS is open on `/config` and `/call` so the embed widget works cross-origin.

## Configuration

Copy `config.example.env` → `.env`. Env vars override the file.

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | yes | — | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | yes | — | Twilio auth token |
| `TWILIO_FROM_NUMBER` | yes | — | Your Twilio caller number (E.164) |
| `ESCAPE_NUMBERS` | web UI | — | Comma-separated destination numbers (E.164). Shown masked in UI (`+9188xxxxxx88`). Also supports `Label:+number` format. |
| `ESCAPE_TO` | no | — | CLI default destination (overridden by `--to`) |
| `ESCAPE_VOICE` | no | `Polly.Aditi` | Twilio `<Say>` voice |
| `PORT` | no | `8500` | HTTP port |
| `ESCAPE_CALL_ENV` | no | `.env` | Alternate path to secrets file |

Reuse credentials stored elsewhere:
```bash
ESCAPE_CALL_ENV=~/.config/agent/secrets.env python3 server.py
```

## CLI

```
python3 server.py call [--to E.164] [--delay SECONDS] [--scenario KEY]
```

| Flag | Default | Notes |
|------|---------|-------|
| `--to` | — | E.164 destination |
| `--delay` | `15` | 0–21600 seconds |
| `--scenario` | `generic` | See scenario keys below |

Destination resolution: `--to` → `ESCAPE_TO` env → first `ESCAPE_NUMBERS` entry → stdin line.

Examples:
```bash
python3 server.py call --to +91XXXXXXXXXX --delay 0
ESCAPE_TO=+91XXXXXXXXXX python3 server.py call --scenario mom
echo +91XXXXXXXXXX | python3 server.py call --delay 30
```

Exit code `0` on success, `1` on Twilio failure. Logs `[escape] call queued` or `[escape] call failed (code): …`.

## HTTP API

### `GET /config`
```json
{
  "scenarios": [{"key": "generic", "label": "Generic"}],
  "numbers":   [{"id": "0", "label": "+9188xxxxxx88"}],
  "configured": true
}
```

### `POST /call`
Request:
```json
{ "delay": 15, "scenario": "boss", "phone": "0" }
```
Response `200`: `{ "ok": true, "delay": 15 }`
Response `503`: `{ "error": "Twilio not configured (see README)" }`

- `delay` — seconds 0–21600
- `scenario` — key from `/config` scenarios list
- `phone` — `id` from `/config` numbers list (defaults to first)

## Embed widget

```html
<div data-escape-call data-base="https://your-host"></div>
<script src="https://your-host/embed.js"></script>
```

Optional `data-*` attributes:

| Attribute | Default | Description |
|-----------|---------|-------------|
| `data-base` | script origin | Backend URL |
| `data-delay` | `60` | Seconds before calling |
| `data-scenario` | `generic` | Scenario key |
| `data-phone` | first | Destination id |
| `data-label` | `📞 Escape Call` | Button text |

See [`examples/embed-example.html`](examples/embed-example.html).

## Scenarios

Built-in keys: `generic` · `mom` · `boss` · `reminder`.

Override or extend by creating `scenarios.json` next to `server.py`:
```json
{
  "generic":  "Hey, are you free right now?",
  "partner":  "Hey, where are you? I need you home.",
  "urgent":   "There's been an incident — can you step out?"
}
```
The file takes full precedence over built-in defaults when present.

## Demo GIF

`docs/demo.gif` is tracked via Git LFS. The capture script mocks `/config` and `/call` (no real Twilio calls, no real numbers in the recording).

```bash
python3 server.py                    # separate terminal
python3 scripts/capture-demo.py     # writes docs/demo.gif
```

Requires: `pip install playwright && python3 -m playwright install chromium` + `ffmpeg`.

## Security

- Credentials live only in `.env` or exported env vars — never in the repo or served to the browser.
- `/config` returns masked number labels only (`+9188xxxxxx88`), not full numbers.
- Auth token is used server-side only; the browser never sees it.

## Twilio notes

- **Trial accounts**: can only call verified numbers and prepend a recorded trial message. Upgrade to remove both.
- A US (+1) Twilio number calling Indian mobiles works, but the forwarded leg is billed at ISD rates.
- Voices: `Polly.Aditi` (Indian English, default), `Polly.Kajal-Neural` (better quality), `Polly.Joanna` (US English), `Google.en-IN-Neural2-A` (Indian English, Google). Full list at [Twilio TTS docs](https://www.twilio.com/docs/voice/twiml/say/text-speech).

## Deploying on a Raspberry Pi

1. Clone the repo, e.g. to `~/escape-call`.
2. Run it as a systemd user service (a plain tailnet port is fine, no HTTPS needed):
   ```
   ESCAPE_CALL_ENV=~/.config/agent/secrets.env PORT=8500 \
     python3 ~/escape-call/server.py
   ```
   It's then reachable at `http://<your-pi>.<your-tailnet>.ts.net:8500` from your tailnet.
3. Optional: embed the button in a dashboard page:
   ```html
   <div data-escape-call data-base="http://<your-pi>.<your-tailnet>.ts.net:8500"></div>
   <script src="http://<your-pi>.<your-tailnet>.ts.net:8500/embed.js"></script>
   ```
4. Verify with one test call.
