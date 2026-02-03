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
import threading
from datetime import datetime

# Import configuration
try:
    from config import *
except ImportError:
    # Default values if config.py doesn't exist
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID = ""
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    ALERT_COOLDOWN_MINUTES = 10
    OBSTRUCTION_THRESHOLD = 20

class FancyShelfDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Shelf Monitor Pro")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')
        self.style = tb.Style("cosmo")

        self.colors = cycle(['#2c3e50', '#3498db', '#e74c3c', '#27ae60'])
        self.models_loaded = False
        self.last_alert_time = 0
        self.ALERT_COOLDOWN = ALERT_COOLDOWN_MINUTES * 60
        self.TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
        self.TELEGRAM_CHAT_ID = TELEGRAM_CHAT_ID
        self.is_running = False
        self.cap = None
        self.detection_count = 0
        
        # Ensure detections folder exists
        os.makedirs("detections", exist_ok=True)

        self.show_login()

    def show_login(self):
        # Create main login container
        self.login_frame = tb.Frame(self.root, padding=40)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Title
        title_frame = tb.Frame(self.login_frame)
        title_frame.pack(pady=(0, 30))
        
        self.login_title_label = tb.Label(title_frame, text="🔐 Admin Access", 
                                         font=("Segoe UI", 28, "bold"), 
                                         bootstyle="primary")
        self.login_title_label.pack()
        
        tb.Label(title_frame, text="Shelf Monitoring System", 
                font=("Segoe UI", 12), bootstyle="secondary").pack()

        # Login form
        form_frame = tb.Frame(self.login_frame)
        form_frame.pack(pady=20)
        
        tb.Label(form_frame, text="Username", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        self.username_entry = tb.Entry(form_frame, width=25, font=("Segoe UI", 11))
        self.username_entry.pack(pady=(0, 15))
        self.username_entry.insert(0, "admin")  # Pre-fill for convenience

        tb.Label(form_frame, text="Password", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        self.password_entry = tb.Entry(form_frame, show="*", width=25, font=("Segoe UI", 11))
        self.password_entry.pack(pady=(0, 20))
        self.password_entry.insert(0, "admin123")  # Pre-fill for convenience

        tb.Button(form_frame, text="▶ Login", bootstyle="success-outline", 
                 width=20, command=self.handle_login).pack()
        
        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.handle_login())
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())

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
        try:
            # Use relative paths for portability
            shelf_model_path = os.path.join("runs", "detect", "train18", "weights", "best.pt")
            empty_model_path = os.path.join("runs", "detect", "train20", "weights", "best.pt")
            
            if not os.path.exists(shelf_model_path):
                raise FileNotFoundError(f"Shelf model not found: {shelf_model_path}")
            if not os.path.exists(empty_model_path):
                raise FileNotFoundError(f"Empty model not found: {empty_model_path}")
                
            self.shelf_model = YOLO(shelf_model_path)
            self.empty_model = YOLO(empty_model_path)
            self.models_loaded = True
            print("Models loaded successfully")  # Use print instead of log_message
        except Exception as e:
            messagebox.showerror("Model Loading Error", f"Failed to load YOLO models: {e}")
            self.root.quit()

    def build_interface(self):
        # Main container
        self.main_frame = tb.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control panel
        control_frame = tb.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Camera selection
        tb.Label(control_frame, text="Camera:").pack(side=tk.LEFT, padx=(0, 5))
        self.camera_list = self.get_available_cameras()
        self.selected_camera = tk.StringVar()
        self.cam_dropdown = tb.Combobox(control_frame, textvariable=self.selected_camera, 
                                       values=self.camera_list, state="readonly", width=15)
        self.cam_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        
        # URL input
        tb.Label(control_frame, text="URL:").pack(side=tk.LEFT, padx=(0, 5))
        self.url_entry = tb.Entry(control_frame, width=40)
        self.url_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.url_entry.insert(0, "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")
        
        # Buttons
        tb.Button(control_frame, text="Start Camera", bootstyle="success", 
                 command=self.start_detection).pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Start URL", bootstyle="primary", 
                 command=self.start_url_detection).pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Open File", bootstyle="secondary", 
                 command=self.run_offline_video).pack(side=tk.LEFT, padx=2)
        self.stop_btn = tb.Button(control_frame, text="Stop", bootstyle="danger", 
                                 command=self.stop_detection, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Test Telegram", bootstyle="warning", 
                 command=self.test_telegram_alert).pack(side=tk.LEFT, padx=2)

        # Video canvas
        self.canvas = tk.Canvas(self.main_frame, width=1200, height=600, bg="#2c3e50")
        self.canvas.pack(pady=10)
        
        # Status labels
        status_frame = tb.Frame(self.main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tb.Label(status_frame, text="Ready to start monitoring")
        self.status_label.pack(side=tk.LEFT)
        
        self.warning_label = tb.Label(status_frame, text="", bootstyle="danger")
        self.warning_label.pack(side=tk.RIGHT)

        # Log area
        self.log_view = scrolledtext.ScrolledText(self.main_frame, height=6, wrap=tk.WORD)
        self.log_view.pack(fill=tk.X, pady=(10, 0))
        
        self.log_message("System initialized successfully")

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

    def is_frame_obstructed(self, frame, threshold=None):
        if threshold is None:
            threshold = OBSTRUCTION_THRESHOLD
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray.mean() < threshold

    def start_detection(self):
        selected = self.selected_camera.get()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a camera from the dropdown.")
            return
        if self.is_running:
            self.stop_detection()
        cam_index = int(selected.split()[-1])
        threading.Thread(target=self._run_detection, args=(cv2.VideoCapture(cam_index),), daemon=True).start()

    def start_url_detection(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a video URL")
            return
        if self.is_running:
            self.stop_detection()
        self.log_message(f"Starting URL detection: {url}")
        threading.Thread(target=self._run_detection, args=(cv2.VideoCapture(url),), daemon=True).start()

    def run_offline_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if file_path:
            if self.is_running:
                self.stop_detection()
            threading.Thread(target=self._run_detection, args=(cv2.VideoCapture(file_path),), daemon=True).start()

    def stop_detection(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Detection stopped")
        self.log_message("Detection stopped by user")

    def run_offline_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if file_path:
            if self.is_running:
                self.stop_detection()
            threading.Thread(target=self._run_detection, args=(cv2.VideoCapture(file_path),), daemon=True).start()

    def _run_detection(self, cap):
        if not cap.isOpened():
            self.root.after(0, lambda: messagebox.showerror("Error", "Failed to open video stream."))
            return

        self.cap = cap
        self.is_running = True
        self.root.after(0, lambda: self.stop_btn.config(state="normal"))
        self.root.after(0, lambda: self.status_label.config(text="Detection running..."))
        
        frame_skip = 30
        frame_count = 0

        try:
            while cap.isOpened() and self.is_running:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                if self.is_frame_obstructed(frame):
                    self.root.after(0, lambda: self.warning_label.config(text="Camera obstructed or too dark"))
                    continue
                else:
                    self.root.after(0, lambda: self.warning_label.config(text=""))

                if frame_count % frame_skip == 0:
                    shelf_results = self.shelf_model(frame)
                    shelf_detections = []
                    
                    for r in shelf_results:
                        for i, box in enumerate(r.boxes.xyxy):
                            x1, y1, x2, y2 = map(int, box)
                            conf = float(r.boxes.conf[i]) if len(r.boxes.conf) > i else 0.0
                            shelf_detections.append({"bbox": (x1, y1, x2, y2), "conf": conf})
                            
                            cropped = frame[y1:y2, x1:x2]
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, f"Shelf {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            
                            empty_results = self.empty_model(cropped)
                            empty_detections = []
                            
                            for res in empty_results:
                                if hasattr(res, 'boxes') and len(res.boxes) > 0:
                                    for j, empty_box in enumerate(res.boxes.xyxy):
                                        empty_conf = float(res.boxes.conf[j]) if len(res.boxes.conf) > j else 0.0
                                        empty_detections.append({"conf": empty_conf})
                                        
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                    cv2.putText(frame, "EMPTY SHELF!", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                    
                                    # Save detection and log
                                    self.save_detection(frame, shelf_detections, empty_detections)
                                    self.send_telegram_alert()

                # Display frame in main thread
                self.root.after(0, lambda f=frame: self._update_canvas(f))
                
                time.sleep(0.03)  # ~30 FPS

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Detection error: {e}"))
        finally:
            cap.release()
            self.is_running = False
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
            self.root.after(0, lambda: self.status_label.config(text="Detection stopped"))

    def save_detection(self, frame, shelf_detections, empty_detections):
        self.detection_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{self.detection_count:04d}_{timestamp}.jpg"
        filepath = os.path.join("detections", filename)
        
        # Save image
        cv2.imwrite(filepath, frame)
        
        # Log detailed detection info
        log_msg = f"\n=== DETECTION #{self.detection_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
        log_msg += f"Image saved: {filename}\n"
        log_msg += f"Shelves detected: {len(shelf_detections)}\n"
        
        for i, shelf in enumerate(shelf_detections):
            x1, y1, x2, y2 = shelf['bbox']
            log_msg += f"  Shelf {i+1}: bbox=({x1},{y1},{x2},{y2}) confidence={shelf['conf']:.3f}\n"
            
        log_msg += f"Empty spaces detected: {len(empty_detections)}\n"
        for i, empty in enumerate(empty_detections):
            log_msg += f"  Empty {i+1}: confidence={empty['conf']:.3f}\n"
            
        log_msg += "Status: ALERT - Empty shelf detected!\n"
        log_msg += "=" * 50
        
        self.root.after(0, lambda: self.log_message(log_msg))

    def _update_canvas(self, frame):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame_rgb.shape[:2]
            # Scale to fit canvas
            canvas_w, canvas_h = 1200, 600
            scale = min(canvas_w/w, canvas_h/h)
            new_w, new_h = int(w*scale), int(h*scale)
            
            img = cv2.resize(frame_rgb, (new_w, new_h))
            img = ImageTk.PhotoImage(image=Image.fromarray(img))
            
            self.canvas.delete("all")
            x_offset = (canvas_w - new_w) // 2
            y_offset = (canvas_h - new_h) // 2
            self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=img)
            self.canvas.image = img
        except Exception as e:
            print(f"Canvas update error: {e}")

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")
    app = FancyShelfDetector(root)
    root.mainloop()
