import logging
import os

def setup_logger():
    logging.basicConfig(
        filename='crypto_arbitrage_bot.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logger()
