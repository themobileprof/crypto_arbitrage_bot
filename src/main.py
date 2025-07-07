import schedule
import time
from trading.arbitrage import ArbitrageTrader
from utils.file_handler import FileHandler
from config.settings import TRADING_INTERVAL, DASHBOARD_SECRET_KEY
import argparse
import sys

# Web dashboard import
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import os
from utils.db import TradeDB
import sqlite3
import requests
from utils.logger import logger

def check_network_connectivity():
    """Check if we can reach the exchange APIs"""
    test_urls = [
        'https://api.binance.com',
        'https://api.kucoin.com'
    ]
    
    logger.info("🌐 Checking network connectivity...")
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            logger.info(f"✅ {url} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {url} - Error: {e}")
            return False
    return True

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get_by_username(username):
        db = TradeDB()
        user = db.get_user_by_username(username)
        if user:
            return User(user[0], user[1], user[2])
        return None

    @staticmethod
    def get_by_id(user_id):
        db = TradeDB()
        user = db.get_user_by_id(user_id)
        if user:
            return User(user[0], user[1], user[2])
        return None

# Extend TradeDB for user management
setattr(TradeDB, 'init_user_table', lambda self: self._init_user_table())
def _init_user_table(self):
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )''')
        conn.commit()
setattr(TradeDB, '_init_user_table', _init_user_table)

def create_user(username, password):
    logger.info(f"👤 Creating user: {username}")
    db = TradeDB()
    db.init_user_table()
    password_hash = generate_password_hash(password)
    with sqlite3.connect(db.db_path) as conn:
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            logger.info(f"✅ User '{username}' created successfully.")
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ User '{username}' already exists.")

def get_user_by_username(self, username):
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        return c.fetchone()
setattr(TradeDB, 'get_user_by_username', get_user_by_username)

def get_user_by_id(self, user_id):
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT id, username, password_hash FROM users WHERE id = ?', (user_id,))
        return c.fetchone()
setattr(TradeDB, 'get_user_by_id', get_user_by_id)

def run_scheduler(trader, dry_run):
    logger.info(f"⏰ Starting scheduler with {TRADING_INTERVAL}s interval (DRY RUN: {dry_run})")
    
    def job():
        logger.info("🕐 Scheduled trade execution triggered")
        trader.execute_trade(dry_run=dry_run)
    
    schedule.every(TRADING_INTERVAL).seconds.do(job)
    logger.info(f"✅ Scheduler configured to run every {TRADING_INTERVAL} seconds")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_web_dashboard(trader, dry_run):
    logger.info("🌐 Starting web dashboard...")
    
    app = Flask(__name__)
    app.secret_key = DASHBOARD_SECRET_KEY
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    trade_logger = trader.trade_logger

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            logger.info(f"🔐 Login attempt for user: {username}")
            
            user = User.get_by_username(username)
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                logger.info(f"✅ Successful login for user: {username}")
                return redirect(url_for('dashboard'))
            else:
                logger.warning(f"❌ Failed login attempt for user: {username}")
                flash('Invalid username or password')
        return render_template_string('''
        <html><body>
        <h2>Login</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
        </form>
        {% with messages = get_flashed_messages() %}
          {% if messages %}<ul>{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>{% endif %}
        {% endwith %}
        </body></html>
        ''')

    @app.route('/logout')
    @login_required
    def logout():
        logger.info(f"👋 User logout: {current_user.username}")
        logout_user()
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def dashboard():
        logger.info(f"📊 Dashboard accessed by user: {current_user.username}")
        metrics = trade_logger.get_metrics()
        trades = trade_logger.get_trades(since_days=30)
        return render_template_string('''
        <html>
        <head><title>Crypto Arbitrage Dashboard</title></head>
        <body>
            <h1>Crypto Arbitrage Dashboard</h1>
            <a href="/logout">Logout</a>
            <form method="post" action="/run-trade">
                <button type="submit">Run Arbitrage Check</button>
            </form>
            <h2>Metrics (last 30 days)</h2>
            <ul>
                <li>Total Trades: {{ metrics.trade_count }}</li>
                <li>Total Profit: ${{ '%.2f' % metrics.total_profit }}</li>
                <li>Average Profit: ${{ '%.2f' % metrics.avg_profit }}</li>
            </ul>
            <h2>Trade History (last 30 days)</h2>
            <table border="1">
                <tr><th>Time</th><th>Binance Price</th><th>KuCoin Price</th><th>Difference</th><th>Profit</th><th>Result</th><th>Recommendation</th></tr>
                {% for trade in trades %}
                <tr>{% for item in trade[1:] %}<td>{{ item }}</td>{% endfor %}</tr>
                {% endfor %}
            </table>
        </body>
        </html>
        ''', metrics=metrics, trades=trades)

    @app.route('/run-trade', methods=['POST'])
    @login_required
    def run_trade():
        logger.info(f"🚀 Manual trade execution triggered by user: {current_user.username}")
        result = trader.execute_trade(dry_run=dry_run, return_data=True)
        return redirect(url_for('dashboard'))

    logger.info("✅ Web dashboard started successfully")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

def main():
    parser = argparse.ArgumentParser(description='Crypto Arbitrage Bot')
    parser.add_argument('--web', action='store_true', help='Run web dashboard')
    parser.add_argument('--dry-run', action='store_true', help='Simulate trades without executing them')
    parser.add_argument('--create-user', nargs=2, metavar=('username', 'password'), help='Create a dashboard user')
    parser.add_argument('--skip-network-check', action='store_true', help='Skip network connectivity check')
    parser.add_argument('--trading-interval', type=int, help='Override trading interval in seconds')
    args = parser.parse_args()

    # Override trading interval if specified
    global TRADING_INTERVAL
    if args.trading_interval:
        TRADING_INTERVAL = args.trading_interval
        logger.info(f"⏰ Trading interval overridden to {TRADING_INTERVAL} seconds")

    if args.create_user:
        username, password = args.create_user
        create_user(username, password)
        sys.exit(0)

    # Check network connectivity unless skipped
    if not args.skip_network_check:
        if not check_network_connectivity():
            logger.warning("⚠️ Network connectivity issues detected. The bot may not work properly.")
            logger.info("You can use --skip-network-check to bypass this check.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)

    logger.info("🧹 Clearing old log files...")
    FileHandler.clear_files()
    
    logger.info("🤖 Initializing ArbitrageTrader...")
    trader = ArbitrageTrader()

    if args.web:
        logger.info("🌐 Starting in web dashboard mode...")
        run_web_dashboard(trader, args.dry_run)
    else:
        logger.info("⏰ Starting in scheduler mode...")
        run_scheduler(trader, args.dry_run)

if __name__ == "__main__":
    main()