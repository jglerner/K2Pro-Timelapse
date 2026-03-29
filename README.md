# K2Pro-Timelapse

Automatic timelapse capture for the **Creality K2 Pro** 3D printer using its built-in WebRTC camera stream.

> **Tested on:** Creality K2 Pro. May work on other K2 variants that expose the same WebRTC camera endpoint on port 8000.

---

## Prerequisites

### 1 — Enable the camera (one-time setup on the printer)

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
http://<your-printer-ip>:8000
```

### 2 — Install ffmpeg

#### Windows
```powershell
winget install ffmpeg
```
Or download from https://ffmpeg.org/download.html and add to your PATH.

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt install ffmpeg      # Debian/Ubuntu
sudo dnf install ffmpeg      # Fedora
```

### 3 — Python 3.10 or newer

- **Windows / macOS**: download from https://www.python.org/downloads/
- **Linux**: usually pre-installed (`python3 --version`)

---

## Installation

#### Windows
```powershell
git clone https://github.com/jglerner/K2Pro-Timelapse.git
cd K2Pro-Timelapse
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

#### macOS / Linux
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

### Set it and forget it (recommended)

Run the launcher once after installation. It monitors the printer continuously: when a print starts it captures, when it ends it builds the timelapse, then it immediately waits for the next print. No Ctrl+C, no re-activating the venv, no thinking about it.

#### Linux / macOS
```bash
./k2pro-timelapse.sh
```

#### Windows
```bat
k2pro-timelapse.bat
```

To use a different printer IP, pass it as an argument:
```bash
./k2pro-timelapse.sh 192.168.1.50
```

If you don't pass an IP it defaults to `192.168.10.87`.

---

### Start automatically at login (Linux)

To have it start every time you log in without touching a terminal:

```bash
systemctl --user enable --now k2pro-timelapse
```

Check it is running:
```bash
systemctl --user status k2pro-timelapse
```

Stop it:
```bash
systemctl --user stop k2pro-timelapse
```

---

### Manual mode

If you want to control start/stop yourself:

#### Linux / macOS
```bash
source venv/bin/activate
python3 k2pro_timelapse.py <YOUR-PRINTER-IP>
```

#### Windows
```powershell
venv\Scripts\activate
python k2pro_timelapse.py <YOUR-PRINTER-IP>
```

Press **Ctrl+C** when the print finishes — the script will automatically run `ffmpeg` and produce the timelapse MP4.

---

### Automatic mode (single print, no launcher)

```bash
source venv/bin/activate
python3 k2pro_timelapse.py <YOUR-PRINTER-IP> --auto
```

Connects to Moonraker, waits for the print to start, captures automatically, stops and builds the timelapse when the print ends, then waits for the next print. Press Ctrl+C to quit.

---

## Where are the MP4 files?

Each timelapse is saved in the **same folder where you cloned the project**, named with the date and time it was built:

```
k2pro-timelapse-20260329_143512.mp4
k2pro-timelapse-20260330_091047.mp4
...
```

They are never overwritten — every print gets its own file.

---

## Demo

[![K2 Pro Timelapse Demo](https://img.youtube.com/vi/hBXcu0E1xgQ/0.jpg)](https://youtu.be/hBXcu0E1xgQ)

---

## How it works

- A headless Chromium browser opens the camera page at port 8000
- A full **1920×1080** screenshot is taken every **6 seconds**
- Frames smaller than 50 KB (blank startup frames) are discarded automatically
- On exit, `ffmpeg` encodes all frames into an **H.264 MP4 at 24 fps**

### Timelapse timing

| Print duration | Frames | Video duration (24 fps) |
|----------------|--------|-------------------------|
| 30 min         | 300    | ~12 s                   |
| 1 hour         | 600    | ~25 s                   |
| 4 hours        | 2400   | ~100 s                  |
| 8 hours        | 4800   | ~200 s (~3.3 min)       |

---

## Configuration

All settings are at the top of `k2pro_timelapse.py`:

| Variable             | Default               | Description                      |
|----------------------|-----------------------|----------------------------------|
| `DEFAULT_IP`         | `192.168.10.87`       | Fallback printer IP              |
| `SNAPSHOT_INTERVAL`  | `6`                   | Seconds between frames           |
| `FPS`                | `24`                  | Output video frame rate          |
| `MIN_SIZE`           | `50_000`              | Minimum frame size in bytes      |
| `OUTPUT_DIR`         | `snapshots`           | Folder for PNG frames            |
| `OUTPUT_FILE`        | `k2pro-timelapse-YYYYMMDD_HHMMSS.mp4` | Output video filename (auto-timestamped) |

---

## Credits

- **[DnG-Crafts/K2-Camera](https://github.com/DnG-Crafts/K2-Camera)** — the essential camera workaround that makes this possible
- **[Playwright](https://playwright.dev/)** — headless browser automation
- **[ffmpeg](https://ffmpeg.org/)** — video encoding

---

## License

MIT
