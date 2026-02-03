# 📦 Automated Shelf Monitor

AI-powered shelf monitoring system using YOLO object detection with real-time alerts via Telegram.

## 🚀 Quick Deployment (Any Machine)

### Option 1: One-Click Deploy
**Windows:**
```cmd
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Setup
1. **Clone & Setup:**
```bash
git clone <your-repo-url>
cd AutomatedShelfMonitor_Final
```

2. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run:**
```bash
python main_fin.py
```

## 🔐 Login
- **Username:** `admin`
- **Password:** `admin123`

## 📋 Features
- ✅ Real-time shelf detection with confidence scores
- ✅ Empty space detection with alerts
- ✅ **Detailed detection logs** with timestamps
- ✅ **Automatic image saving** in `detections/` folder
- ✅ Telegram notifications
- ✅ Camera & video file support
- ✅ URL video streaming
- ✅ Threaded processing (non-blocking UI)

## 📁 Detection Storage
- All detections saved in `detections/` folder
- Images named: `detection_XXXX_YYYYMMDD_HHMMSS.jpg`
- Detailed logs show:
  - Detection count
  - Timestamp
  - Bounding boxes
  - Confidence scores
  - Alert status

## 🛠️ Configuration
Edit `config.py`:
```python
TELEGRAM_BOT_TOKEN = "your_bot_token"  # From @BotFather
TELEGRAM_CHAT_ID = "your_chat_id"      # From @userinfobot
```

## 🎯 Test Videos
Pre-loaded working URLs:
- Big Buck Bunny (default)
- Elephant Dream
- Various test videos

## 📊 Detection Output Example
```
=== DETECTION #001 - 2024-01-15 14:30:25 ===
Image saved: detection_0001_20240115_143025.jpg
Shelves detected: 2
  Shelf 1: bbox=(100,50,300,200) confidence=0.856
  Shelf 2: bbox=(400,60,600,220) confidence=0.743
Empty spaces detected: 1
  Empty 1: confidence=0.912
Status: ALERT - Empty shelf detected!
```

## 📁 Project Structure
```
AutomatedShelfMonitor_Final/
├── main_fin.py          # Main application
├── config.py            # Configuration
├── auth.py              # Authentication
├── requirements.txt     # Dependencies
├── deploy.bat/.sh       # Deployment scripts
├── detections/          # Saved detection images
├── runs/detect/         # YOLO model files
└── test_videos.md       # Test video URLs
```