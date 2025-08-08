import os, re
from pathlib import Path
from .media import ffprobe_duration
from faster_whisper import WhisperModel

def pick_model_by_duration(seconds: int, default_size="base"):
    if seconds < 60: return "tiny"
    if seconds < 1800: return "small"
    if seconds < 3600: return "base"
    return default_size

def run_whisper(media_path: str, workdir: Path, model_size: str|None=None, progress_cb=None) -> str:
    dur = max(ffprobe_duration(media_path), 1)
    size = model_size or pick_model_by_duration(dur)
    model = WhisperModel(size, device="cpu", compute_type="int8", num_workers=os.cpu_count() or 2)

    start_pct, end_pct = 55, 95
    last = -1
    segments, _ = model.transcribe(media_path, vad_filter=True)
    txt_path = workdir / (Path(media_path).stem + ".txt")
    done_sec = 0.0

    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            line = seg.text.strip()
            if line:
                f.write(line + "\n")
            done_sec = max(done_sec, float(seg.end or 0))
            pct = start_pct + int((min(done_sec, dur) / dur) * (end_pct - start_pct))
            if progress_cb and pct > last:
                last = pct
                try: progress_cb(pct, f"Transcribing… {pct}%")
                except Exception: pass

    if progress_cb:
        try: progress_cb(95, "Cleaning transcript…")
        except Exception: pass

    return str(txt_path)

def clean_vtt_to_txt(vtt_path: str, out_path: str):
    lines = []
    with open(vtt_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s == "WEBVTT" or "-->" in s or s.isdigit():
                continue
            s = re.sub(r"<[^>]+>", "", s)
            if s: lines.append(s)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path
