"""
Dashboard Server - Flask-based Web Interface
Provides real-time visualization of bot activity
"""

import logging
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import sqlite3
from threading import Thread
import os

logger = logging.getLogger(__name__)

class DashboardServer:
    """Flask dashboard server for bot visualization"""
    
    def __init__(self, db_file="data/trading_bot.db", port=5000):
        """Initialize dashboard"""
        self.app = Flask(__name__)
        self.app.config['JSON_SORT_KEYS'] = False
        CORS(self.app)
        
        self.db_file = db_file
        self.port = port
        self.bot_instance = None
        self.running = False
        
        self._setup_routes()
        logger.info(f"Dashboard server initialized on port {port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return self.get_dashboard_html()
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get trading statistics"""
            return jsonify(self._get_statistics())
        
        @self.app.route('/api/trades')
        def get_trades():
            """Get recent trades"""
            limit = request.args.get('limit', 50, type=int)
            return jsonify(self._get_recent_trades(limit))
        
        @self.app.route('/api/balance')
        def get_balance():
            """Get current balance"""
            if self.bot_instance and self.bot_instance.quotex.is_connected():
                balance = self.bot_instance.quotex.get_balance()
            else:
                balance = 0
            return jsonify({"balance": balance})
        
        @self.app.route('/api/active-trades')
        def get_active():
            """Get active trades"""
            if self.bot_instance:
                return jsonify({
                    "count": len(self.bot_instance.active_trades),
                    "trades": list(self.bot_instance.active_trades.values())
                })
            return jsonify({"count": 0, "trades": []})
        
        @self.app.route('/api/predictions')
        def get_predictions():
            """Get recent predictions"""
            return jsonify(self._get_recent_predictions(20))
        
        @self.app.route('/api/candles/<asset>')
        def get_candles(asset):
            """Get candle data for chart"""
            return jsonify(self._get_candle_data(asset))
        
        @self.app.route('/api/performance')
        def get_performance():
            """Get performance metrics"""
            return jsonify(self._get_performance_metrics())
    
    def _get_statistics(self):
        """Get overall trading statistics"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Total trades
            cursor.execute('SELECT COUNT(*) as count FROM trades WHERE status = "closed"')
            total_trades = cursor.fetchone()['count'] or 0
            
            # Wins
            cursor.execute('SELECT COUNT(*) as count FROM trades WHERE status = "closed" AND win = 1')
            wins = cursor.fetchone()['count'] or 0
            
            # Losses
            losses = total_trades - wins
            
            # Total P&L
            cursor.execute('SELECT SUM(profit_loss) as total FROM trades WHERE status = "closed"')
            result = cursor.fetchone()
            total_pl = result['total'] if result['total'] else 0
            
            # Win rate
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            conn.close()
            
            return {
                "total_trades": total_trades,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 2),
                "total_profit_loss": round(total_pl, 2),
                "avg_profit_per_trade": round(total_pl / total_trades, 2) if total_trades > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "total_profit_loss": 0,
                "avg_profit_per_trade": 0
            }
    
    def _get_recent_trades(self, limit=50):
        """Get recent trades"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM trades 
                ORDER BY entry_time DESC 
                LIMIT ?
            ''', (limit,))
            
            trades = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return trades
        except Exception as e:
            logger.error(f"Error getting trades: {str(e)}")
            return []
    
    def _get_recent_predictions(self, limit=20):
        """Get recent predictions"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM predictions 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            predictions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return predictions
        except Exception as e:
            logger.error(f"Error getting predictions: {str(e)}")
            return []
    
    def _get_candle_data(self, asset):
        """Get candle data for chart"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, open, high, low, close 
                FROM candles 
                WHERE asset = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''', (asset,))
            
            candles = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Reverse to get chronological order
            return list(reversed(candles))
        except Exception as e:
            logger.error(f"Error getting candles: {str(e)}")
            return []
    
    def _get_performance_metrics(self):
        """Get detailed performance metrics"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Performance by asset
            cursor.execute('''
                SELECT asset, 
                       COUNT(*) as trades,
                       SUM(CASE WHEN win=1 THEN 1 ELSE 0 END) as wins,
                       SUM(profit_loss) as profit
                FROM trades 
                WHERE status = "closed"
                GROUP BY asset
            ''')
            
            by_asset = []
            for row in cursor.fetchall():
                win_rate = (row['wins'] / row['trades'] * 100) if row['trades'] > 0 else 0
                by_asset.append({
                    "asset": row['asset'],
                    "trades": row['trades'],
                    "wins": row['wins'],
                    "win_rate": round(win_rate, 2),
                    "profit": round(row['profit'] or 0, 2)
                })
            
            # Performance by direction
            cursor.execute('''
                SELECT direction,
                       COUNT(*) as trades,
                       SUM(CASE WHEN win=1 THEN 1 ELSE 0 END) as wins
                FROM trades
                WHERE status = "closed"
                GROUP BY direction
            ''')
            
            by_direction = []
            for row in cursor.fetchall():
                win_rate = (row['wins'] / row['trades'] * 100) if row['trades'] > 0 else 0
                by_direction.append({
                    "direction": row['direction'],
                    "trades": row['trades'],
                    "wins": row['wins'],
                    "win_rate": round(win_rate, 2)
                })
            
            conn.close()
            
            return {
                "by_asset": by_asset,
                "by_direction": by_direction
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {"by_asset": [], "by_direction": []}
    
    def get_dashboard_html(self):
        """Return HTML for dashboard"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quotex AI Trading Bot - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 10px;
            border: 2px solid #00ff88;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #00ff88;
        }
        
        .header p {
            font-size: 1.1em;
            color: #aaa;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: #00ff88;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
            transform: translateY(-5px);
        }
        
        .card-title {
            font-size: 0.9em;
            color: #aaa;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }
        
        .card-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }
        
        .card-sub {
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
        }
        
        .stat-positive {
            color: #00ff88;
        }
        
        .stat-negative {
            color: #ff4444;
        }
        
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .status.connected {
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
        }
        
        .status.disconnected {
            background: rgba(255, 68, 68, 0.2);
            color: #ff4444;
        }
        
        .status.trading {
            background: rgba(0, 150, 255, 0.2);
            color: #00aaff;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .chart-container h3 {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
        }
        
        table thead {
            background: rgba(0, 255, 136, 0.2);
        }
        
        table th, table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(0, 255, 136, 0.1);
        }
        
        table th {
            color: #00ff88;
            font-weight: bold;
        }
        
        table tr:hover {
            background: rgba(0, 255, 136, 0.1);
        }
        
        .trade-win {
            color: #00ff88;
        }
        
        .trade-loss {
            color: #ff4444;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #aaa;
        }
        
        .spinner {
            border: 3px solid rgba(0, 255, 136, 0.2);
            border-top: 3px solid #00ff88;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .refresh-info {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Quotex AI Trading Bot</h1>
            <p>Real-time Dashboard & Analytics</p>
        </div>
        
        <!-- Key Metrics -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Current Balance</div>
                <div class="card-value" id="balance">$1000.00</div>
                <div class="card-sub">Starting: $1000</div>
            </div>
            
            <div class="card">
                <div class="card-title">Total Trades</div>
                <div class="card-value" id="total-trades">0</div>
                <div class="card-sub"><span id="trade-ratio">0W / 0L</span></div>
            </div>
            
            <div class="card">
                <div class="card-title">Win Rate</div>
                <div class="card-value stat-positive" id="win-rate">0%</div>
                <div class="card-sub">Success percentage</div>
            </div>
            
            <div class="card">
                <div class="card-title">Total P&L</div>
                <div class="card-value" id="total-pl">$0.00</div>
                <div class="card-sub">Profit/Loss</div>
            </div>
            
            <div class="card">
                <div class="card-title">Avg Trade</div>
                <div class="card-value" id="avg-trade">$0.00</div>
                <div class="card-sub">Per trade average</div>
            </div>
            
            <div class="card">
                <div class="card-title">Active Trades</div>
                <div class="card-value" id="active-trades">0</div>
                <div class="card-sub">Currently open</div>
            </div>
        </div>
        
        <!-- Status -->
        <div style="margin-bottom: 30px; text-align: center;">
            <span class="status connected">✓ Connected</span>
            <span class="status trading">⏱ Trading Active</span>
            <span class="status" style="background: rgba(100, 150, 200, 0.2); color: #00aaff;">🔄 Last Updated: <span id="last-update">--:--:--</span></span>
        </div>
        
        <!-- Charts -->
        <div class="charts-grid">
            <div class="chart-container">
                <h3>Performance by Asset</h3>
                <canvas id="assetChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h3>Call vs Put Success</h3>
                <canvas id="directionChart"></canvas>
            </div>
        </div>
        
        <!-- Recent Trades -->
        <h2 style="color: #00ff88; margin: 30px 0 20px 0;">📊 Recent Trades</h2>
        <div id="trades-table">
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading trades...</p>
            </div>
        </div>
        
        <div class="refresh-info">
            Dashboard updates every 5 seconds • Open this page in multiple tabs to monitor simultaneously
        </div>
    </div>
    
    <script>
        let assetChart, directionChart;
        
        async function updateDashboard() {
            try {
                // Get stats
                const statsRes = await fetch('/api/stats');
                const stats = await statsRes.json();
                
                // Update main metrics
                document.getElementById('balance').textContent = '$' + stats.total_profit_loss.toFixed(2);
                document.getElementById('total-trades').textContent = stats.total_trades;
                document.getElementById('trade-ratio').textContent = stats.wins + 'W / ' + stats.losses + 'L';
                document.getElementById('win-rate').textContent = stats.win_rate + '%';
                document.getElementById('total-pl').textContent = '$' + stats.total_profit_loss.toFixed(2);
                document.getElementById('avg-trade').textContent = '$' + stats.avg_profit_per_trade.toFixed(2);
                
                // Update active trades
                const activeRes = await fetch('/api/active-trades');
                const active = await activeRes.json();
                document.getElementById('active-trades').textContent = active.count;
                
                // Update trades table
                const tradesRes = await fetch('/api/trades?limit=20');
                const trades = await tradesRes.json();
                updateTradesTable(trades);
                
                // Update performance charts
                const perfRes = await fetch('/api/performance');
                const performance = await perfRes.json();
                updateCharts(performance);
                
                // Update timestamp
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }
        
        function updateTradesTable(trades) {
            let html = '<table><thead><tr>';
            html += '<th>Time</th>';
            html += '<th>Asset</th>';
            html += '<th>Direction</th>';
            html += '<th>Amount</th>';
            html += '<th>Result</th>';
            html += '<th>P&L</th>';
            html += '</tr></thead><tbody>';
            
            if (trades.length === 0) {
                html += '<tr><td colspan="6" style="text-align: center; color: #666;">No trades yet</td></tr>';
            } else {
                trades.forEach(trade => {
                    const time = new Date(trade.entry_time).toLocaleTimeString();
                    const resultClass = trade.win ? 'trade-win' : 'trade-loss';
                    const resultText = trade.win ? '✓ WIN' : '✗ LOSS';
                    const plText = '$' + (trade.profit_loss || 0).toFixed(2);
                    const plClass = (trade.profit_loss || 0) >= 0 ? 'stat-positive' : 'stat-negative';
                    
                    html += '<tr>';
                    html += '<td>' + time + '</td>';
                    html += '<td><strong>' + trade.asset + '</strong></td>';
                    html += '<td>' + trade.direction.toUpperCase() + '</td>';
                    html += '<td>$' + trade.amount.toFixed(2) + '</td>';
                    html += '<td class="' + resultClass + '"><strong>' + resultText + '</strong></td>';
                    html += '<td class="' + plClass + '"><strong>' + plText + '</strong></td>';
                    html += '</tr>';
                });
            }
            
            html += '</tbody></table>';
            document.getElementById('trades-table').innerHTML = html;
        }
        
        function updateCharts(performance) {
            // Asset performance chart
            const assetLabels = performance.by_asset.map(a => a.asset);
            const assetWinRates = performance.by_asset.map(a => a.win_rate);
            
            if (assetChart) assetChart.destroy();
            
            assetChart = new Chart(document.getElementById('assetChart'), {
                type: 'bar',
                data: {
                    labels: assetLabels.length > 0 ? assetLabels : ['No Data'],
                    datasets: [{
                        label: 'Win Rate (%)',
                        data: assetWinRates.length > 0 ? assetWinRates : [0],
                        backgroundColor: 'rgba(0, 255, 136, 0.5)',
                        borderColor: '#00ff88',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { color: '#aaa' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: { ticks: { color: '#aaa' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#aaa' } }
                    }
                }
            });
            
            // Direction chart
            const dirLabels = performance.by_direction.map(d => d.direction.toUpperCase());
            const dirWins = performance.by_direction.map(d => d.wins);
            
            if (directionChart) directionChart.destroy();
            
            directionChart = new Chart(document.getElementById('directionChart'), {
                type: 'doughnut',
                data: {
                    labels: dirLabels.length > 0 ? dirLabels : ['No Data'],
                    datasets: [{
                        data: dirWins.length > 0 ? dirWins : [0],
                        backgroundColor: [
                            'rgba(0, 255, 136, 0.7)',
                            'rgba(255, 100, 100, 0.7)'
                        ],
                        borderColor: ['#00ff88', '#ff6464'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { labels: { color: '#aaa' } }
                    }
                }
            });
        }
        
        // Update dashboard every 5 seconds
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
        '''
    
    def run(self, debug=False, bot_instance=None):
        """Run the dashboard server"""
        self.bot_instance = bot_instance
        self.running = True
        logger.info(f"Starting Dashboard at http://localhost:{self.port}")
        self.app.run(debug=debug, host='0.0.0.0', port=self.port, use_reloader=False)

# Usage in bot.py
if __name__ == "__main__":
    dashboard = DashboardServer(port=5000)
    dashboard.run(debug=False)
