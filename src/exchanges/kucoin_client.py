import ccxt
from src.config.settings import KUCOIN_API_KEY, KUCOIN_API_SECRET, KUCOIN_API_PASSPHRASE
from src.utils.logger import logger

class KuCoinHandler:
    def __init__(self):
        self.client = ccxt.kucoin({
            'apiKey': KUCOIN_API_KEY,
            'secret': KUCOIN_API_SECRET,
            'password': KUCOIN_API_PASSPHRASE,
        })

    def get_btc_price(self):
        try:
            ticker = self.client.fetch_ticker('BTC/USDT')
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Error fetching KuCoin BTC price: {e}")
            return None

    def check_balance(self):
        try:
            balance = self.client.fetch_balance()
            return balance['total'].get('BTC', 0.0)
        except Exception as e:
            logger.error(f"Error fetching KuCoin balance: {e}")
            return 0.0

    def place_sell_order(self, symbol, quantity):
        try:
            order = self.client.create_order(
                symbol=symbol,
                type='market',
                side='sell',
                amount=quantity
            )
            logger.info(f"Sell order placed on KuCoin: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing sell order on KuCoin: {e}")
            return None
