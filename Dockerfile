FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Pre-download faster-whisper model into the image (fast cold start)
ENV FW_CACHE=/models FW_CPU_THREADS=4 FW_BEAM_SIZE=1 FW_VAD=0
RUN python - <<'PY'
from faster_whisper import WhisperModel
WhisperModel("base", device="cpu", compute_type="int8", download_root="/models")
print("Model cached.")
PY

COPY app app

# Runtime environment variables
ENV BOT_TOKEN="" MODEL_SIZE=base MAX_DURATION_SECS=5400 MAX_CONCURRENCY=1

# ✅ Run bot and API server concurrently for Leapcell health checks
CMD ["sh", "-c", "python -m app.bot & uvicorn app.health:app --host 0.0.0.0 --port ${PORT:-8080}"]