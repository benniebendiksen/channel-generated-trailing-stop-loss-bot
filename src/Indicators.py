from src.BaseClass import BaseClass
from src.Config import Config
from datetime import datetime
import pandas as pd
import numpy as np
import asyncio
import time
import math

pd.set_option("display.precision", 8)


class Indicators(BaseClass):
    """
    Spawn dynamically updating candlestick close values dataframe, per Symbol.
    Continually compute values for indicators using aforementioned dataframe.
    """

    def __init__(self, tsla, config, client, Coinpairs, loop):
        self.tsla = tsla
        self.config = config
        self.event_loop = loop
        self.timeframe = Config.CANDLESTICK_TIME_INTERVAL
        self.ma_fast = Config.MA_FAST
        self.ma_slow = Config.MA_SLOW
        self.signal_length = Config.SIGNAL_LENGTH
        self.Coinpairs = Coinpairs
        self.dict_macd_values = {}
        self.dict_rsi_values = {}
        self.client = client
        self.macd = self.MACD(self.tsla, self.config)
        self.event_loop.create_task(self.schedule_candlestick_df_update())

    def fetch_and_make_kline_df(self, coinpair_instance):
        try:
            df_prices = self.client.fetch_klines_remotely(coinpair_instance.name.split("@")[0])
            df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp(
                (int(x) + 1) / 1e3))  # provide one millisecond and break down into fractions of a second
            df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
            df_prices.rename(columns={df_prices.columns[0]: "datetime", df_prices.columns[1]: "close"},
                             inplace=True)
            df_prices.set_index("datetime", inplace=True)
            coinpair_instance.df_close_prices = df_prices
            coinpair_instance.price = df_prices.iloc[-1, 0]
            self.macd.initialize_macd(coinpair_instance)
        except Exception as error:
            self.stdout(f"Unknown Error in fetch_and_make_kline_df() - {error} - "
                        f"Aborting...",
                        "CRITICAL", True)
            self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

    async def schedule_candlestick_df_update(self):
        """
        scheduler method for updating the candlestick_df
        """
        # self.stdout(f"Started async schedule_tick_df_update()...")
        [self.fetch_and_make_kline_df(cp) for cp in self.Coinpairs]
        self.ssh_singleton.ssh_client.close()
        start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
        sleep_time = start_time - time.time()
        while self.tsla.is_stopping() is False:
            try:
                await asyncio.sleep(sleep_time)
                start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
                sleep_time = start_time - time.time()
                for coinpair in self.Coinpairs:
                    coinpair.update_candlestick_df()
            except Exception as error_msg:
                self.stdout(f"Unknown Error in schedule_candlestick_df_update() - {error_msg} - "
                            f"Aborting...",
                            "CRITICAL", True)
                self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

    def perform_indicator_updates(self, stream_data, coinpair_instance):
        coinpair_instance.price = float(stream_data.get("price"))
        coinpair_instance.trend_direction = self.macd.calculate_macd(stream_data, coinpair_instance)
        symbol = coinpair_instance.name.split("@")[0]
        print(f"trend direction for {symbol}: {coinpair_instance.trend_direction}")

    class MACD(BaseClass):
        def __init__(self, tsla, config):
            self.tsla = tsla
            self.config = config

        def initialize_macd(self, coinpair_instance):
            try:
                df_prices = coinpair_instance.df_close_prices
                signals = self._generate_signals(df_prices, coinpair_instance.name)
                if signals['macd_line'][-1] > signals['signal_line'][-1]:
                    trend_direction = "UP"
                elif signals['macd_line'][-1] < signals['signal_line'][-1]:
                    trend_direction = "DOWN"
                coinpair_instance.price = df_prices.iloc[4, 0]
                coinpair_instance.macd_minus_signal = signals['MACD-Signal'][-1]
                coinpair_instance.df_close_prices = df_prices
                coinpair_instance.trend_direction = trend_direction
                print(f"trend for {coinpair_instance.name}: {coinpair_instance.trend_direction}")
            except Exception as error_msg:
                self.stdout(f"Unknown Error in initialize_macd() for {coinpair_instance.name} - {error_msg} - "
                            f"Aborting...", "CRITICAL", True)
                self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

        def calculate_macd(self, stream_data, coinpair_instance):
            """
            Calculate MACD and generate trend direction indicator!

            :param stream_data:
            :param coinpair_instance:
            :param ma_fast: period length (historic candles + current candle) for generating fast moving average
            :param ma_slow: period length (historic candles + current candle) for generating slow moving average
            :param signal_length: period length - number of data points (of ma_fast - ma_slow) - for generating signal line
            :return: string
            """
            try:
                if coinpair_instance.df_close_prices is not None:
                    row_df = pd.DataFrame(
                        [{'datetime': datetime.utcfromtimestamp(stream_data.get('trade_time') / 1e3),
                          'close': coinpair_instance.price}])
                    row_df.set_index('datetime', inplace=True)
                    temp_candlesticks = pd.concat([coinpair_instance.df_close_prices, row_df])
                    signals = self._generate_signals(temp_candlesticks, coinpair_instance.name)
                    if (signals['macd_line'][-2] < signals['signal_line'][-2]) and (
                            signals['macd_line'][-1] > signals['signal_line'][-1]):  # Crossover to upside here
                        coinpair_instance.trend_direction = "UP"
                    elif (signals['macd_line'][-2] > signals['signal_line'][-2]) and (
                            signals['macd_line'][-1] < signals['signal_line'][-1]):  # Crossover to downside here
                        coinpair_instance.trend_direction = "DOWN"
                    elif coinpair_instance.trend_direction == "DOWN" and coinpair_instance.macd_minus_signal < 0 and \
                            signals['MACD-Signal'][
                                -1] > 0:  # Intra-minute crossover from downside to upside
                        coinpair_instance.trend_direction = "UP"
                    elif coinpair_instance.trend_direction == "UP" and coinpair_instance.macd_minus_signal > 0 and \
                            signals[
                                'MACD-Signal'][
                                -1] < 0:  # Intra-minute crossover from upside to downside
                        coinpair_instance.trend_direction = "DOWN"
                    coinpair_instance.macd_minus_signal = signals['MACD-Signal'][-1]
                    signals['price'] = temp_candlesticks
                    return coinpair_instance.trend_direction
                else:
                    self.stdout(f"calculate_macd(): Empty df_close_prices dataframe found for {coinpair_instance.name}"
                                f" - Aborting...", "CRITICAL", True)
                    self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
            except IndexError as i:
                print(
                    f"INDEX ERROR: {i} \nfor {coinpair_instance.name} with candlesticks: "
                    f"{coinpair_instance.df_close_prices}")
            except Exception as e:
                self.stdout(f"Unknown Error in calculate_macd() for {coinpair_instance.name} - {e} - "
                            f"Aborting...",
                            "CRITICAL", True)
                self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

        def _generate_signals(self, df, name):
            """
            Generate macd_line as well as signal_line for a given dataframe
            """
            try:
                ma_fast = df.ewm(span=self.config.MA_FAST, adjust=True).mean()
                ma_slow = df.ewm(span=self.config.MA_SLOW, adjust=True).mean()
                macd = ma_fast - ma_slow
                # print(f"MACD 1 {macd} for {name}")
                macd['fast'] = ma_fast
                macd['slow'] = ma_slow
                macd['signal_line'] = macd.close.ewm(span=self.config.SIGNAL_LENGTH).mean()
                # print(f"MACD 2 {macd} for {name}")
                signals = pd.DataFrame(index=macd.index)
                signals['macd_line'] = macd['close']
                signals['signal_line'] = macd['signal_line']
                signals['MACD-Signal'] = signals['macd_line'] - signals['signal_line']
                return signals
            except IndexError as i:
                print(f"INDEXERROR in _generate_signals(): {i} for {name} with ticks: {df}")
            except Exception as e:
                self.stdout(f"Unknown Error in _generate_signals() for {name} - {e} - "
                            f"Aborting...", "CRITICAL", True)
                self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")
