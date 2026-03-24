# K2Pro-Timelapse

Automatic timelapse capture for the **Creality K2 Pro** 3D printer using its built-in WebRTC camera stream.

> **Tested on:** Creality K2 Pro. May work on other K2 variants that expose the same WebRTC camera endpoint on port 8000.

---

## Prerequisites

### 1 — Enable the camera in Fluidd (one-time setup)

The K2 Pro camera is not accessible by default. You first need to apply the workaround by **[DnG-Crafts/K2-Camera](https://github.com/DnG-Crafts/K2-Camera)**, which patches the printer firmware to expose the WebRTC stream.

> ⚠️ This requires **root access** enabled on the printer.
> Firmware updates may revert the change — you may need to re-run the install after updating.

Run these commands on the printer (or follow the original repo instructions):

```sh
python -c "from six.moves import urllib; urllib.request.urlretrieve('https://github.com/DnG-Crafts/K2-Camera/archive/refs/heads/main.zip', '/root/main.zip')"
python -c "import shutil; shutil.unpack_archive('/root/main.zip', '/root/')"
sh ~/K2-Camera-main/install.sh
```

Once installed, the camera stream is available at:
```
http://<printer-ip>:8000
```

### 2 — System dependencies

- Python 3.10+
- `ffmpeg` installed and on your PATH
- A Linux/macOS machine on the same local network as the printer

---

## Installation

```bash
git clone https://github.com/jglerner/K2Pro-Timelapse.git
cd K2Pro-Timelapse

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

---

## Usage

1. Edit the `CAMERA_URL` at the top of `k2pro_timelapse.py` to match your printer's IP:

```python
CAMERA_URL = "http://192.168.10.87:8000"
```

2. Start your print, then run:

```bash
python3 k2pro_timelapse.py
```

3. When the print finishes, press **Ctrl+C**.
   The script will automatically run `ffmpeg` and produce `k2pro-timelapse.mp4`.

---

## How it works

- A headless Chromium browser opens the camera page at port 8000
- A full 1920×1080 screenshot is taken every **6 seconds**
- Frames smaller than 50 KB (blank startup frames) are discarded automatically
- On exit, `ffmpeg` encodes all frames into an H.264 MP4 at **24 fps**

### Timelapse timing

| Print duration | Frames | Video duration (24 fps) |
|----------------|--------|-------------------------|
| 30 min         | 300    | ~12 s                   |
| 1 hour         | 600    | ~25 s                   |
| 4 hours        | 2400   | ~100 s                  |
| 8 hours        | 4800   | ~200 s (~3.3 min)       |

---

## Configuration

| Variable            | Default                        | Description                        |
|---------------------|--------------------------------|------------------------------------|
| `CAMERA_URL`        | `http://192.168.10.87:8000`    | WebRTC camera page URL             |
| `SNAPSHOT_INTERVAL` | `6`                            | Seconds between frames             |
| `FPS`               | `24`                           | Output video frame rate            |
| `MIN_SIZE`          | `50_000`                       | Minimum frame size in bytes        |
| `OUTPUT_DIR`        | `snapshots`                    | Folder for PNG frames              |
| `OUTPUT_FILE`       | `k2pro-timelapse.mp4`          | Output video filename              |

---

## Credits

- **[DnG-Crafts/K2-Camera](https://github.com/DnG-Crafts/K2-Camera)** — the essential camera workaround that makes this possible
- **[Playwright](https://playwright.dev/)** — headless browser automation
- **[ffmpeg](https://ffmpeg.org/)** — video encoding

---

## License

MIT
