# tg-media-bot (v1.1)

Telegram bot that downloads YouTube/media (MP3 or MP4) and optionally transcribes via **faster-whisper**.
Includes live progress updates, smaller downloads (<=720p), and Leapcell-safe start command.

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN="YOUR_BOTFATHER_TOKEN"
python -m app.bot
```

## Deploy on Leapcell
- Connect this repo, build the Dockerfile.
- Set env vars:
  - `BOT_TOKEN`: your Telegram bot token
  - `MODEL_SIZE`: `base` (default) or `small`/`medium`
  - `MAX_DURATION_SECS`: `5400` (default)
- No ports needed (long-polling).

## Notes
- Sends media back if <= ~48MB (Telegram friendly).
- Tries YouTube captions first; falls back to Whisper.
- First run downloads model; subsequent runs use cache.
