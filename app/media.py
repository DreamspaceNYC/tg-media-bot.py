import subprocess, re
from pathlib import Path

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)

def is_url(s: str) -> bool:
    return bool(re.match(r'^https?://', s))

def ffprobe_duration(path: str) -> int:
    try:
        out = run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nokey=1:noprint_wrappers=1", path]).stdout
        return int(float(out.strip()))
    except Exception:
        return 0

def dl_url(url: str, outdir: Path, fmt: str) -> str:
    if fmt == "mp3":
        run([
            "yt-dlp","-f","bestaudio",
            "--extract-audio","--audio-format","mp3",
            "--no-playlist","-o", f"{outdir}/%(title)s.%(ext)s", url
        ])
    else:
        # Prefer native MP4; otherwise remux best to MP4 container (no re-encode)
        run([
            "yt-dlp",
            "-f", "bv*[ext=mp4][height<=720]+ba[ext=m4a]/b[ext=mp4]/best[ext=mp4]/best",
            "--merge-output-format","mp4",
            "--remux-video","mp4",
            "--no-playlist",
            "-o", f"{outdir}/%(title)s.%(ext)s", url
        ])
    files = sorted(outdir.iterdir(), key=lambda p: p.stat().st_mtime)
    return str(files[-1]) if files else ""

def try_captions(url: str, outdir: Path) -> str|None:
    try:
        run([
            "yt-dlp","--skip-download","--write-auto-subs","--write-subs",
            "--sub-langs","en.*","--sub-format","vtt",
            "-o", f"{outdir}/%(title)s.%(ext)s", url
        ])
        vtts = list(outdir.glob("*.vtt"))
        return str(vtts[0]) if vtts else None
    except Exception:
        return None
