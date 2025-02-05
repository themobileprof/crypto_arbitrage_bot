from src.config.settings import TRADING_CAPITAL, ALLOCATION_PERCENTAGE, STOP_LOSS_THRESHOLD

class PositionManager:
    @staticmethod
    def calculate_position_size(capital=TRADING_CAPITAL, 
                              allocation_percentage=ALLOCATION_PERCENTAGE):
        if allocation_percentage < 0 or allocation_percentage > 100:
            raise ValueError("Allocation percentage should be between 0 and 100.")
        return capital * (allocation_percentage / 100)

    @staticmethod
    def calculate_fees(price, exchange):
        fee_rate = 0.001  # 0.1% fee
        return price * fee_rate

    @staticmethod
    def calculate_profit(binance_price, kucoin_price, quantity):
        binance_fee = PositionManager.calculate_fees(binance_price, 'Binance')
        kucoin_fee = PositionManager.calculate_fees(kucoin_price, 'KuCoin')
        
        if binance_price > kucoin_price:
            profit = (binance_price - (kucoin_price * (1 + kucoin_fee))) * quantity
        else:
            profit = (kucoin_price - (binance_price * (1 + binance_fee))) * quantity
            
        return profit

    @staticmethod
    def check_stop_loss(current_profit_loss, threshold=STOP_LOSS_THRESHOLD):
        return current_profit_loss <= threshold
