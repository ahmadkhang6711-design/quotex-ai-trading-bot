````markdown name=DASHBOARD_GUIDE.md url=https://github.com/ahmadkhang6711-design/quotex-ai-trading-bot/blob/main/DASHBOARD_GUIDE.md
# 📊 Dashboard Guide - Quotex AI Trading Bot

## Overview

Your bot includes a **real-time web dashboard** that displays live trading statistics, charts, and analytics.

## 🚀 Accessing the Dashboard

When you start the bot:

```bash
python bot.py
```

The dashboard will automatically start and be available at:

**http://localhost:5000**

Simply open this URL in your web browser to monitor your bot in real-time.

## 📈 Dashboard Features

### 1. **Key Metrics Cards**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Current Balance │  │  Total Trades   │  │    Win Rate     │
│   $1,047.50     │  │       42        │  │      67.6%      │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Total P&L     │  │  Avg Trade      │  │  Active Trades  │
│   +$47.50       │  │    +$1.13       │  │        2        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

- **Current Balance**: Your account balance (updated every 5 seconds)
- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of winning trades
- **Total P&L**: Total profit or loss
- **Avg Trade**: Average profit/loss per trade
- **Active Trades**: Currently open positions

### 2. **Status Indicators**

```
✓ Connected  ⏱ Trading Active  🔄 Last Updated: 12:34:56
```

Shows your bot's current state:
- 🟢 Connected - Connected to Quotex
- 🟡 Trading Active - Currently trading
- 🔄 Last Updated - When data was last refreshed

### 3. **Charts & Graphs**

#### Performance by Asset
Bar chart showing win rate for each trading pair:
```
EURUSD  ████████░░  80%
GBPUSD  ██████░░░░  60%
USDJPY  ███████░░░  70%
```

#### Call vs Put Success
Pie chart showing wins by trade direction:
```
        CALL (28 wins)
       ╱════════════╲
      ╱              ╲
CALL ║                ║ PUT
80%  ║     SUCCESS    ║ 55%
      ╲              ╱
       ╲════════════╱
```

### 4. **Recent Trades Table**

| Time | Asset | Direction | Amount | Result | P&L |
|------|-------|-----------|--------|--------|-----|
| 12:05 | EURUSD | CALL | $50 | ✓ WIN | +$47.50 |
| 12:04 | GBPUSD | PUT | $50 | ✗ LOSS | -$47.50 |
| 12:03 | USDJPY | CALL | $50 | ✓ WIN | +$47.50 |

Shows your last 20 trades with:
- **Time**: When trade was placed
- **Asset**: Currency pair traded
- **Direction**: UP (CALL) or DOWN (PUT)
- **Amount**: Trade size in USD
- **Result**: Win ✓ or Loss ✗
- **P&L**: Profit or loss amount

## 🔄 Real-time Updates

The dashboard automatically refreshes every **5 seconds** with the latest data:

- Live balance updates
- New trades as they execute
- Win rate changes
- Chart updates
- Performance metrics

## 📱 Multi-Monitor Setup

You can open the dashboard on **multiple screens/devices**:

```
Desktop Computer          Laptop
┌────────────────┐       ┌────────────────┐
│  http://localhost:5000  │
│     Dashboard          │
│   (Trading View)       │
└────────────────┘       └────────────────┘
                (Same real-time data)
```

All devices show synchronized data.

## 🔧 Customizing Dashboard Port

Edit `config.py` to change the dashboard port:

```python
# Default: 5000
DASHBOARD_PORT = 5000

# Change to another port if needed:
DASHBOARD_PORT = 8080  # Access at http://localhost:8080
```

Then restart the bot.

## 🎨 Dashboard Theme

The dashboard features:
- 🌙 Dark theme (easy on eyes)
- 🟢 Neon green accent colors
- 📊 Professional UI/UX
- 📈 Interactive charts
- ⚡ Real-time updates

## 📊 Dashboard Metrics Explained

### Win Rate
Shows percentage of profitable trades:
```
Win Rate = (Winning Trades / Total Trades) × 100

Example:
- 28 winning trades
- 42 total trades
- Win Rate = (28/42) × 100 = 66.7%
```

### P&L (Profit/Loss)
Net result of all trades:
```
P&L = Sum of all trade profits and losses

Example:
- Trade 1: +$50
- Trade 2: -$45
- Trade 3: +$75
- Total P&L: +$80
```

### Average Trade
Average profit/loss per trade:
```
Avg Trade = Total P&L / Number of Trades

Example:
- Total P&L: +$80
- Total Trades: 42
- Avg Trade: +$1.90
```

## ⚠️ Important Notes

1. **Dashboard requires internet**: Uses Chart.js for graphs
2. **Localhost only by default**: Access from your local network
3. **Data persists**: Historical data saved in database
4. **No sensitive data**: API keys not displayed
5. **Real-time updates**: May show slight delay (5-10 seconds)

## 🚨 Troubleshooting Dashboard

### "Cannot connect to localhost:5000"
- Check if bot is running: `python bot.py`
- Check firewall settings
- Try different port in config.py

### "Dashboard loads but no data shows"
- Wait 30 seconds for first update
- Check browser console for errors (F12)
- Ensure bot has executed at least one trade

### "Charts not loading"
- Check internet connection (uses CDN)
- Clear browser cache (Ctrl+Shift+Del)
- Try different browser

### "Data not updating"
- Refresh page (F5)
- Check if bot is still running
- Restart both bot and dashboard

## 📊 What to Monitor

### Daily Checks:
- ✅ Win rate trending up or down?
- ✅ P&L increasing over time?
- ✅ Any pattern in losses?
- ✅ Balance growing steadily?

### Weekly Analysis:
- Compare asset performance
- Check call vs put success rate
- Identify best trading times
- Adjust confidence threshold if needed

### Monthly Review:
- Overall profitability
- Win rate consistency
- Risk management effectiveness
- Model accuracy improvement

## 🎯 Using Dashboard for Strategy Improvement

1. **Monitor asset performance**: Which pairs trade best?
2. **Track direction bias**: Are calls or puts more successful?
3. **Identify patterns**: When does bot perform best?
4. **Adjust settings**: Based on observed performance
5. **Optimize confidence**: Fine-tune prediction threshold

## 💾 Exporting Data

Dashboard data is saved in your SQLite database:

```
data/trading_bot.db
```

You can export for analysis:
```bash
sqlite3 data/trading_bot.db ".mode csv" ".output report.csv" "SELECT * FROM trades;"
```

## 🔐 Security Notes

- Dashboard runs on localhost by default (secure)
- No API keys displayed
- Data stored locally
- CORS enabled for flexibility

To expose publicly (not recommended):
```python
# In bot.py, change:
host='0.0.0.0'  # Exposes to network
host='localhost'  # Secure (default)
```

---

**Happy monitoring! 📈**

For more help, check the main README.md
````
