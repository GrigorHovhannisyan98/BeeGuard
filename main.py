import subprocess
import os
import time
from streamer.screen_streamer import ScreenStreamer
import threading
import subprocess
import os
import time
import sys
from streamer.screen_streamer import ScreenStreamer
import threading

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # PyInstaller temp folder
    return os.path.dirname(os.path.abspath(__file__))

def run_mediamtx():
    """Start MediaMTX server with its YAML config and print logs."""
    base_dir = get_base_path()

    exe_path = os.path.join(base_dir, "mediamtx", "mediamtx.exe")
    config_path = os.path.join(base_dir, "mediamtx", "mediamtx.yml")

    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"MediaMTX not found at {exe_path}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")

    process = subprocess.Popen(
        [exe_path, config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print(f"MediaMTX started with PID {process.pid}")

    def print_logs():
        for line in process.stdout:
            print(line, end="")

    threading.Thread(target=print_logs, daemon=True).start()
    return process
    """Start MediaMTX server with its YAML config and print logs."""
    base_dir = os.path.dirname(__file__)
    exe_path = os.path.join(base_dir, "mediamtx", "mediamtx.exe")
    config_path = os.path.join(base_dir, "mediamtx", "mediamtx.yml")

    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"MediaMTX not found at {exe_path}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")

    # Run MediaMTX and capture stdout
    process = subprocess.Popen(
        [exe_path, config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(f"MediaMTX started with PID {process.pid}")

    # Thread to print logs in real-time
    def print_logs():
        for line in process.stdout:
            print(line, end="")

    threading.Thread(target=print_logs, daemon=True).start()
    return process


if __name__ == "__main__":
    # 1. Start MediaMTX
    mediamtx_process = run_mediamtx()
    time.sleep(2)  # give MediaMTX a moment to start

    # 2. RTSP URL must match your mediamtx.yml settings
    rtsp_url = "rtsp://myuser:mypass@127.0.0.1:8554/mainstream"


    # 3. Start screen streaming
    streamer = ScreenStreamer(rtsp_url, width=1280, height=720, fps=15)
    print("Screen streaming started! Press Ctrl+C to stop.")
    streamer.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping stream and MediaMTX...")
        streamer.stop()
        mediamtx_process.terminate()
        mediamtx_process.wait()
        print("Shutdown complete.")
