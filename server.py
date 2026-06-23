#!/usr/bin/env python3
"""
Escape Call — a tiny self-hosted "fake call" rescue tool.

Tap a button → after a delay your phone rings and a voice plays a chosen line,
so you can excuse yourself from an awkward/boring situation.

- Backend: Python stdlib only (no Twilio SDK; calls the REST API directly).
- Serves a full UI at /  and a one-button embeddable widget at /embed.js
- Config from environment / a .env file. NEVER commit real credentials.

Required config:
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
Destinations:
  ESCAPE_NUMBERS="+91XXXXXXXXXX,+91XXXXXXXXXX"   # comma-separated E.164 list (in .env only)
Optional:
  ESCAPE_VOICE=Polly.Aditi   PORT=8500   ESCAPE_CALL_ENV=/path/to/.env

Run:  python3 server.py
      python3 server.py call [--to +91…] [--delay 15] [--scenario boss]
      ESCAPE_CALL_ENV=~/.config/agent/secrets.env python3 server.py   # reuse existing creds
"""
import os, sys, json, base64, threading, time, html, argparse
import urllib.request, urllib.parse, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "public")

DEFAULT_SCENARIOS = {
    "generic":  "Hey! Are you free right now? I really need to talk to you, it's kind of important.",
    "mom":      "Where are you? Everyone is waiting at home, please come quickly.",
    "boss":     "Hi, sorry to call after hours — there's an urgent issue, can you join a quick call right now?",
    "reminder": "This is your reminder. You need to leave now for your next appointment.",
}


def load_env():
    cfg = {}
    path = os.environ.get("ESCAPE_CALL_ENV", os.path.join(HERE, ".env"))
    if os.path.exists(path):
        for line in open(path):
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            v = v.strip()
            v = v[1:].split(v[0], 1)[0] if v[:1] in ('"', "'") else v.split("#", 1)[0].strip()
            cfg[k.strip()] = v
    cfg.update(os.environ)  # real environment overrides the file
    return cfg


def scenarios():
    p = os.path.join(HERE, "scenarios.json")
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            pass
    return DEFAULT_SCENARIOS


def mask_number(num):
    s = num.strip()
    plus = s.startswith("+")
    digits = s[1:] if plus else s
    if len(digits) <= 6:
        return s
    return ("+" if plus else "") + digits[:4] + "x" * (len(digits) - 6) + digits[-2:]


def numbers(cfg):
    raw = (cfg.get("ESCAPE_NUMBERS") or "").strip()
    out = []
    for i, part in enumerate(p for p in raw.split(",") if p.strip()):
        part = part.strip()
        if ":" in part:
            _, _, num = part.partition(":")
            num = num.strip()
        else:
            num = part
        out.append({"id": str(i), "label": mask_number(num), "number": num})
    return out


def twilio_configured(cfg):
    return bool(cfg.get("TWILIO_ACCOUNT_SID") and cfg.get("TWILIO_AUTH_TOKEN")
                and cfg.get("TWILIO_FROM_NUMBER"))


def configured(cfg):
    return twilio_configured(cfg) and bool(numbers(cfg))


def resolve_to(cfg, arg=None):
    if arg:
        return arg.strip()
    if cfg.get("ESCAPE_TO"):
        return cfg["ESCAPE_TO"].strip()
    nums = numbers(cfg)
    if nums:
        return nums[0]["number"]
    if not sys.stdin.isatty():
        line = sys.stdin.read().strip()
        if line:
            return line.split(",")[0].strip()
    return None


def scenario_message(key):
    scen = scenarios()
    return scen.get(key) or scen.get("generic") or next(iter(scen.values()))


def place_call(cfg, to, message):
    sid, tok, frm = cfg.get("TWILIO_ACCOUNT_SID"), cfg.get("TWILIO_AUTH_TOKEN"), cfg.get("TWILIO_FROM_NUMBER")
    if not all([sid, tok, frm, to]):
        print("[escape] missing Twilio config", flush=True)
        return False
    voice = cfg.get("ESCAPE_VOICE", "Polly.Aditi")
    safe = html.escape(message)
    twiml = (f'<Response><Pause length="1"/><Say voice="{voice}">{safe}</Say>'
             f'<Pause length="1"/><Say voice="{voice}">{safe}</Say></Response>')
    data = urllib.parse.urlencode({"To": to, "From": frm, "Twiml": twiml}).encode()
    auth = base64.b64encode(f"{sid}:{tok}".encode()).decode()
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json",
        data=data, method="POST",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[escape] call queued to ...{to[-4:]} ({r.status})", flush=True)
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"[escape] call failed ({e.code}): {body}", flush=True)
        return False
    except Exception as e:
        print(f"[escape] call failed: {e}", flush=True)
        return False


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=b"", ctype="text/plain", cors=False):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode(), "application/json", cors=True)

    def _static(self, fname, ctype):
        p = os.path.join(PUBLIC, fname)
        if not os.path.isfile(p):
            return self._send(404, b"not found")
        with open(p, "rb") as f:
            self._send(200, f.read(), ctype, cors=(fname == "embed.js"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._static("index.html", "text/html; charset=utf-8")
        if path == "/style.css":
            return self._static("style.css", "text/css")
        if path == "/embed.js":
            return self._static("embed.js", "application/javascript")
        if path == "/config":
            cfg = load_env()
            scen = scenarios()
            return self._json(200, {
                "scenarios": [{"key": k, "label": k[:1].upper() + k[1:]} for k in scen],
                "numbers": [{"id": n["id"], "label": n["label"]} for n in numbers(cfg)],
                "configured": configured(cfg),
            })
        self._send(404, b"not found")

    def do_POST(self):
        if self.path.split("?")[0] != "/call":
            return self._json(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        cfg = load_env()
        if not configured(cfg):
            return self._json(503, {"error": "Twilio not configured (see README)"})
        scen, nums = scenarios(), numbers(cfg)
        delay = max(0, min(int(body.get("delay", 60)), 21600))   # 0..6h
        msg = scenario_message(body.get("scenario", "generic"))
        pid = str(body.get("phone", nums[0]["id"]))
        to = next((x["number"] for x in nums if x["id"] == pid), nums[0]["number"])
        threading.Timer(delay, place_call, args=(cfg, to, msg)).start()
        return self._json(200, {"ok": True, "delay": delay})


def run_server():
    port = int(load_env().get("PORT", "8500"))
    print(f"Escape Call → http://0.0.0.0:{port}  (configured: {configured(load_env())})")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


def run_cli(argv):
    p = argparse.ArgumentParser(prog="server.py call", description="Schedule an escape call")
    p.add_argument("--to", help="Destination E.164 (else ESCAPE_TO, ESCAPE_NUMBERS, or stdin)")
    p.add_argument("--delay", type=int, default=15, help="Seconds before calling (default 15)")
    p.add_argument("--scenario", default="generic", help="Scenario key (default generic)")
    args = p.parse_args(argv)
    cfg = load_env()
    if not twilio_configured(cfg):
        print("[escape] set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER", file=sys.stderr)
        sys.exit(1)
    to = resolve_to(cfg, args.to)
    if not to:
        print("[escape] no destination — pass --to, set ESCAPE_TO, ESCAPE_NUMBERS, or pipe a number", file=sys.stderr)
        sys.exit(1)
    delay = max(0, min(args.delay, 21600))
    msg = scenario_message(args.scenario)
    if delay:
        print(f"[escape] calling ...{to[-4:]} in {delay}s ({args.scenario})", flush=True)
        time.sleep(delay)
    sys.exit(0 if place_call(cfg, to, msg) else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "call":
        run_cli(sys.argv[2:])
    else:
        run_server()
