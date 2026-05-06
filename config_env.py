import os
from pathlib import Path


_LOADED = False


def load_env_file():
    """Load key=value pairs from a local .env file without overriding real env vars."""
    global _LOADED
    if _LOADED:
        return

    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        _LOADED = True
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

    _LOADED = True
