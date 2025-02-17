import os
import sys

from src.Config import Config
from unicorn_binance_rest_api import BinanceRestApiManager
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class BinanceHistoricalDataFetcher:
    """
    Fetches and manages historical price data from Binance Futures
    with rate limiting and data persistence capabilities.
    """

    def __init__(
            self,
            symbol: str,
            interval: str,
            data_dir: str = "historical_data",
            max_requests_per_minute: int = 1200,
            request_weight: int = 1
    ):
        self.config = Config()
        self.have_loaded_index = False
        self.socks5_proxy = self.config.SOCKS5_IP_PORT
        self.logger = None
        self.stats = None
        self.symbol = symbol.upper()
        self.interval = interval
        self.counter = 0
        self.client = BinanceRestApiManager(
            api_key=self.config.API_KEY,
            api_secret=self.config.API_SECRET,
            exchange="binance.com-futures",
            socks5_proxy_server=self.socks5_proxy,
            socks5_proxy_user=None,
            socks5_proxy_pass=None,
            socks5_proxy_ssl_verification=True
        )
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.max_requests_per_minute = max_requests_per_minute
        self.request_weight = request_weight
        self.request_timestamps: List[float] = []

        self.setup_logging()

        self.interval_ms = {
            '1m': 60000,
            '3m': 180000,
            '5m': 300000,
            '15m': 900000,
            '30m': 1800000,
            '1h': 3600000,
            '2h': 7200000,
            '4h': 14400000,
            '6h': 21600000,
            '8h': 28800000,
            '12h': 43200000,
            '1d': 86400000,
        }

    def setup_logging(self):
        """Configure logging for the data fetcher"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.symbol.lower()}_data_fetcher.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Track data collection statistics
        self.stats = {
            'total_requests': 0,
            'empty_responses': 0,
            'total_records': 0,
            'earliest_timestamp': None,
            'latest_timestamp': None
        }

    def check_rate_limit(self) -> None:
        """
        Implements rate limiting by tracking request timestamps and waiting if necessary.
        """
        weight_info = self.client.get_used_weight()
        print(f"Current API weight usage: {weight_info}")

        current_time = time.time()
        self.request_timestamps = [ts for ts in self.request_timestamps
                                   if current_time - ts < 60]

        if len(self.request_timestamps) * self.request_weight >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0])
            if sleep_time > 0:
                self.logger.info(f"Rate limit approaching, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

        self.request_timestamps.append(current_time)

    def fetch_klines(
            self,
            start_time: int,
            end_time: Optional[int] = None,
            limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch kline data for a specific time range with rate limiting.
        """
        self.check_rate_limit()
        self.stats['total_requests'] += 1

        try:
            klines = self.client.futures_klines(
                symbol=self.symbol,
                interval=self.interval,
                startTime=start_time,
                endTime=end_time,
                limit=limit
            )

            time.sleep(0.5)

            if not klines:
                self.stats['empty_responses'] += 1
                self.logger.info(
                    f"No data available for period starting at {datetime.fromtimestamp(start_time / 1000)}")
                return pd.DataFrame()

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume',
                'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])

            # Convert numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Update statistics
            self.stats['total_records'] += len(df)
            if self.stats['earliest_timestamp'] is None or df.index.min() < self.stats['earliest_timestamp']:
                self.stats['earliest_timestamp'] = df.index.min()
            if self.stats['latest_timestamp'] is None or df.index.max() > self.stats['latest_timestamp']:
                self.stats['latest_timestamp'] = df.index.max()

            return df

        except Exception as e:
            self.logger.error(f"Error fetching klines: {str(e)}")
            raise

    def fetch_complete_history(self) -> pd.DataFrame:
        """
        Fetch all available historical data for the symbol and interval.
        """
        self.logger.info(f"Starting historical data collection for {self.symbol}")

        chunk_size = 1000
        all_data = []
        consecutive_empty_responses = 0
        max_empty_responses = 3  # Stop after 3 consecutive empty responses

        # Define the datetime string
        dt_str = "2019-09-08 17:45:00"

        # Convert to a datetime object
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

        # Convert to Unix timestamp (milliseconds)
        timestamp_ms = int(dt_obj.timestamp() * 1000)

        end_time = timestamp_ms
        #end_time = int(time.time() * 1000)
        start_time = end_time - (chunk_size * self.interval_ms[self.interval])

        while True:
            print(f"Fetching data from {datetime.fromtimestamp(start_time / 1000)}")

            chunk = self.fetch_klines(
                start_time=start_time,
                end_time=end_time,
                limit=chunk_size
            )

            if chunk.empty:
                consecutive_empty_responses += 1
                if consecutive_empty_responses >= max_empty_responses:
                    self.logger.info(
                        "Reached maximum consecutive empty responses, assuming no more historical data available")
                    break
            else:
                consecutive_empty_responses = 0
                all_data.append(chunk)

            end_time = start_time
            start_time = end_time - (chunk_size * self.interval_ms[self.interval])

            if len(all_data) % 10 == 0:
                self.save_data(pd.concat(all_data))

        if not all_data:
            self.logger.error("No data collected!")
            return pd.DataFrame()

        final_df = pd.concat(all_data).sort_index()
        self.save_data(final_df)

        # Log collection statistics
        self.logger.info(f"Data collection completed:")
        self.logger.info(f"Total records: {self.stats['total_records']}")
        self.logger.info(f"Date range: {self.stats['earliest_timestamp']} to {self.stats['latest_timestamp']}")
        self.logger.info(f"Total requests: {self.stats['total_requests']}")
        self.logger.info(f"Empty responses: {self.stats['empty_responses']}")

        return final_df

    def save_data(self, df: pd.DataFrame) -> None:
        """Save the DataFrame to a CSV file while maintaining index consistency"""
        filename = self.data_dir / f"{self.symbol.lower()}_{self.interval}_historical.csv"
        df.sort_index(inplace=True)
        self.counter += 1

        try:
            if os.path.exists(filename):
                # Load existing CSV and ensure index is datetime
                existing_df = pd.read_csv(filename, index_col=0, parse_dates=True)

                # Get oldest stored timestamp
                last_timestamp = existing_df.index[0]
                print(f"existing oldest ts: {last_timestamp}")
                print(f"existing newest ts: {existing_df.index[-1]}")

                print(f"oldest ts: {df.index[0]}")
                print(f"newest ts: {df.index[-1]}")

                df = df[df.index < last_timestamp]
                combined_df = pd.concat([df, existing_df])
            else:
                combined_df = df

            # Save back to CSV (overwrite with new order)
            combined_df.to_csv(filename, mode="w", header=True, index=True)
            print(f"Prepended {len(df)} new records to {filename}")
        except Exception as e:
            print(f"Error during data saving: {str(e)}")
            sys.exit(2)

    def load_data(self) -> Optional[pd.DataFrame]:
        """Load historical data from CSV file if it exists"""
        filename = self.data_dir / f"{self.symbol.lower()}_{self.interval}_historical.csv"
        if filename.exists():
            return pd.read_csv(filename, index_col='timestamp', parse_dates=True)
        return None
