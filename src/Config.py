from src.BaseClass import BaseClass
import os

class Config(BaseClass):
    """
    Configuration class
    """

    def __init__(self):
        self.stdout(f"Loading trend-activated-bot configuration ...")

    API_KEY = os.environ.get('API_KEY')
    API_SECRET = os.environ.get('API_SECRET')
