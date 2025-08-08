from fastapi import FastAPI
app = FastAPI()

@app.get("/tgmedia")
async def tgmedia():
    return {"ok": True, "service": "tg-media-bot", "status": "alive"}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/")
async def root():
    return {"ok": True, "hint": "use /tgmedia for Leapcell health"}
