#!/bin/bash
# Universal Deployment Script for Shelf Monitor

echo "🚀 Deploying Automated Shelf Monitor..."

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.7+"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv shelf_monitor_env

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source shelf_monitor_env/Scripts/activate
else
    source shelf_monitor_env/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p detections
mkdir -p logs

# Set permissions (Unix/Linux/Mac)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    chmod +x setup.sh
    chmod +x run.sh
fi

echo "✅ Deployment complete!"
echo ""
echo "🔧 To configure:"
echo "1. Edit config.py with your Telegram credentials"
echo "2. Run: python main_fin.py"
echo ""
echo "📋 Login credentials:"
echo "   Username: admin"
echo "   Password: admin123"