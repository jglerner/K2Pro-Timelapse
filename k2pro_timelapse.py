import asyncio
import os
import subprocess
import time
from playwright.async_api import async_playwright

# ── Configuration ─────────────────────────────────────────────────────────────
CAMERA_URL       = "http://192.168.10.87:8000"   # WebRTC camera page on the K2 Pro
OUTPUT_DIR       = "snapshots"                   # folder for captured PNG frames
OUTPUT_FILE      = "k2pro-timelapse.mp4"         # final timelapse video
SNAPSHOT_INTERVAL = 6                            # seconds between frames
FPS              = 24                            # output video frame rate
MIN_SIZE         = 50_000                        # discard frames smaller than 50 KB
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    frame_index = 0

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

        # wait for the <video> element to start playing
        print("Waiting for video to start playing...")
        await page.wait_for_selector("video")
        await page.evaluate("""() => new Promise((resolve) => {
            const v = document.querySelector('video');
            if (v && v.currentTime > 0) { resolve(); return; }
            v.addEventListener('timeupdate', () => resolve(), { once: true });
        })""")
        print("Video playing — capturing every 6 s.  Press Ctrl+C to stop and build timelapse.")

        try:
            while True:
                t0 = time.monotonic()

                path = os.path.join(OUTPUT_DIR, f"frame_{frame_index:06d}.png")
                await page.screenshot(path=path, full_page=False)
                size = os.path.getsize(path)

                if size < MIN_SIZE:
                    os.remove(path)
                    print(f"Discarded small frame ({size // 1024} KB)")
                else:
                    print(f"Saved {path}  ({size // 1024} KB)")
                    frame_index += 1

                elapsed = time.monotonic() - t0
                await asyncio.sleep(max(0, SNAPSHOT_INTERVAL - elapsed))

        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            try:
                await browser.close()
            except Exception:
                pass

    build_timelapse(frame_index)


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
