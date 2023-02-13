import math
import threading
from src.UnicornBinanceTrailingStopLossEngine import UnicornBinanceTrailingStopLossEngine
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
from src.BaseClass import BaseClass
from src.Config import Config
from datetime import datetime
import pandas as pd
import numpy as np
import logging
import time
import sys
import os


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
            self.price = 0.0
            self.engine = None
            if self.config.API_KEY is None or self.config.API_SECRET is None:
                self.exit_all(exit_code=0, exit_msg="Please provide API_KEY and API_SECRET")
            # initialize client object for api calls to server for data
            self.client = Client(api_key=self.config.API_KEY, api_secret=self.config.API_SECRET)

            binance_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")
            markets = {'btcusdt', 'bchusdt', 'ethusdt'}
            binance_websocket_api_manager.create_stream(["aggTrade"], markets)
            self.stdout(f"Started Websocket Manager ...")
            self.initialize_moving_averages('BTCUSDT')
            # start a worker process to move the received stream_data from the stream_buffer to a print function
            worker_thread = threading.Thread(target=self.print_stream_data_from_stream_buffer,
                                             args=(binance_websocket_api_manager,), daemon=True)
            worker_thread.start()

            ### for future use ###
            # self.engine = UnicornBinanceTrailingStopLossEngine(self.config.API_KEY, self.config.API_KEY, "BTCUSDT")
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.exit_all(exit_code=0)
        except Exception as e:
            self.stdout(f"Unknown Error in TrailingStopLossActivation Constructor - {e}", "CRITICAL",
                        print_enabled=True)
            self.exit_all(exit_code=0)

    def get_kline_volume(self, coinpair, time_interval, limit):
        try:
            kline_response = self.client.get_klines(symbol=coinpair, interval=time_interval, limit=limit)
            return kline_response
        except Exception as error_msg:
            self.stdout(f"Unknown Error in get_kline_volume() for {coinpair} - {error_msg} - "
                        f"Aborting...", "CRITICAL", True)
            self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")


    def initialize_moving_averages(self, coinpair):
        try:
            #make api call to server for candlestick data
            response = self.get_kline_volume(coinpair, self.config.CANDLESTICK_TIME_INTERVAL, self.config.MA_SLOW)
            #data preprocessing
            array_response = np.array(response)
            list_response = array_response[:, [0, 4]].tolist()  # subset by timestamp and 'close' fields
            df_prices = pd.DataFrame(list_response)
            df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp(
                (int(x) + 1) / 1e3))  # provide one millisecond and break down into fractions of a second
            df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
            df_prices.rename(columns={df_prices.columns[0]: "datetime", df_prices.columns[1]: "close"}, inplace=True)
            df_prices.set_index("datetime", inplace=True)
            #now ready to generate moving averages
            ma_fast = df_prices.ewm(span=self.config.MA_FAST, adjust=True).mean()
            ma_slow = df_prices.ewm(span=self.config.MA_SLOW, adjust=True).mean()
            fast_minus_slow = ma_fast - ma_slow
            print(f"fast moving average value: {ma_fast}")
            print(f"slow_moving_average_value: {ma_slow}")
            print(f"fast minus slow: {fast_minus_slow}")
        except Exception as error_msg:
            self.stdout(f"Unknown Error in initialize_moving_averages() for {coinpair} - {error_msg} - "
                        f"Aborting...", "CRITICAL", True)
            self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")


    def schedule_candlestick_df_update(self, coinpair):
        """
        scheduler method for binance kline api calls
        """
        # self.stdout(f"Process: {process_num}: Started async schedule_tick_df_update() for {tick.name}...")
        start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
        sleep_time = start_time - time.time()
        while True:
            try:
                time.sleep(sleep_time)
                start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
                sleep_time = start_time - time.time()
                self.update_candlestick_df(coinpair)
            except Exception as error_msg:
                self.stdout(f"Unknown Error in schedule_candlestick_df_update() for {coinpair} - {error_msg} - "
                            f"Aborting...",
                            "CRITICAL", True)
                self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

    def update_candlestick_df(self, coinpair):
        try:
            if self.price == 0.0:
                print(f"No price update for {coinpair} at {datetime.now()}")
        except Exception as error_msg:
            print(f"Error in update_candlestick_df() for {coinpair} - with df: {self.df} - {error_msg}")
        return


    def print_stream_data_from_stream_buffer(self, binance_websocket_api_manager):
        while True:
            if binance_websocket_api_manager.is_manager_stopping():
                self.exit_all(exit_code=0)
            oldest_stream_data_from_stream_buffer = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
            if oldest_stream_data_from_stream_buffer is False:
                time.sleep(0.01)
                continue
            print(oldest_stream_data_from_stream_buffer)

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
            if self.engine:
                self.engine.ubtsl.stop_manager()
            sys.exit(exit_code)
        except Exception as e:
            self.stdout(f"Unknown Error in exit_all() - {e}", "CRITICAL", print_enabled=True)
