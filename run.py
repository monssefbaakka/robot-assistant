"""Single entry point — launches the IoT dashboard."""
import subprocess
import sys

subprocess.run(
    [sys.executable, "-m", "streamlit", "run", "app_complet.py"],
    check=True,
)
