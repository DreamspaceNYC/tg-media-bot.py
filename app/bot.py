import os, asyncio
from uuid import uuid4
from pathlib import Path
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

from .utils import mkwork, cleanup, bytes_ok
from .media import is_url, dl_url, try_captions
from .transcribe import run_whisper, clean_vtt_to_txt

BOT_TOKEN = os.getenv("BOT_TOKEN")
MODEL_SIZE = os.getenv("MODEL_SIZE", "base")
MAX_DURATION_SECS = int(os.getenv("MAX_DURATION_SECS", "5400"))

SESS = {}

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a YouTube link or upload an audio/video.\nI'll only ask: MP3/MP4 (for URLs) and Transcript?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()
    doc = update.message.document
    vid = update.message.video
    aud = update.message.audio

    ses = SESS[user_id] = {"id": str(uuid4()), "url": None, "file": None, "fmt": None, "want_tx": None}
    if text and is_url(text):
        ses["url"] = text
        kb = [[InlineKeyboardButton("MP3", callback_data=f"{ses['id']}|fmt|mp3"),
               InlineKeyboardButton("MP4", callback_data=f"{ses['id']}|fmt|mp4")]]
        await update.message.reply_text("Download as…", reply_markup=InlineKeyboardMarkup(kb))
        return

    f = doc or vid or aud
    if f:
        tmpdir = mkwork("upload_")
        fpath = tmpdir / f"{uuid4()}_{f.file_name}"
        tgf = await f.get_file()
        await tgf.download_to_drive(str(fpath))
        ses["file"] = str(fpath)
        kb = [[InlineKeyboardButton("Yes", callback_data=f"{ses['id']}|tx|yes"),
               InlineKeyboardButton("No",  callback_data=f"{ses['id']}|tx|no")]]
        await update.message.reply_text("Generate transcript?", reply_markup=InlineKeyboardMarkup(kb))
        return

    await update.message.reply_text("Send a valid URL or upload a media file.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    ses = SESS.get(user_id)
    if not ses:
        await q.edit_message_text("Session expired. Send your file/link again.")
        return

    sid, kind, val = q.data.split("|", 2)
    if sid != ses["id"]:
        await q.edit_message_text("That choice no longer applies.")
        return

    if kind == "fmt":
        ses["fmt"] = val
        kb = [[InlineKeyboardButton("Yes", callback_data=f"{ses['id']}|tx|yes"),
               InlineKeyboardButton("No",  callback_data=f"{ses['id']}|tx|no")]]
        await q.edit_message_text("Generate transcript?", reply_markup=InlineKeyboardMarkup(kb))
        return

    if kind == "tx":
        ses["want_tx"] = (val == "yes")
        await q.edit_message_text("Processing… 0%")
        await process_job(q, ses)

async def edit_step(q, pct, note):
    try:
        await q.edit_message_text(f"Processing… {pct}%\n{note}")
    except Exception:
        pass

async def process_job(q, ses):
    work = mkwork("job_")
    url = ses.get("url")
    local = ses.get("file")
    fmt = ses.get("fmt") or "mp4"
    want_tx = bool(ses.get("want_tx"))
    media_path = None
    txt_path = None

    try:
        await edit_step(q, 10, "Acquiring media…")
        if url:
            media_path = dl_url(url, work, fmt)
        else:
            media_path = local

        await edit_step(q, 40, "Media ready.")
        if want_tx:
            vtt = None
            if url:
                await edit_step(q, 45, "Checking captions…")
                vtt = try_captions(url, work)
            if not vtt:
                loop = asyncio.get_running_loop()
                def cb(p, n):
                    loop.call_soon_threadsafe(asyncio.create_task, edit_step(q, p, n))
                txt_path = run_whisper(media_path, work, MODEL_SIZE, progress_cb=cb)
            else:
                txt_path = str(work / (Path(vtt).stem + ".txt"))
                clean_vtt_to_txt(vtt, txt_path)

        await edit_step(q, 90, "Sending results…")
        if txt_path and Path(txt_path).exists():
            try:
                await q.message.reply_document(document=open(txt_path, "rb"), filename=Path(txt_path).name)
            except Exception:
                await q.message.reply_text("Transcript ready, but sending failed.")
        if media_path and Path(media_path).exists():
            if bytes_ok(media_path, 48):
                try:
                    await q.message.reply_document(document=open(media_path, "rb"), filename=Path(media_path).name)
                except Exception:
                    await q.message.reply_text("Media ready, but sending failed.")
            else:
                await q.message.reply_text("Media processed (too large for Telegram).")
        await edit_step(q, 100, "Done ✅")
    except Exception as e:
        await q.message.reply_text(f"Error: {e}")
    finally:
        cleanup(work)

def main():
    token = BOT_TOKEN
    if not token:
        raise SystemExit("BOT_TOKEN missing.")
    req = HTTPXRequest(connect_timeout=30, read_timeout=60, write_timeout=60, pool_timeout=30)
    app = ApplicationBuilder().token(token).request(req).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
