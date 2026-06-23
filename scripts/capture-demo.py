#!/usr/bin/env python3
"""Record a short usage demo GIF for the README (no real Twilio calls)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo.gif"
BASE = os.environ.get("ESCAPE_CALL_DEMO_URL", "http://localhost:8500")
W, H = 520, 720

DEMO_CONFIG = {
    "scenarios": [
        {"key": "generic", "label": "Generic"},
        {"key": "mom", "label": "Mom"},
        {"key": "boss", "label": "Boss"},
        {"key": "reminder", "label": "Reminder"},
    ],
    "numbers": [
        {"id": "0", "label": "+9199xxxxxx42"},
        {"id": "1", "label": "+1415xxxxxx07"},
    ],
    "configured": True,
}


def snap(page, frames, name):
    n = len(list(frames.glob("*.png")))
    path = frames / f"{n:03d}_{name}.png"
    page.screenshot(path=path, full_page=False)
    return path


def hold(frames, last, repeats=8):
    for _ in range(repeats):
        n = len(list(frames.glob("*.png")))
        dst = frames / f"{n:03d}_hold.png"
        dst.write_bytes(last.read_bytes())


def main():
    frames = Path(tempfile.mkdtemp(prefix="escape-demo-"))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H})
            page.route(
                "**/config",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(DEMO_CONFIG),
                ),
            )
            page.route(
                "**/call",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"ok": true, "delay": 120}',
                ),
            )
            page.goto(BASE, wait_until="networkidle")
            page.wait_for_selector("#callBtn")
            last = snap(page, frames, "loaded")
            hold(frames, last, 10)

            page.select_option("#scenario", "boss")
            last = snap(page, frames, "scenario")
            hold(frames, last, 6)

            page.select_option("#phone", index=1)
            last = snap(page, frames, "phone")
            hold(frames, last, 6)

            page.locator('.chip[data-d="120"]').click()
            last = snap(page, frames, "delay")
            hold(frames, last, 6)

            page.locator("#callBtn").click()
            page.wait_for_selector(".status.ok")
            last = snap(page, frames, "scheduled")
            hold(frames, last, 18)

            browser.close()

        OUT.parent.mkdir(parents=True, exist_ok=True)
        pattern = str(frames / "*.png")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-framerate", "8",
                "-pattern_type", "glob",
                "-i", pattern,
                "-vf", f"scale={W}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                str(OUT),
            ],
            check=True,
            capture_output=True,
        )
        print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    finally:
        for f in frames.glob("*.png"):
            f.unlink()
        frames.rmdir()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"capture failed: {e}", file=sys.stderr)
        sys.exit(1)
