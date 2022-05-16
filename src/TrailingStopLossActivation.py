from src.UnicornBinanceTrailingStopLossEngine import UnicornBinanceTrailingStopLossEngine
from binance.client import Client
import logging
import os

class TrailingStopLossActivation:
    logging.getLogger("unicorn_binance_trailing_stop_loss.unicorn_binance_trailing_stop_loss_engine_manager")
    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.basename(__file__) + '.log',
                        format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                        style="{")
    def __init__(self):
        API_KEY = os.environ.get('API_KEY_2')
        API_SECRET = os.environ.get('API_SECRET_2')
        self.client = Client(api_key=API_KEY, api_secret=API_SECRET)
        self.engine = UnicornBinanceTrailingStopLossEngine(API_KEY, API_SECRET, "LUNABUSD")
        self.engine.ubtsl.stop_manager()
