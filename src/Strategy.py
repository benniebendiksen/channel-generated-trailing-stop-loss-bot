from src.BaseClass import BaseClass
import numpy as np
import pandas as pd
import sys

class Strategy(BaseClass):
    """
    Class that houses the very strategy generating algorithm, designed to capture
    an otherwise visually-defined trend following strategy
    """


    def __init__(self, client):
        self.client = client

    def create_df(self, list_klines):
        array_np = np.array([lst[:5] for lst in list_klines])
        return pd.DataFrame(array_np)
