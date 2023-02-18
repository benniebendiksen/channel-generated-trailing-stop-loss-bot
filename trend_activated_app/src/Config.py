from src.BaseClass import BaseClass
import os

class Config(BaseClass):
    """
    Configuration class
    """

    def __init__(self):
        self.stdout(f"Loading trend-activated-bot configuration ...")

    API_KEY = os.environ.get('API_KEY_3')
    API_SECRET = os.environ.get('API_SECRET_3')
    CANDLESTICK_TIME_INTERVAL = '1m'
    MA_FAST = 3
    MA_SLOW = 5
    SIGNAL_LENGTH = 3
