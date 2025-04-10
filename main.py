import customtkinter as ctk
import json
import os
import pyperclip
import threading
import time
from PIL import Image
import ctypes
import win32clipboard
import win32con
import psutil  # To get system stats (CPU, memory, etc.)

# ---------- CONFIG ----------
CONFIG_PATH = "config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"theme": "Dark", "clipboard_history_limit": 20}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

# ---------- APP ----------
class UtilityApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = load_config()
        ctk.set_appearance_mode(self.config.get("theme", "Dark"))
        ctk.set_default_color_theme("blue")

        self.title("All-in-One Utility")
        self.geometry("700x500")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self, height=40)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self.top_bar, text="Utility Suite", font=("Arial", 18))
        self.title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        settings_icon = ctk.CTkImage(light_image=Image.open("assets/settings.png"),
                                     dark_image=Image.open("assets/settings.png"), size=(24, 24))
        self.settings_button = ctk.CTkButton(self.top_bar, image=settings_icon, text="", width=40, command=self.open_settings)
        self.settings_button.grid(row=0, column=2, padx=10)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky="nsew")

        self.clipboard_tab = self.tabs.add("Clipboard")
        self.organizer_tab = self.tabs.add("Files")
        self.monitor_tab = self.tabs.add("System Monitor")

        self.setup_clipboard_tab()

        ctk.CTkLabel(self.organizer_tab, text="File Organizer coming soon").pack(pady=20)
        ctk.CTkLabel(self.monitor_tab, text="System Monitor coming soon").pack(pady=20)

        self.clipboard_history = []
        self.last_clipboard = ""
        self.running = True
        threading.Thread(target=self.monitor_clipboard, daemon=True).start()

        # Start the thread to update system stats
        threading.Thread(target=self.update_system_stats, daemon=True).start()

    def setup_clipboard_tab(self):
        self.clipboard_frame = ctk.CTkFrame(self.clipboard_tab)
        self.clipboard_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.clipboard_frame, label_text="Clipboard History")
        self.scrollable_frame.pack(fill="both", expand=True)

    def monitor_clipboard(self):
        while self.running:
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    file_paths = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    win32clipboard.CloseClipboard()
                    if file_paths and file_paths != self.last_clipboard:
                        self.last_clipboard = file_paths
                        self.clipboard_history.insert(0, file_paths)
                        self.clipboard_history = self.clipboard_history[:self.config.get("clipboard_history_limit", 20)]
                        self.update_clipboard_ui()
                        continue
                else:
                    win32clipboard.CloseClipboard()

                current = pyperclip.paste()
                if current != self.last_clipboard and isinstance(current, str) and current.strip():
                    self.last_clipboard = current
                    self.clipboard_history.insert(0, current)
                    self.clipboard_history = self.clipboard_history[:self.config.get("clipboard_history_limit", 20)]
                    self.update_clipboard_ui()
            except Exception as e:
                pass
            time.sleep(1)

    def update_clipboard_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for item in self.clipboard_history:
            if isinstance(item, list):  # File paths
                for file in item:
                    label = ctk.CTkLabel(self.scrollable_frame, text=f"📁 {file}", anchor="w", justify="left", wraplength=600)
                    label.pack(fill="x", pady=2, padx=5)
                    label.bind("<Button-1>", lambda e, f=file: pyperclip.copy(f))
            else:  # Text
                label = ctk.CTkLabel(self.scrollable_frame, text=item, anchor="w", justify="left", wraplength=600)
                label.pack(fill="x", pady=2, padx=5)
                label.bind("<Button-1>", lambda e, t=item: pyperclip.copy(t))

    def update_system_stats(self):
        while self.running:
            # Fetch system stats (CPU, RAM, etc.) using psutil
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            gpu = self.get_gpu_usage()

            # Update your overlay or UI with these stats
            print(f"CPU: {cpu}% | RAM: {memory}% | GPU: {gpu}%")
            time.sleep(1)

    def get_gpu_usage(self):
        # This method can be customized depending on your GPU's interface (NVIDIA, AMD, etc.)
        # If using NVIDIA, for example, you can call nvidia-smi via subprocess or use libraries like GPUtil
        return 0  # Just a placeholder for now

    def open_settings(self):
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Settings")
        settings_win.geometry("300x300")

        theme_var = ctk.StringVar(value=self.config.get("theme", "Dark"))

        def update_theme():
            new_theme = theme_var.get()
            ctk.set_appearance_mode(new_theme)
            self.config["theme"] = new_theme
            save_config(self.config)

        ctk.CTkRadioButton(settings_win, text="Dark", variable=theme_var, value="Dark", command=update_theme).pack(pady=5)
        ctk.CTkRadioButton(settings_win, text="Light", variable=theme_var, value="Light", command=update_theme).pack(pady=5)

        clipboard_history_limit = ctk.IntVar(value=self.config.get("clipboard_history_limit", 20))
        ctk.CTkLabel(settings_win, text="Clipboard History Limit:", font=("Arial", 14)).pack(pady=5)
        ctk.CTkSlider(settings_win, from_=1, to=50, variable=clipboard_history_limit).pack(pady=10)

        def update_clipboard_limit():
            self.config["clipboard_history_limit"] = clipboard_history_limit.get()
            save_config(self.config)

        ctk.CTkButton(settings_win, text="Save Settings", command=update_clipboard_limit).pack(pady=10)

    def on_closing(self):
        """Handle the closing event."""
        self.running = False  # Stop background threads
        self.destroy()  # Close the application window

# ---------- RUN ----------
if __name__ == "__main__":
    app = UtilityApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)  # Connect the close button to on_closing
    app.mainloop()
