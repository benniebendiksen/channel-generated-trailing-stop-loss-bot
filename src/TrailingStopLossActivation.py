import math
import threading

from src.UnicornBinanceTrailingStopLossEngine import UnicornBinanceTrailingStopLossEngine
from src.BaseClass import BaseClass
from src.Config import Config
from src.Indicators import Indicators
from src.CoinPair import CoinPair
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
from datetime import datetime
import paramiko
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import pandas as pd
import numpy as np
import json
import asyncio
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
            self.stop_request = False
            self.engine = None
            self.ubwa_manager = None
            self.Coinpairs_dict = {market + '@' + 'aggTrade': CoinPair(self, market + '@' + 'aggTrade') for market in \
                                   self.config.MARKETS}
            self.all_tasks_list = []
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            if self.config.API_KEY is None or self.config.API_SECRET is None:
                self.exit_all(exit_code=0, exit_msg="Please provide API_KEY and API_SECRET")
            # initialize client object for api calls to server for data
            # self.client = Client(api_key=self.config.API_KEY, api_secret=self.config.API_SECRET)
            self.stdout(f"Starting Unicorn Binance Websocket Manager ...")
            self.ubwa_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")
            self.ubwa_manager.create_stream("aggTrade", self.config.MARKETS, output="UnicornFy")
            self.indicators = Indicators(self, self.config, self.Coinpairs_dict.values(), self.event_loop)
            # threading.Thread(target=self.process_stream_data_from_stream_buffer,
            #                  args=(binance_websocket_api_manager,), daemon=True).start()
            self.event_loop.create_task(self.process_stream_data_from_stream_buffer(self.ubwa_manager))
            self.event_loop.run_until_complete(self.main_loop())
            # self.initialize_macd("BTCUSDT")
            # # start a thread to update candlestick df and another to process stream data
            # threading.Thread(target=self.schedule_candlestick_df_update, args=("BTCUSDT",), daemon=True).start()
            # threading.Thread(target=self.process_stream_data_from_stream_buffer,
            #                  args=(binance_websocket_api_manager, "BTCUSDT"), daemon=True).start()
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

    # def get_kline_volume(self, coinpair, time_interval, limit):
    #     try:
    #         kline_response = self.client.get_klines(symbol=coinpair, interval=time_interval, limit=limit)
    #         return kline_response
    #     except Exception as error_msg:
    #         self.stdout(f"Unknown Error in get_kline_volume() for {coinpair} - {error_msg} - "
    #                     f"Aborting...", "CRITICAL", True)
    #         self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

    # def initialize_macd(self, coinpair):
    #     try:
    #         # make api call to server for candlestick data
    #         # response = self.get_kline_volume(coinpair, self.config.CANDLESTICK_TIME_INTERVAL, self.config.MA_SLOW)
    #         # #data preprocessing
    #         # array_response = np.array(response)
    #         # list_response = array_response[:, [0, 4]].tolist()  # subset by timestamp and 'close' fields
    #         # df_prices = pd.DataFrame(list_response) # convert to dataframe
    #         df_prices = self.fetchRemoteClientDataFrameWithArgs()
    #         df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp(
    #             (int(x) + 1) / 1e3))  # provide one millisecond and break down into fractions of a second
    #         df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
    #         df_prices.rename(columns={df_prices.columns[0]: "datetime", df_prices.columns[1]: "close"}, inplace=True)
    #         df_prices.set_index("datetime", inplace=True)
    #         # now ready to generate moving averages
    #         signals = self._generate_signals(df_prices, 'Null')
    #         if signals['macd_line'][-1] > signals['signal_line'][-1]:
    #             trend_direction = "UP"
    #         elif signals['macd_line'][-1] < signals['signal_line'][-1]:
    #             trend_direction = "DOWN"
    #         self.trend_direction = trend_direction
    #         self.price = df_prices.iloc[4, 0]
    #         self.df_prices = df_prices
    #     except Exception as error_msg:
    #         self.stdout(f"Unknown Error in initialize_moving_averages() for {coinpair} - {error_msg} - "
    #                     f"Aborting...", "CRITICAL", True)
    #         self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
    #
    # def fetchRemoteClientDataFrameWithArgs(self, coinpair="BTCUSDT", candle_time_interval = '1m', num_candles = 5, st='-1.0', et='-1.0'):
    #     try:
    #         user = 'ec2-user'
    #         pri_key = paramiko.RSAKey.from_private_key_file(
    #             self.config.REMOTE_KEYS_PATH)
    #         if st == '-1.0' or et == '-1.0':
    #             cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py ' + coinpair + ' ' + \
    #                   str(candle_time_interval) + ' ' + \
    #                   str(num_candles)
    #
    #         else:
    #             print("startTime:" + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
    #             print(datetime.fromtimestamp(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()))
    #             print("endTime:" + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
    #             print(datetime.fromtimestamp(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()))
    #             cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py ' + coinpair + ' ' \
    #                   + str(candle_time_interval) + ' ' \
    #                   + str(num_candles) + ' ' \
    #                   + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' ' \
    #                   + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' '
    #         s = SSHClient()
    #         s.set_missing_host_key_policy(AutoAddPolicy())
    #         print("[+] Start ssh into:" + self.config.REMOTE_ADDRESS)
    #         s.connect(hostname=self.config.REMOTE_ADDRESS, username=user, pkey=pri_key)
    #         print("[+] SSH established !")
    #         print(f"[+] running following command remotely: {cmd}")
    #         stdin, stdout, stderr = s.exec_command(cmd)
    #         tempJSON_str = stdout.read().decode('ascii')
    #         print(f"[+] read following output from remote: {tempJSON_str}")
    #         temp_json_file = open("df_prices_returned.json", "wt")
    #         n = temp_json_file.write(tempJSON_str)
    #         temp_json_file.close()
    #         s.close()
    #         tempPD = pd.read_json('df_prices_returned.json', orient='split')
    #         if stderr.read() != None:
    #             print("[+] error: ")
    #             print(stderr.read())
    #         return tempPD
    #     except Exception as e:
    #         self.stdout(f"Unknown Error in fetch_remote_client_dataframe() - {e} - "
    #                     f"Aborting...", "CRITICAL", True)
    #         self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
    #     finally:
    #         s.close()
    #
    # def _generate_signals(self, df, name):
    #     """
    #     Generate macd_line as well as signal_line for a given dataframe
    #     """
    #     try:
    #         ma_fast = df.ewm(span=self.config.MA_FAST, adjust=True).mean()
    #         ma_slow = df.ewm(span=self.config.MA_SLOW, adjust=True).mean()
    #         macd = ma_fast - ma_slow
    #         # print(f"MACD 1 {macd} for {name}")
    #         macd['fast'] = ma_fast
    #         macd['slow'] = ma_slow
    #         macd['signal_line'] = macd.close.ewm(span=self.config.SIGNAL_LENGTH).mean()
    #         # print(f"MACD 2 {macd} for {name}")
    #         signals = pd.DataFrame(index=macd.index)
    #         signals['macd_line'] = macd['close']
    #         signals['signal_line'] = macd['signal_line']
    #         signals['MACD-Signal'] = signals['macd_line'] - signals['signal_line']
    #         return signals
    #     except IndexError as i:
    #         print(f"INDEXERROR: {i} for {name} with ticks: {df}")
    #     except Exception as e:
    #         self.stdout(f"Unknown Error in _generate_signals() for {name} - {e} - "
    #                     f"Aborting...", "CRITICAL", True)
    #         self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
    #
    # def schedule_candlestick_df_update(self, coinpair):
    #     """
    #     scheduler method for updating the candlestick_df
    #     """
    #     # self.stdout(f"Process: {process_num}: Started async schedule_tick_df_update() for {tick.name}...")
    #     start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
    #     sleep_time = start_time - time.time()
    #     while self.is_stopping() is False:
    #         try:
    #             time.sleep(sleep_time)
    #             start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
    #             sleep_time = start_time - time.time()
    #             self._update_candlestick_df(coinpair)
    #         except Exception as error_msg:
    #             self.stdout(f"Unknown Error in schedule_candlestick_df_update() for {coinpair} - {error_msg} - "
    #                         f"Aborting...",
    #                         "CRITICAL", True)
    #             self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
    #
    # def _update_candlestick_df(self, coinpair):
    #     """
    #     Update candletick df, based on self.schedule_candlestick_df_update()'s time interval, with latest price value
    #     """
    #     try:
    #         if self.price == 0.0:
    #             print(f"No price update for {coinpair} at {datetime.now()}")
    #             return
    #         row_dict = {'datetime': self.df_prices.index[-1] + (self.df_prices.index[-1] - self.df_prices.index[-2]),
    #                     'close': self.price}
    #         df = pd.DataFrame([row_dict])
    #         df.set_index('datetime', inplace=True)
    #         self.df_prices = pd.concat([self.df_prices, df])
    #         self.df_prices = self.df_prices.drop(self.df_prices.index[0])
    #     except Exception as error_msg:
    #         print(f"Error in update_candlestick_df() for {coinpair} - with df: {self.df} - {error_msg}")
    #     return
    #
    # def calculate_macd(self, stream_data, coinpair):
    #     """
    #     Calculate MACD and generate trend direction indicator!
    #
    #     :param ma_fast: period length (historic candles + current candle) for generating fast moving average
    #     :param ma_slow: period length (historic candles + current candle) for generating slow moving average
    #     :param signal_length: period length - number of data points (of ma_fast - ma_slow) - for generating signal line
    #     :return: string
    #     """
    #     try:
    #         if self.df_prices is not None:
    #             row_df = pd.DataFrame(
    #                 [{'datetime': datetime.utcfromtimestamp(stream_data.get('trade_time') / 1e3), 'close': self.price}])
    #             row_df.set_index('datetime', inplace=True)
    #             temp_candlesticks = pd.concat([self.df_prices, row_df])
    #             signals = self._generate_signals(temp_candlesticks, coinpair)
    #             if (signals['macd_line'][-2] < signals['signal_line'][-2]) and (
    #                     signals['macd_line'][-1] > signals['signal_line'][-1]):  # Crossover to upside here
    #                 self.trend_direction = "UP"
    #             elif (signals['macd_line'][-2] > signals['signal_line'][-2]) and (
    #                     signals['macd_line'][-1] < signals['signal_line'][-1]):  # Crossover to downside here
    #                 self.trend_direction = "DOWN"
    #             elif self.trend_direction == "DOWN" and self.macd_minus_signal_cache < 0 and signals['MACD-Signal'][
    #                 -1] > 0:  # Intra-minute crossover from downside to upside
    #                 self.trend_direction = "UP"
    #             elif self.trend_direction == "UP" and self.macd_minus_signal_cache > 0 and signals['MACD-Signal'][
    #                 -1] < 0:  # Intra-minute crossover from upside to downside
    #                 self.trend_direction = "DOWN"
    #             self.macd_minus_signal_cache = signals['MACD-Signal'][-1]
    #             signals['price'] = temp_candlesticks
    #             return self.trend_direction
    #         return self.trend_direction
    #     except IndexError as i:
    #         print(f"INDEX ERROR: {i} \nfor {coinpair} with candlesticks: {self.df_prices}")
    #     except Exception as e:
    #         self.stdout(f"Unknown Error in calculate_macd() for {coinpair} - {e} - "
    #                     f"Aborting...",
    #                     "CRITICAL", True)
    #         self.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

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
