import shutil, tempfile
from pathlib import Path

def mkwork(prefix="job_"):
    return Path(tempfile.mkdtemp(prefix=prefix))

def cleanup(path):
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

def bytes_ok(path: str, max_mb=48):
    try:
        return Path(path).stat().st_size <= max_mb * 1024 * 1024
    except Exception:
        return False
