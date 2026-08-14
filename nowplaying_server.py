import asyncio
import sys
import tempfile
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, send_file, abort, redirect
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winsdk.windows.storage.streams import Buffer, DataReader, InputStreamOptions

# Substring match against a session's SourceAppUserModelId (case-insensitive).
# Run list_sessions.py while Tidal is playing if this doesn't pick it up.
APP_ID_FILTER = "tidal"
POLL_INTERVAL = 1.0

# When frozen by PyInstaller, bundled files (like static/) live under
# sys._MEIPASS instead of next to this script.
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
ART_PATH = Path(tempfile.gettempdir()) / "tidal_nowplaying_art.png"

state_lock = threading.Lock()
state = {"title": None, "artist": None, "album": None, "playing": False, "art_available": False}


async def read_thumbnail(thumb_ref):
    if thumb_ref is None:
        return None
    stream = await thumb_ref.open_read_async()
    if stream.size == 0:
        return None
    buffer = Buffer(stream.size)
    await stream.read_async(buffer, stream.size, InputStreamOptions.READ_AHEAD)
    reader = DataReader.from_buffer(buffer)
    data = bytearray(stream.size)
    reader.read_bytes(data)
    return bytes(data)


async def poll_once():
    manager = await MediaManager.request_async()

    target = None
    for session in manager.get_sessions():
        aumid = (session.source_app_user_model_id or "").lower()
        if APP_ID_FILTER in aumid:
            target = session
            break

    if target is None:
        with state_lock:
            state.update(title=None, artist=None, album=None, playing=False, art_available=False)
        return

    props = await target.try_get_media_properties_async()
    playback_info = target.get_playback_info()
    is_playing = bool(playback_info and playback_info.playback_status == PlaybackStatus.PLAYING)

    art_bytes = await read_thumbnail(props.thumbnail) if props else None
    if art_bytes:
        ART_PATH.write_bytes(art_bytes)

    with state_lock:
        state.update(
            title=props.title if props else None,
            artist=props.artist if props else None,
            album=props.album_title if props else None,
            playing=is_playing,
            art_available=bool(art_bytes),
        )


def poll_loop():
    while True:
        try:
            asyncio.run(poll_once())
        except Exception as exc:
            print(f"[nowplaying] poll error: {exc}")
        time.sleep(POLL_INTERVAL)


app = Flask(__name__, static_folder=str(BASE_DIR / "static"), static_url_path="")


@app.get("/")
def index():
    return redirect("/overlay.html")


@app.get("/nowplaying.json")
def nowplaying():
    with state_lock:
        return jsonify(dict(state))


@app.get("/art.png")
def art():
    if not ART_PATH.exists():
        abort(404)
    return send_file(ART_PATH, mimetype="image/png", max_age=0)


def set_console_icon_and_minimize():
    import ctypes

    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if not hwnd:
        return

    # Windows' console host doesn't always pick up the exe's embedded icon
    # for the taskbar entry on its own, so pull it out and set it explicitly.
    large = ctypes.c_void_p()
    small = ctypes.c_void_p()
    count = ctypes.windll.shell32.ExtractIconExW(sys.executable, 0, ctypes.byref(large), ctypes.byref(small), 1)
    WM_SETICON = 0x0080
    ICON_SMALL = 0
    ICON_BIG = 1
    if count > 0:
        if small.value:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small)
        if large.value:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, large)

    SW_MINIMIZE = 6
    ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)


if __name__ == "__main__":
    set_console_icon_and_minimize()
    threading.Thread(target=poll_loop, daemon=True).start()
    app.run(host="127.0.0.1", port=5959)
