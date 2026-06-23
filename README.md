# 📞 Escape Call

Sometimes you're stuck in a conversation you can't easily leave — not because it's wrong to leave, but because *"let's continue this later"* is just hard to say out loud. Social anxiety, not wanting to seem rude, or simply no graceful exit.

This gives you an out. Schedule a fake incoming call. Your phone rings, you say *"sorry, I have to take this"*, and you're free.

![Escape Call demo](docs/demo.gif)

## Use it

- **Web** — `python3 server.py` → pick a scenario, phone, delay → tap **Call me**
- **CLI** — `python3 server.py call --to +91… --delay 0 --scenario boss`
- **Embed** — one `<div>` + `<script>` drops a button into any page

Needs a [Twilio](https://twilio.com) account (free trial works). Python stdlib only — no pip installs.

## Quick start

```bash
cp config.example.env .env   # fill in TWILIO_* + ESCAPE_NUMBERS
python3 server.py            # → http://localhost:8500
```

Full setup, API, embed, CLI, and deploy details → **[DEV.md](DEV.md)**

## License

Public domain — [Unlicense](LICENSE).
