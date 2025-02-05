from dotenv import load_dotenv
import os

load_dotenv()

def get_env_var(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Please set the {var_name} environment variable")
    return value

# Exchange API credentials
BINANCE_API_KEY = get_env_var('BINANCE_API_KEY')
BINANCE_API_SECRET = get_env_var('BINANCE_API_SECRET')
KUCOIN_API_KEY = get_env_var('KUCOIN_API_KEY')
KUCOIN_API_SECRET = get_env_var('KUCOIN_API_SECRET')
KUCOIN_API_PASSPHRASE = get_env_var('KUCOIN_API_PASSPHRASE')

# Trading parameters
TRADING_CAPITAL = 50
ALLOCATION_PERCENTAGE = 50
ARBITRAGE_THRESHOLD = 10
STOP_LOSS_THRESHOLD = -5
TRADING_INTERVAL = 5  # seconds
