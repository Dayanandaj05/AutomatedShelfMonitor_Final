import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from auth import validate_login
import cv2
import os
import requests
import time
import numpy as np
from ultralytics import YOLO
from itertools import cycle
from PIL import Image, ImageTk

class FancyShelfDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Fancy Shelf Stock Monitoring")
        self.root.geometry("1280x720")
        self.style = tb.Style("flatly")

        self.colors = cycle(['#8899aa', '#aacccc', '#99bbbb', '#667788'])
        self.models_loaded = False
        self.last_alert_time = 0
        self.ALERT_COOLDOWN = 10 * 60
        self.TELEGRAM_BOT_TOKEN = YOUR_BOT_TOKEN
        self.TELEGRAM_CHAT_ID = YOUR_CHAT_ID

        self.show_login()

    def animate_login_title(self):
        next_color = next(self.colors)
        self.login_title_label.config(fg=next_color)
        self.root.after(700, self.animate_login_title)

    def show_login(self):
        self.login_frame = tb.Frame(self.root)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.login_title_label = tk.Label(self.login_frame, text="🔐 Admin Login", font=("Segoe UI", 24, "bold"), bg=self.root['bg'])
        self.login_title_label.pack(pady=15)
        self.animate_login_title()

        tb.Label(self.login_frame, text="Username:", bootstyle=INFO).pack(pady=5)
        self.username_entry = tb.Entry(self.login_frame, width=30)
        self.username_entry.pack()

        tb.Label(self.login_frame, text="Password:", bootstyle=INFO).pack(pady=5)
        self.password_entry = tb.Entry(self.login_frame, show="*", width=30)
        self.password_entry.pack()

        tb.Button(self.login_frame, text="Login", bootstyle=SUCCESS, width=20, command=self.handle_login).pack(pady=20)

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        result = validate_login(username, password)

        if isinstance(result, tuple):
            valid, message = result
        else:
            valid, message = result, "Invalid login"

        if valid:
            self.login_frame.destroy()
            self.load_models()
            self.build_interface()
        else:
            messagebox.showerror("Login Failed", message)

    def load_models(self):
        self.shelf_model = YOLO("runs/detect/train18/weights/best.pt")
        self.empty_model = YOLO("runs/detect/train20/weights/best.pt")
        self.models_loaded = True

    def build_interface(self):
        self.main_frame = tb.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tb.Frame(self.main_frame, width=200, bootstyle=SECONDARY)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tb.Label(self.sidebar, text="📷 Cameras", font=("Segoe UI", 12, "bold"), bootstyle=INFO).pack(pady=(5, 0))
        self.camera_list = self.get_available_cameras()
        self.selected_camera = tk.StringVar()
        self.cam_dropdown = tb.Combobox(self.sidebar, textvariable=self.selected_camera, values=self.camera_list, state="readonly")
        self.cam_dropdown.pack(pady=5)

        tb.Button(self.sidebar, text="🔄 Refresh", bootstyle=INFO, command=self.refresh_cameras).pack(fill=tk.X, pady=5)
        tb.Button(self.sidebar, text="▶️ Open Feed", bootstyle=PRIMARY, command=self.start_detection).pack(fill=tk.X, pady=5)
        tb.Button(self.sidebar, text="📂 Open Video File", bootstyle=SECONDARY, command=self.run_offline_video).pack(fill=tk.X, pady=5)
        tb.Button(self.sidebar, text="📨 Test Telegram", bootstyle=WARNING, command=self.test_telegram_alert).pack(fill=tk.X, pady=5)
        tb.Button(self.sidebar, text="❌ Exit", bootstyle=DANGER, command=self.root.quit).pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.canvas = tk.Canvas(self.main_frame, width=960, height=540, bg="black")
        self.canvas.pack(side=tk.TOP, padx=5, pady=5)

        self.warning_label = tb.Label(self.main_frame, text="", bootstyle="danger")
        self.warning_label.pack()

        log_frame = tb.LabelFrame(self.root, text="📜 Alert Log", bootstyle="info")
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.log_view = scrolledtext.ScrolledText(log_frame, height=4, wrap=tk.WORD)
        self.log_view.pack(fill=tk.X)

    def log_message(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_view.insert(tk.END, f"{timestamp}: {message}\n")
        self.log_view.see(tk.END)

    def get_available_cameras(self, max_index=5):
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.read()[0]:
                available.append(f"Camera {i}")
            cap.release()
        return available

    def refresh_cameras(self):
        self.cam_dropdown["values"] = self.get_available_cameras()

    def test_telegram_alert(self):
        message = "✅ *Telegram Test Successful!*\nThis is a test alert from the Shelf Monitoring System."
        telegram_url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": self.TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(telegram_url, json=payload)
            if response.status_code == 200:
                messagebox.showinfo("Telegram Test", "Test alert sent successfully!")
            else:
                self.log_message(f"Telegram error: {response.text}")
        except Exception as e:
            self.log_message(f"Telegram exception: {e}")

    def send_telegram_alert(self):
        current_time = time.time()
        if current_time - self.last_alert_time < self.ALERT_COOLDOWN:
            self.log_message("⚠️ Alert not sent - system is on cooldown.")
            return

        message = "🚨 *Restock Alert!* 🚨\n\nAn empty shelf has been detected. Please restock immediately."
        telegram_url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": self.TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(telegram_url, json=payload)
            if response.status_code == 200:
                self.last_alert_time = current_time
                self.log_message("Empty shelf detected and alert sent.")
            else:
                self.log_message(f"Telegram error: {response.text}")
        except Exception as e:
            self.log_message(f"Telegram exception: {e}")

    def is_frame_obstructed(self, frame, threshold=20):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray.mean() < threshold

    def start_detection(self):
        selected = self.selected_camera.get()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a camera from the dropdown.")
            return
        cam_index = int(selected.split()[-1])
        self.run_detection(cv2.VideoCapture(cam_index))

    def run_offline_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if file_path:
            self.run_detection(cv2.VideoCapture(file_path))

    def run_detection(self, cap):
        if not cap.isOpened():
            messagebox.showerror("Error", "Failed to open video stream.")
            return

        frame_skip = 30
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if self.is_frame_obstructed(frame):
                self.warning_label.config(text="⚠️ Camera view obstructed or too dark.")
                self.log_message("⚠️ Camera frame is obstructed or too dark.")
                continue
            else:
                self.warning_label.config(text="")

            if frame_count % frame_skip == 0:
                results = self.shelf_model(frame)
                for r in results:
                    for box in r.boxes.xyxy:
                        x1, y1, x2, y2 = map(int, box)
                        cropped = frame[y1:y2, x1:x2]
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "Shelf", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        empty_results = self.empty_model(cropped)
                        for res in empty_results:
                            if hasattr(res, 'boxes') and len(res.boxes) > 0:
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                cv2.putText(frame, "Empty Space!", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                self.send_telegram_alert()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(frame_rgb, (960, 540))
            img = ImageTk.PhotoImage(image=Image.fromarray(img))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img

            self.root.update()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    app = FancyShelfDetector(root)
    root.mainloop()
