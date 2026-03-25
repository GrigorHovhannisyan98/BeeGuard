import av
import numpy as np
import time
import cv2
import threading
from .tracker import InputTracker

class ScreenStreamer:
    def __init__(self, rtsp_url="rtsp://127.0.0.1:8554/",
                 width=1280, height=720, fps=15, key_display_duration=1.5):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.fps = fps

        # Input tracker
        self.input_tracker = InputTracker(key_display_duration=key_display_duration)

        self.running = False
        self.thread = None

    @staticmethod
    def _draw_cursor(frame, x, y, color=(255,0,0)):
        size = 8
        for dy in range(-size, size):
            for dx in range(-size, size):
                if dx*dx + dy*dy <= size*size:
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < frame.shape[0] and 0 <= xx < frame.shape[1]:
                        frame[yy, xx] = color

    def _capture_loop(self):
        # --- MSS initialized inside thread (Windows fix) ---
        import mss
        import numpy as np
        import av
        import time
        import cv2

        sct = mss.mss()
        monitor = sct.monitors[1]
        src_w, src_h = monitor["width"], monitor["height"]
        ys = (np.linspace(0, src_h - 1, self.height)).astype(np.int32)
        xs = (np.linspace(0, src_w - 1, self.width)).astype(np.int32)

        # Open RTSP output
        output = av.open(self.rtsp_url, mode="w", format="rtsp", options={
            "rtsp_transport": "tcp",
            "muxdelay": "0"
        })
        stream = output.add_stream("libx264", rate=self.fps)
        stream.width = self.width
        stream.height = self.height
        stream.pix_fmt = "yuv420p"
        stream.options = {"preset": "ultrafast", "tune": "zerolatency"}

        frame_time = 1.0 / self.fps

        try:
            while self.running:
                start = time.time()

                # Capture screen
                img = sct.grab(monitor)
                arr = np.array(img)[:, :, :3]
                arr = arr[:, :, ::-1]  # BGRA -> RGB

                # Resize
                arr = arr[ys[:, None], xs[None, :], :]

                # Draw mouse
                mx, my = self.input_tracker.get_mouse_position()
                mx = int(mx * self.width / src_w)
                my = int(my * self.height / src_h)
                self._draw_cursor(arr, mx, my)

                # Draw keys pressed (fixed NoneType issue)
                keys = [str(k) for k in self.input_tracker.get_active_keys() if k is not None]
                if keys:
                    text = "Keys: " + ", ".join(keys)
                    cv2.putText(arr, text, (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Encode frame
                frame = av.VideoFrame.from_ndarray(arr, format="rgb24")
                frame.pts = None
                for packet in stream.encode(frame):
                    output.mux(packet)

                # Maintain FPS
                elapsed = time.time() - start
                if (delay := frame_time - elapsed) > 0:
                    time.sleep(delay)

        finally:
            # Flush encoder
            for packet in stream.encode():
                output.mux(packet)
            output.close()
            self.input_tracker.stop()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
