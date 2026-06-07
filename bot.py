"""
Updated Main Trading Bot with Dashboard Integration
"""

import logging
import time
import json
import threading
from datetime import datetime
from typing import Dict, List
import pandas as pd
import numpy as np
from quotex_api import QuotexAPI
from ai_model import AITrader
from dashboard import DashboardServer
from config import *

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    """Main AI-powered Quotex trading bot with Dashboard"""
    
    def __init__(self, enable_dashboard=True, dashboard_port=5000):
        """Initialize the trading bot"""
        logger.info("=" * 60)
        logger.info("QUOTEX AI TRADING BOT INITIALIZING")
        logger.info("=" * 60)
        
        self.quotex = QuotexAPI(QUOTEX_EMAIL, QUOTEX_PASSWORD, QUOTEX_ACCOUNT_TYPE)
        self.ai = AITrader(model_type=MODEL_TYPE)
        
        self.active_trades = {}
        self.trade_history = []
        self.running = False
        self.last_model_update = time.time()
        
        # Dashboard
        self.enable_dashboard = enable_dashboard
        self.dashboard = None
        self.dashboard_thread = None
        self.dashboard_port = dashboard_port
        
        logger.info("✓ Bot initialized successfully")
    
    def start_dashboard(self):
        """Start the web dashboard in a separate thread"""
        if not self.enable_dashboard:
            logger.info("Dashboard disabled")
            return
        
        try:
            logger.info(f"🌐 Starting Dashboard on http://localhost:{self.dashboard_port}")
            
            self.dashboard = DashboardServer(port=self.dashboard_port)
            self.dashboard.bot_instance = self
            
            # Run dashboard in separate thread
            self.dashboard_thread = threading.Thread(
                target=lambda: self.dashboard.run(debug=False),
                daemon=True
            )
            self.dashboard_thread.start()
            
            logger.info(f"✓ Dashboard running at http://localhost:{self.dashboard_port}")
            logger.info("  Open in your browser to view real-time statistics")
            
        except Exception as e:
            logger.error(f"Error starting dashboard: {str(e)}")
    
    def start(self):
        """Start the trading bot"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("STARTING TRADING BOT")
            logger.info("=" * 60)
            
            # Connect to Quotex
            if not self.quotex.connect():
                logger.error("Failed to connect to Quotex")
                return False
            
            balance = self.quotex.get_balance()
            logger.info(f"✓ Connected to Quotex")
            logger.info(f"✓ Account Type: {QUOTEX_ACCOUNT_TYPE}")
            logger.info(f"✓ Starting Balance: ${balance:.2f}")
            
            # Start dashboard
            self.start_dashboard()
            
            # Train AI model with historical data
            logger.info("\n📊 Training AI model with historical data...")
            if not self._train_ai_model():
                logger.warning("AI model training failed, using prediction anyway")
            
            self.running = True
            logger.info("\n✓ Bot is RUNNING and ready to trade!")
            logger.info(f"✓ Trading Assets: {', '.join(TRADING_ASSETS)}")
            logger.info(f"✓ Timeframe: {TIMEFRAME}s")
            logger.info(f"✓ Max Risk per Trade: {MAX_POSITION_SIZE * 100}%")
            
            if self.enable_dashboard:
                logger.info(f"\n📊 DASHBOARD: http://localhost:{self.dashboard_port}")
                logger.info("   Open this URL in your web browser to view live updates")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            return False
    
    def _train_ai_model(self):
        """Train the AI model with historical data"""
        try:
            for asset in TRADING_ASSETS[:1]:
                logger.info(f"  Fetching data for {asset}...")
                
                df = self.quotex.get_candles(asset, TIMEFRAME, CANDLE_COUNT * 2)
                
                if df is None or len(df) == 0:
                    logger.warning(f"  Could not fetch data for {asset}")
                    continue
                
                logger.info(f"  Training model on {len(df)} candles...")
                
                if self.ai.train(df):
                    self.ai.save_model()
                    logger.info(f"✓ Model trained successfully on {asset}")
                    return True
                else:
                    logger.warning(f"Failed to train model on {asset}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error training AI model: {str(e)}")
            return False
    
    def run_trading_cycle(self):
        """Execute one complete trading cycle"""
        try:
            if not self.running or not self.quotex.is_connected():
                logger.warning("Bot not running or connection lost")
                return
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n{'='*60}")
            logger.info(f"TRADING CYCLE - {current_time}")
            logger.info(f"{'='*60}")
            
            balance = self.quotex.get_balance()
            logger.info(f"Current Balance: ${balance:.2f}")
            logger.info(f"Active Trades: {len(self.active_trades)}")
            
            for asset in TRADING_ASSETS:
                logger.info(f"\n📈 Analyzing {asset}...")
                
                df = self.quotex.get_candles(asset, TIMEFRAME, CANDLE_COUNT)
                
                if df is None or len(df) == 0:
                    logger.warning(f"Could not fetch data for {asset}")
                    continue
                
                prediction = self.ai.predict(df)
                logger.info(f"  Direction: {prediction['direction']}")
                logger.info(f"  Confidence: {prediction['confidence']:.2%}")
                
                if prediction['confidence'] >= PREDICTION_CONFIDENCE_THRESHOLD:
                    position_size = self._calculate_position_size(balance)
                    self._place_trade(asset, prediction['direction'], position_size)
                else:
                    logger.info(f"  ⏭️  Confidence too low ({prediction['confidence']:.2%} < {PREDICTION_CONFIDENCE_THRESHOLD:.2%})")
            
            if time.time() - self.last_model_update > MODEL_UPDATE_INTERVAL:
                logger.info("\n🔄 Updating AI model...")
                self._train_ai_model()
                self.last_model_update = time.time()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
    
    def _calculate_position_size(self, balance):
        """Calculate safe position size based on risk management"""
        position_size = balance * MAX_POSITION_SIZE
        return round(position_size, 2)
    
    def _place_trade(self, asset, direction, amount):
        """Place a trade with the AI prediction"""
        try:
            if len(self.active_trades) >= MAX_CONCURRENT_TRADES:
                logger.warning(f"Max concurrent trades ({MAX_CONCURRENT_TRADES}) reached")
                return
            
            trade_result = self.quotex.place_trade(
                asset=asset,
                direction=direction.lower(),
                amount=amount,
                expiration_time=EXPIRATION_TIME
            )
            
            if trade_result['status'] == 'success':
                trade_id = trade_result['trade_id']
                self.active_trades[trade_id] = trade_result
                
                logger.info(f"  ✓ TRADE PLACED!")
                logger.info(f"    Trade ID: {trade_id}")
                logger.info(f"    Direction: {direction}")
                logger.info(f"    Amount: ${amount}")
                logger.info(f"    Expiration: {EXPIRATION_TIME}s")
                
                self.trade_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'trade_id': trade_id,
                    'status': 'open'
                })
            else:
                logger.error(f"  ✗ Failed to place trade: {trade_result.get('message')}")
        
        except Exception as e:
            logger.error(f"Error placing trade: {str(e)}")
    
    def stop(self):
        """Stop the trading bot"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("STOPPING TRADING BOT")
            logger.info("=" * 60)
            
            self.running = False
            
            if self.active_trades:
                logger.info(f"Closing {len(self.active_trades)} active trades...")
                for trade_id in list(self.active_trades.keys()):
                    self.quotex.close_trade(trade_id)
                    del self.active_trades[trade_id]
            
            self.quotex.disconnect()
            
            self._print_statistics()
            
            logger.info("✓ Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
    
    def _print_statistics(self):
        """Print trading statistics"""
        try:
            total_trades = len(self.trade_history)
            
            if total_trades == 0:
                logger.info("No trades executed")
                return
            
            logger.info("\n" + "=" * 60)
            logger.info("TRADING STATISTICS")
            logger.info("=" * 60)
            logger.info(f"Total Trades: {total_trades}")
            logger.info(f"Final Balance: ${self.quotex.get_balance():.2f}")
            
        except Exception as e:
            logger.error(f"Error printing statistics: {str(e)}")

def main():
    """Main entry point"""
    # Create bot with dashboard enabled
    bot = TradingBot(enable_dashboard=True, dashboard_port=5000)
    
    try:
        if bot.start():
            cycle_count = 0
            while bot.running:
                cycle_count += 1
                logger.info(f"\n🔄 Cycle {cycle_count}/{float('inf')}")
                
                bot.run_trading_cycle()
                
                logger.info(f"⏳ Waiting {TIMEFRAME}s for next candle...")
                time.sleep(TIMEFRAME)
        
    except KeyboardInterrupt:
        logger.info("\n⛔ Keyboard interrupt - shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        bot.stop()

if __name__ == "__main__":
    main()
