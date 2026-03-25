from pynput import mouse, keyboard
import time

class InputTracker:
    def __init__(self, key_display_duration=1.5):
        # --- Mouse ---
        self.mouse_pos = (0, 0)
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
        self.mouse_listener.start()

        # --- Keyboard ---
        self.key_display_duration = key_display_duration
        self.key_timestamps = {}  # key -> last pressed time
        self.key_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.key_listener.start()

    # --- Mouse ---
    def _on_mouse_move(self, x, y):
        self.mouse_pos = (x, y)

    def get_mouse_position(self):
        return self.mouse_pos

    # --- Keyboard ---
    def _on_key_press(self, key):
        now = time.time()
        try:
            self.key_timestamps[key.char] = now
        except AttributeError:
            self.key_timestamps[str(key)] = now

    def _on_key_release(self, key):
        pass  # Keep key visible for display_duration

    def get_active_keys(self):
        now = time.time()
        active_keys = [k for k, t in self.key_timestamps.items()
                       if now - t <= self.key_display_duration]
        # Remove old keys
        self.key_timestamps = {k: t for k, t in self.key_timestamps.items()
                               if now - t <= self.key_display_duration}
        return active_keys

    def stop(self):
        self.mouse_listener.stop()
        self.key_listener.stop()
