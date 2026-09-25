"""Word Stars — desktop launcher.

Runs the Flask app in a background thread and shows it in a native
app window via pywebview, so it behaves like a normal installed game
instead of a website. Player data and the login session persist
between launches in a per-user app data folder.
"""

import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path


def _app_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    path = Path(base) / "WordStars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _persistent_secret_key(data_dir: Path) -> str:
    key_file = data_dir / "secret.key"
    if key_file.exists():
        return key_file.read_text().strip()
    key = secrets.token_hex(32)
    key_file.write_text(key)
    return key


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 15.0) -> None:
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.2)


def main() -> None:
    data_dir = _app_data_dir()

    os.environ.setdefault("DATA_DIR", str(data_dir))
    os.environ.setdefault("SECRET_KEY", _persistent_secret_key(data_dir))
    os.environ.setdefault("FLASK_DEBUG", "0")
    os.environ.setdefault("BEHIND_PROXY", "0")
    port = _free_port()
    os.environ["PORT"] = str(port)

    if getattr(sys, "frozen", False):
        os.chdir(sys._MEIPASS)  # type: ignore[attr-defined]

    import app as flask_app

    server = threading.Thread(
        target=lambda: flask_app.app.run(
            host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True
        ),
        daemon=True,
    )
    server.start()

    url = f"http://127.0.0.1:{port}/"
    _wait_for_server(url)

    import webview

    webview.create_window(
        "Word Stars",
        url,
        width=1280,
        height=820,
        min_size=(900, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
