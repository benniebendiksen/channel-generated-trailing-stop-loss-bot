from src.BaseClass import BaseClass

from src.Config import Config
from datetime import datetime
import pandas as pd
import numpy as np
import time

pd.set_option("display.precision", 8)


class CoinPair(BaseClass):
    """
    Store Symbol websocket trade data of price updates and maintain resultant candlestick df.
    """
    LOOKBACK = max(Config.MA_SLOW, Config.RSI_LOOKBACK)

    def __init__(self, tsla, name):
        self.tsla = tsla
        self.name = name
        self.price = 0.0
        self.df_close_prices = pd.DataFrame()
        self.macd_minus_signal = 0
        self.trend_direction = "NULL"

    def update_candlestick_df(self):
        """
        Update candletick df, based on self.schedule_candlestick_df_update()'s time interval, with latest price value
        """
        try:
            if self.price == 0.0:
                print(f"No price update for {self.name} at {datetime.now()}")
                return
            self.stdout(f"Updating Candlestick DF for {self.name} at {datetime.now()}")
            row_dict = {'datetime': self.df_close_prices.index[-1] + (self.df_close_prices.index[-1] -
                                                                      self.df_close_prices.index[-2]),
                        'close': self.price}
            df = pd.DataFrame([row_dict])
            df.set_index('datetime', inplace=True)
            self.df_close_prices = pd.concat([self.df_close_prices, df])
            self.df_close_prices = self.df_close_prices.drop(self.df_close_prices.index[0])
        except Exception as error_msg:
            print(f"Error in update_candlestick_df() for {self.name} - with df: {self.df_close_prices} - {error_msg}")

