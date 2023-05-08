from functools import wraps
from src.Config import Config
from unicorn_binance_rest_api.exceptions import BinanceAPIException
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
import threading
import requests
import json


def api_method_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BinanceAPIException as e:
            print(f"Error in {func.__name__}: {e}")
            return None

    return wrapper


class BinanceManager:
    """
    Methods to interact with Binance API
    """

    def __init__(self, baseclass):
        self.baseclass = baseclass
        self.client_switch_bool = True
        self.client = Client(api_key=baseclass.config.API_KEY, api_secret=baseclass.config.API_SECRET)
        if baseclass.config.API_KEY_2 and baseclass.config.API_SECRET_2:
            self.client_2 = Client(api_key=baseclass.config.API_KEY_2, api_secret=baseclass.config.API_SECRET_2)
        self.client_switch_bool_2 = 1
        self.account = self.get_account()
        self.balances = []
        self.addresses = {}
        self.markets = baseclass.config.markets  # Set the markets attribute using the config object

    def get_coin_list(self):
        coin_list = set()
        for market in self.markets:
            coin_list.add(market.split("_")[0])
        return list(coin_list)

    def sell_asset_for_usdt(self, asset, quantity):
        symbol = f"{asset}_USDT"
        try:
            order = self.client.create_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )
            return order
        except Exception as e:
            self.baseclass.stdout(f"Unable to sell {asset} for USDT. Exception: {e}", "ERROR")
            return None


def zero_out_unlisted_wallets(self):
    coin_list = self.get_coin_list()
    account_balances = self.get_account_balances()
    for balance in account_balances:
        if balance['asset'] not in coin_list and balance['asset'] != 'USDT':
            free_balance = float(balance['free'])
            if free_balance > 0:
                self.sell_asset_for_usdt(asset=balance['asset'], quantity=free_balance)

    @api_method_wrapper
    def get_addresses(self, coins):
        self.addresses = {coin: self.get_coin_address(coin).get('address') for coin in coins}
        return self.addresses

    @api_method_wrapper
    def set_balances(self, coin_list):
        keyValList = [coin.upper() for coin in coin_list]
        keyValList.append('BTC')
        self.balances = [d for d in self.get_account_balances() if d['asset'] in keyValList]

    @api_method_wrapper
    def get_exchange_info(self, *args, **kwargs):
        if self.baseclass.config.API_SECRET_2 and self.client_switch_bool:
            self.client_switch_bool = False
            return self.client_2.get_exchange_info(*args, **kwargs)
        self.client_switch_bool = True
        return self.client.get_exchange_info(*args, **kwargs)

    @api_method_wrapper
    def get_klines(self, *args, **kwargs):
        if self.baseclass.config.API_SECRET_2 and self.client_switch_bool:
            self.client_switch_bool = False
            return self.client_2.get_klines(*args, **kwargs)
        self.client_switch_bool = True
        return self.client.get_klines(*args, **kwargs)

    @api_method_wrapper
    def get_coin_address(self, coin):
        return self.client.get_deposit_address(coin=coin)

    @api_method_wrapper
    def get_open_orders(self, symbol):
        return self.client.get_open_orders(symbol=symbol)

    @api_method_wrapper
    def get_account(self):
        return self.client.get_account()

    @api_method_wrapper
    def get_account_balances(self):
        account = self.account
        return account.get('balances')

    @api_method_wrapper
    def create_order(self, **kwargs):
        self.client.create_order(**kwargs)

    @api_method_wrapper
    def create_multi_orders(self, list_of_kwargs):
        threads = [threading.Thread(target=self.create_order, kwargs=args) for args in list_of_kwargs]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return True

    @api_method_wrapper
    def cancel_order(self, **kwargs):
        self.client.cancel_order(**kwargs)

    @api_method_wrapper
    def cancel_orders(self, list_of_kwargs):
        threads = [threading.Thread(target=self.cancel_order(), kwargs=args) for args in list_of_kwargs]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return True
