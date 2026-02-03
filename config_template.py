# Configuration Template for Shelf Monitor
# Copy this file to config.py and fill in your actual values

# Telegram Bot Configuration
# 1. Create a bot by messaging @BotFather on Telegram
# 2. Get your bot token from BotFather
# 3. Get your chat ID by messaging @userinfobot on Telegram
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"

# Login Credentials (change these for security)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Alert Settings
ALERT_COOLDOWN_MINUTES = 10  # Minutes between alerts
OBSTRUCTION_THRESHOLD = 20   # Brightness threshold for obstruction detection