import argparse
import asyncio
import datetime
import glob
import json
import os
import subprocess
import time
import aiohttp
from playwright.async_api import async_playwright

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_IP        = "192.168.10.87"
OUTPUT_DIR        = "snapshots"
SNAPSHOT_INTERVAL = 6      # seconds between frames
FPS               = 24     # output video frame rate
MIN_SIZE          = 50_000  # discard frames smaller than 50 KB
# ──────────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="K2 Pro timelapse capture")
parser.add_argument(
    "ip",
    nargs="?",
    default=DEFAULT_IP,
    help=f"IP address of the K2 Pro (default: {DEFAULT_IP})",
)
parser.add_argument(
    "--auto",
    action="store_true",
    help="Wait for print to start/stop automatically via Moonraker",
)
args = parser.parse_args()

CAMERA_URL    = f"http://{args.ip}:8000"
MOONRAKER_WS  = f"ws://{args.ip}:7125/websocket"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# clean up any leftover frames from a previous run
old_frames = glob.glob(os.path.join(OUTPUT_DIR, "frame_*.png"))
if old_frames:
    for f in old_frames:
        os.remove(f)
    print(f"Cleaned up {len(old_frames)} old frame(s).")

# timestamped output filename so old timelapses are never overwritten
timestamp  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"k2pro-timelapse-{timestamp}.mp4"


# ── Moonraker WebSocket ────────────────────────────────────────────────────────

async def wait_for_print_state(target_states: list[str]):
    """Connect to Moonraker and block until print_stats.state is in target_states."""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(MOONRAKER_WS) as ws:
            # subscribe to print_stats
            await ws.send_str(json.dumps({
                "jsonrpc": "2.0",
                "method": "printer.objects.subscribe",
                "params": {"objects": {"print_stats": ["state"]}},
                "id": 1,
            }))
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue
                data = json.loads(msg.data)
                # update notifications: params is [{"print_stats": ...}, timestamp]
                params = data.get("params", [])
                if isinstance(params, list) and params:
                    status = params[0].get("print_stats", {})
                elif "result" in data:
                    # initial subscription response: result.status.print_stats
                    status = (
                        data["result"]
                            .get("status", {})
                            .get("print_stats", {})
                    )
                else:
                    status = {}
                state = status.get("state")
                if state in target_states:
                    return state


# ── Capture loop ───────────────────────────────────────────────────────────────

async def capture_loop(page, stop_event: asyncio.Event):
    """Take screenshots every SNAPSHOT_INTERVAL seconds until stop_event is set."""
    frame_index = 0
    video = await page.query_selector("video")

    print("Capture started — one frame every 6 s.")
    while not stop_event.is_set():
        t0 = time.monotonic()

        path = os.path.join(OUTPUT_DIR, f"frame_{frame_index:06d}.png")
        await video.screenshot(path=path)
        size = os.path.getsize(path)

        if size < MIN_SIZE:
            os.remove(path)
            print(f"Discarded small frame ({size // 1024} KB)")
        else:
            print(f"Saved {path}  ({size // 1024} KB)")
            frame_index += 1

        elapsed = time.monotonic() - t0
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=max(0, SNAPSHOT_INTERVAL - elapsed),
            )
        except asyncio.TimeoutError:
            pass

    return frame_index


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["camera", "microphone"],
        )
        page = await context.new_page()

        print(f"Opening {CAMERA_URL} ...")
        await page.goto(CAMERA_URL)

        print("Waiting for video to start playing...")
        await page.wait_for_selector("video")
        await page.evaluate("""() => new Promise((resolve) => {
            const v = document.querySelector('video');
            if (v && v.currentTime > 0) { resolve(); return; }
            v.addEventListener('timeupdate', () => resolve(), { once: true });
        })""")

        stop_event = asyncio.Event()
        frame_count = 0

        try:
            if args.auto:
                # ── Automatic mode ─────────────────────────────────────────
                print(f"Auto mode — connecting to Moonraker at {MOONRAKER_WS}")
                print("Waiting for print to start...")
                await wait_for_print_state(["printing"])
                print("Print started — capturing.")

                capture_task = asyncio.create_task(capture_loop(page, stop_event))

                await wait_for_print_state(["complete", "error", "standby"])
                print("Print finished — stopping capture.")
                stop_event.set()
                frame_count = await capture_task

            else:
                # ── Manual mode ────────────────────────────────────────────
                print("Manual mode — press Ctrl+C to stop and build timelapse.")
                frame_count = await capture_loop(page, stop_event)

        except (KeyboardInterrupt, asyncio.CancelledError):
            stop_event.set()
        finally:
            try:
                await browser.close()
            except Exception:
                pass

    build_timelapse(frame_count)


def build_timelapse(frame_count):
    if frame_count == 0:
        print("No frames captured.")
        return
    print(f"\nBuilding timelapse from {frame_count} frames at {FPS} fps...")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(OUTPUT_DIR, "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        OUTPUT_FILE,
    ], check=True)
    print(f"\nTimelapse saved to {OUTPUT_FILE}")
    duration = frame_count / FPS
    print(f"Duration: {duration:.1f} s  ({frame_count} frames @ {FPS} fps)")


asyncio.run(main())
