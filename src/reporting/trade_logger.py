from datetime import datetime
from utils.file_handler import FileHandler
from tabulate import tabulate

class TradeLogger:
    def __init__(self):
        self.file_handler = FileHandler()
        self.headers = ["Time", "Binance Price", "KuCoin Price", 
                       "Difference", "Profit", "Result", "Recommendation"]

    def log_trade(self, time, binance_price, kucoin_price, difference, profit):
        result = "Successful" if profit >= 0.01 else "Failed"
        recommendation = ('Buy on KuCoin and sell on Binance' 
                         if binance_price > kucoin_price 
                         else 'Buy on Binance and sell on KuCoin')

        data = [
            time.strftime('%Y-%m-%d %H:%M:%S'),
            f'${binance_price}',
            f'${kucoin_price}',
            f'${difference:.2f}',
            f'${profit:.2f}',
            result,
            recommendation
        ]

        # Print results in table format
        table_data = [self.headers, data]
        print(tabulate(table_data, headers="firstrow", tablefmt="grid"))

        # Save to different log files
        self.file_handler.save_to_csv('daily_trades.csv', data, self.headers)
        self.file_handler.save_to_csv(
            f'weekly_trades_week_{datetime.now().isocalendar()[1]}.csv', 
            data, self.headers)
        self.file_handler.save_to_csv(
            f'monthly_trades_{datetime.now().strftime("%Y-%m")}.csv', 
            data, self.headers)
