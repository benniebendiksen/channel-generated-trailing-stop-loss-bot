from src.UnicornBinanceTrailingStopLossEngine import UnicornBinanceTrailingStopLossEngine
from src.Config import Config
from src.BaseClass import BaseClass
from binance.client import Client
import logging
import time
import sys
import os


class TrailingStopLossActivation(BaseClass):
    logging.getLogger("unicorn_binance_trailing_stop_loss.unicorn_binance_trailing_stop_loss_engine_manager")
    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.basename(__file__) + '.log',
                        format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                        style="{")

    def __init__(self):
        self.stdout(f"Starting new instance of trend-activated-bot ...")
        self.config = Config()
        self.engine = None
        if self.config.API_KEY is None or self.config.API_SECRET is None:
            self.exit_all(exit_code=0, exit_msg="Please provide API_KEY and API_SECRET")
        self.client = Client(api_key=self.config.API_KEY, api_secret=self.config.API_SECRET)
        self.engine = UnicornBinanceTrailingStopLossEngine(self.config.API_KEY, self.config.API_KEY, "BTCUSD")
        self.stdout(f"instantiated Stop Loss Engine ...")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.exit_all(exit_code=0)

    def exit_all(self, exit_msg: str = "", exit_code: int = 1):
        """
        Exit bot cycle
        :param exit_msg: This gets added to the stdout string
        :param exit_code: Exit code for sys.exit() 0=success exit for bot cycle, 1=success exit for system, 2 to
        255=anything else
        """
        self.stdout(f"Stopping ... please wait a few seconds!\n{exit_msg}", "CRITICAL")
        self.stop_request = True
        try:
            if self.engine:
                self.engine.ubtsl.stop_manager()
            sys.exit(exit_code)
        except Exception as e:
            self.stdout(f"Unknown Error in exit_all() - {e}", "CRITICAL", print_enabled=True)
