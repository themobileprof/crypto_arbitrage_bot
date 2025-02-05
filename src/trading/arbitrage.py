from datetime import datetime
from src.exchanges.binance_client import BinanceHandler
from src.exchanges.kucoin_client import KuCoinHandler
from src.trading.position import PositionManager
from src.reporting.trade_logger import TradeLogger
from src.config.settings import ARBITRAGE_THRESHOLD
from src.utils.logger import logger

class ArbitrageTrader:
    def __init__(self):
        self.binance = BinanceHandler()
        self.kucoin = KuCoinHandler()
        self.position_manager = PositionManager()
        self.trade_logger = TradeLogger()

    def check_arbitrage_opportunity(self, binance_price, kucoin_price, 
                                  threshold=ARBITRAGE_THRESHOLD):
        if not all([binance_price, kucoin_price]):
            return False
        
        difference = abs(binance_price - kucoin_price)
        if difference >= threshold:
            logger.info(f'Arbitrage opportunity detected! '
                       f'Binance: ${binance_price}, KuCoin: ${kucoin_price}, '
                       f'Difference: ${difference:.2f}')
            return True
        return False

    def execute_trade(self):
        try:
            binance_price = self.binance.get_btc_price()
            kucoin_price = self.kucoin.get_btc_price()

            if not all([binance_price, kucoin_price]):
                logger.error("Failed to fetch prices from one or both exchanges")
                return

            if self.check_arbitrage_opportunity(binance_price, kucoin_price):
                quantity = self.position_manager.calculate_position_size()
                profit = self.position_manager.calculate_profit(
                    binance_price, kucoin_price, quantity)

                if self.position_manager.check_stop_loss(profit):
                    logger.info('Stop-loss triggered!')
                    return

                self.trade_logger.log_trade(
                    datetime.now(), binance_price, kucoin_price, 
                    abs(binance_price - kucoin_price), profit)

        except Exception as e:
            logger.error(f"Error in execute_trade: {e}")

