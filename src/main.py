import schedule
import time
from trading.arbitrage import ArbitrageTrader
from utils.file_handler import FileHandler
from config.settings import TRADING_INTERVAL

def main():
    # Clear existing logs and files
    FileHandler.clear_files()
    
    # Initialize trader
    trader = ArbitrageTrader()
    
    # Schedule trading job
    schedule.every(TRADING_INTERVAL).seconds.do(trader.execute_trade)
    
    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()