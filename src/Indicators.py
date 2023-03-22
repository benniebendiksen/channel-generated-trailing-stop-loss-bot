from src.BaseClass import BaseClass
from src.SSHClientSingleton import SSHClientSingleton
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

    def __init__(self, tsla, config, coinpair_instances_list):
        self.tsla = tsla
        self.config = config
        self.timeframe = Config.CANDLESTICK_TIME_INTERVAL
        self.ma_fast = Config.MA_FAST
        self.ma_slow = Config.MA_SLOW
        self.signal_length = Config.SIGNAL_LENGTH
        self.coinpairs = coinpair_instances_list
        self.dict_macd_values = {}
        self.dict_rsi_values = {}
        self.ssh_singleton = SSHClientSingleton(config)
        for coinpair in self.coinpairs:
            self.initialize_macd(coinpair)

    async def schedule_candlestick_df_update(self):
        """
        scheduler method for updating the candlestick_df
        """
        # self.stdout(f"Process: {process_num}: Started async schedule_tick_df_update() for {tick.name}...")
        start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
        sleep_time = start_time - time.time()
        while self.tsla.is_stopping() is False:
            try:
                await asyncio.sleep(sleep_time)
                start_time = 1 * 60 * (math.ceil(time.time() / (1 * 60)))
                sleep_time = start_time - time.time()
                for coinpair in self.coinpairs:
                    coinpair.update_candlestick_df()
            except Exception as error_msg:
                self.stdout(f"Unknown Error in schedule_candlestick_df_update() - {error_msg} - "
                            f"Aborting...",
                            "CRITICAL", True)
                self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")

    def initialize_macd(self, coinpair_instance):
        try:
            # make api call to server for candlestick data
            # response = self.get_kline_volume(coinpair, self.config.CANDLESTICK_TIME_INTERVAL, self.config.MA_SLOW)
            # #data preprocessing
            # array_response = np.array(response)
            # list_response = array_response[:, [0, 4]].tolist()  # subset by timestamp and 'close' fields
            # df_prices = pd.DataFrame(list_response) # convert to dataframe
            df_prices = self.ssh_singleton.fetch_klines_remotely(self.ssh_singleton.ssh_client, coinpair_instance.name)
            df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp(
                (int(x) + 1) / 1e3))  # provide one millisecond and break down into fractions of a second
            df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
            df_prices.rename(columns={df_prices.columns[0]: "datetime", df_prices.columns[1]: "close"}, inplace=True)
            df_prices.set_index("datetime", inplace=True)
            # now ready to generate moving averages
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
            print(f"INDEXERROR: {i} for {name} with ticks: {df}")
        except Exception as e:
            self.stdout(f"Unknown Error in _generate_signals() for {name} - {e} - "
                        f"Aborting...", "CRITICAL", True)
            self.tsla.exit_all(exit_code=0, exit_msg=f"Fatal Error — terminating")