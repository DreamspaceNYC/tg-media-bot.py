from fastapi import FastAPI
import time
import socket
import platform
import os

app = FastAPI()

# Start time to calculate uptime
start_time = time.time()

@app.get("/tgmedia")
async def tgmedia():
    uptime = round(time.time() - start_time, 2)
    return {
        "ok": True,
        "service": "tg-media-bot",
        "status": "alive",
        "uptime_seconds": uptime,
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "env": {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "port": os.getenv("PORT", "8080"),
        }
    }

@app.get("/healthz")
async def healthz():
    return {
        "ok": True,
        "status": "ready"
    }

@app.get("/")
async def root():
    return {
        "ok": True,
        "hint": "Service is running. Use /tgmedia for full health."
    }

@app.get("/status")
async def status():
    return {
        "app": "tg-media-bot",
        "version": "1.1.2",
        "status": "live",
        "docs": "/docs",
        "health": ["/tgmedia", "/healthz"]
    }