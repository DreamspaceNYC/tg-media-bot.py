import os, subprocess, re
from pathlib import Path

def ffmpeg_bin() -> str:
    p = os.getenv("FFMPEG_BIN")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG = ffmpeg_bin()

def run(cmd, **kw):
    # Run a command, capturing combined stdout/stderr
    return subprocess.run(
        cmd, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw
    )

def is_url(s: str) -> bool:
    return bool(re.match(r'^https?://', s))

def ffprobe_duration(path: str) -> int:
    """Get duration in seconds using ffmpeg -i output (no ffprobe needed)."""
    try:
        out = subprocess.run([FFMPEG, "-i", path],
                             text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT).stdout
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", out)
        if m:
            h, m_, s = m.groups()
            return int(h) * 3600 + int(m_) * 60 + int(float(s))
    except Exception:
        pass
    return 0

def dl_url(url: str, outdir: Path, fmt: str) -> str:
    """Download URL to outdir. fmt in {'mp3','mp4'}."""
    base = [
        "yt-dlp",
        "--no-playlist",
        "--ffmpeg-location", FFMPEG,
        "-o", f"{outdir}/%(title)s.%(ext)s",
    ]
    if fmt == "mp3":
        cmd = base + [
            "-f", "bestaudio",
            "--extract-audio", "--audio-format", "mp3",
        ]
    else:
        # Prefer native MP4; otherwise remux any best to MP4 (no re-encode)
        cmd = base + [
            "-f", "bv*[ext=mp4][height<=720]+ba[ext=m4a]/b[ext=mp4]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--remux-video", "mp4",
        ]
    run(cmd + [url])
    files = sorted(outdir.iterdir(), key=lambda p: p.stat().st_mtime)
    return str(files[-1]) if files else ""

def try_captions(url: str, outdir: Path) -> str|None:
    try:
        run([
            "yt-dlp","--skip-download","--write-auto-subs","--write-subs",
            "--sub-langs","en.*","--sub-format","vtt",
            "--ffmpeg-location", FFMPEG,
            "-o", f"{outdir}/%(title)s.%(ext)s", url
        ])
        vtts = list(outdir.glob("*.vtt"))
        return str(vtts[0]) if vtts else None
    except Exception:
        return None
