"""
Configuration file for Quotex AI Trading Bot
Store all settings and credentials here
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============ QUOTEX CREDENTIALS ============
QUOTEX_EMAIL = os.getenv("QUOTEX_EMAIL", "your_email@gmail.com")
QUOTEX_PASSWORD = os.getenv("QUOTEX_PASSWORD", "your_password")
QUOTEX_ACCOUNT_TYPE = "demo"  # Change to "real" for live trading

# ============ TRADING SETTINGS ============
# Assets to trade (Quotex symbols)
TRADING_ASSETS = [
    "EURUSD",
    "GBPUSD", 
    "USDJPY",
    "AUDUSD",
]

# Trading timeframe (in seconds)
TIMEFRAME = 60  # 1 minute candles
CANDLE_COUNT = 100  # Number of candles for analysis

# ============ AI MODEL SETTINGS ============
MODEL_TYPE = "random_forest"  # Options: random_forest, lstm, gradient_boosting
PREDICTION_CONFIDENCE_THRESHOLD = 0.65  # Min confidence to place trade (0-1)
MODEL_UPDATE_INTERVAL = 3600  # Retrain model every hour

# ============ RISK MANAGEMENT ============
INITIAL_BALANCE = 1000  # Starting capital
MAX_POSITION_SIZE = 0.05  # Risk 5% per trade
STOP_LOSS_PERCENT = 2  # Stop loss at 2%
TAKE_PROFIT_PERCENT = 5  # Take profit at 5%
MAX_CONCURRENT_TRADES = 3  # Max open positions

# ============ EXPIRATION TIME ============
EXPIRATION_TIME = 60  # 1 minute expiration for trades

# ============ LOGGING ============
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "logs/trading_bot.log"

# ============ DATABASE ============
DB_FILE = "data/trading_bot.db"
DATA_SAVE_INTERVAL = 300  # Save data every 5 minutes

# ============ NOTIFICATIONS ============
SEND_NOTIFICATIONS = True
NOTIFICATION_EMAIL = "your_email@gmail.com"  # For alerts

# ============ FEATURE FLAGS ============
USE_AI = True  # Enable AI predictions
USE_TECHNICAL_INDICATORS = True  # Enable TA analysis
AUTO_TRADING = False  # Start trading automatically
PAPER_TRADING = True  # Demo mode testing
