from src.BaseClass import BaseClass
import os

class Config(BaseClass):
    """
    Configuration class
    """

    def __init__(self):
        self.stdout(f"Loading trend-activated-bot configuration ...")

    # API_KEY = os.environ.get('API_KEY')
    # API_SECRET = os.environ.get('API_SECRET')
    API_KEY = "QjK5Z0MyX74ykrdEAPoWwJvzcdo0g2eIS7gfSqyISlj5HHjsUmRXctkcfROJeiv3"
    API_SECRET = "EzYEiocX5ERenyqCb8qf9PrgU1ew9X4MqXut8ZdHuuCJJh65seLYmo96p94bPbIf"
    REMOTE_KEYS_PATH = "/Users/bendiksen/Desktop/trend-activated-trailing-stop-loss-bot/MY_AWS_KEYS.pem"
    REMOTE_ADDRESS = "18.183.102.61"
    AGGTRADE_FILENAME = "df_aggTrade_returned.json"
    MARKETS = ["btcusdt", "ethusdt"]
    CANDLESTICK_TIME_INTERVAL = '1m'
    #MACD PARAMS
    MA_FAST = 3
    MA_SLOW = 5
    SIGNAL_LENGTH = 3
    #RSI PARAMS
    RSI_LOOKBACK = 14
    OVERBOUGHT = 70
    OVERSOLD = 30