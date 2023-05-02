import math
import threading

from src.UnicornBinanceTrailingStopLossEngine import UnicornBinanceTrailingStopLossEngine
from src.BaseClass import BaseClass
from src.Config import Config
from src.Indicators import Indicators
from src.CoinPair import CoinPair
from src.Strategy import Strategy
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
from datetime import datetime
import pandas as pd
import numpy as np
import json
import asyncio
import logging
import time
import sys
import os

socks5_proxy = None
socks5_user = None
socks5_pass = None
socks5_ssl_verification = True
BASE_URL = "https://fapi.binance.com"


class TrailingStopLossActivation(BaseClass):
    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.basename(__file__) + '.log',
                        format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                        style="{")
    logging.getLogger("unicorn_binance_trailing_stop_loss")

    def __init__(self):
        try:
            self.stdout(f"Starting new instance of trend-activated-bot ...")
            self.config = Config()
            socks5_proxy = self.config.SOCKS5_IP_PORT
            self.stop_request = False
            self.engine = None
            self.ubwa_manager = None
            self.markets = ["".join(market.split("_")) for market in self.config.MARKETS]
            self.Coinpairs_dict = {market + '@' + 'aggTrade': CoinPair(self, market + '@' + 'aggTrade') for market in \
                                   self.markets}
            self.all_tasks_list = []
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            if self.config.API_KEY is None or self.config.API_SECRET is None:
                self.exit_all(exit_code=0, exit_msg="Please provide API_KEY and API_SECRET")
            # initialize client object for api calls to server for data
            self.client = Client(api_key=self.config.API_KEY, api_secret=self.config.API_SECRET,
                                 exchange="binance.com-futures",
                                 socks5_proxy_server=socks5_proxy,
                                 socks5_proxy_user=socks5_user,
                                 socks5_proxy_pass=socks5_pass,
                                 socks5_proxy_ssl_verification=socks5_ssl_verification)
            self.strategy = Strategy(self.client)
            klines_1m = self.client.futures_klines(symbol="BTCUSDT", interval="1m", limit=1500)
            print(self.strategy.create_df(klines_1m))
            # IP weight limit is 1200/min. klines limit 1000 = 5 weight, limit 1500 = 10
            print(self.client.response.headers['X-MBX-USED-WEIGHT-1M'])
            # # print(self.client.futures_account_balance())
            # print(self.client.futures_exchange_info()['rateLimits'])
            # self.client.create_order(symbol='ETHUSDT', side="BUY", quantity=2, stopPrice='2000', type='STOP_LOSS')
            self.stdout(f"Starting Unicorn Binance Websocket Manager ...")
            # self.ubwa_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")
            # self.ubwa_manager.create_stream("aggTrade", self.markets, output="UnicornFy")
            # self.indicators = Indicators(self, self.config, self.client, self.Coinpairs_dict.values(),
            # self.event_loop)
            # self.event_loop.create_task(self.process_stream_data_from_stream_buffer(self.ubwa_manager))
            self.event_loop.run_until_complete(self.main_loop())
        except KeyboardInterrupt:
            self.exit_all(exit_code=0)
        except Exception as e:
            self.stdout(f"Unknown Error in TrailingStopLossActivation Constructor - {e}", "CRITICAL",
                        print_enabled=True)
            self.exit_all(exit_code=0)

    async def main_loop(self):
        sleep_counter = 0
        self.stdout(f"Started Main Loop")
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            self.tsla.exit_all(exit_code=0)

    def exit_all(self, exit_msg: str = "", exit_code: int = 1):
        """
        Exit bot cycle
        :param exit_msg: This gets added to the stdout string
        :param exit_code: Exit code for sys.exit() 0=success exit for system, 1=success exit for bot cycle, 2 to
        255=anything else
        """
        self.stdout(f"Stopping ... please wait a few seconds!\n{exit_msg}", "CRITICAL")
        self.stop_request = True
        try:
            if self.engine is not None:
                self.engine.ubtsl.stop_manager()
            if self.ubwa_manager is not None:
                self.ubwa_manager.stop_manager_with_all_streams()
            time.sleep(3)
            sys.exit(exit_code)
        except Exception as e:
            self.stdout(f"Unknown Error in exit_all() - {e}", "CRITICAL", print_enabled=True)

    def is_stopping(self):
        """
        Is there a stop request?

        :return: bool
        """
        return self.stop_request

    async def process_stream_data_from_stream_buffer(self, binance_websocket_api_manager):
        while self.is_stopping() is False:
            if binance_websocket_api_manager.is_manager_stopping():
                self.exit_all(exit_code=0)
            oldest_stream_data = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
            if oldest_stream_data is False:
                await asyncio.sleep(0.01)
            else:
                try:
                    Coinpair = self.Coinpairs_dict[oldest_stream_data.get("stream_type")]
                    self.indicators.perform_indicator_updates(oldest_stream_data, Coinpair)
                except Exception as error:
                    # Result of None expected when websocket first establishing connection
                    if 'result' in oldest_stream_data:
                        if oldest_stream_data['result'] is None:
                            continue
                    else:
                        self.stdout(f"Unknown Error in process_stream_data_from_stream_buffer() -"
                                    f" {oldest_stream_data} -"
                                    f" {error} - "
                                    f"Aborting...",
                                    "CRITICAL", True)
                        self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
