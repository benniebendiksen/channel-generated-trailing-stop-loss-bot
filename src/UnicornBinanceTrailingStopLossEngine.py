from unicorn_binance_trailing_stop_loss.manager import BinanceTrailingStopLossManager
import os


class UnicornBinanceTrailingStopLossEngine:
    def __init__(self, API_KEY, API_SECRET, market):
        self.ubtsl = BinanceTrailingStopLossManager(callback_error=self.callback_error,
                                               callback_finished=self.callback_finished,
                                               callback_partially_filled=self.callback_partially_filled,
                                               binance_public_key=API_KEY,
                                               binance_private_key=API_SECRET,
                                               exchange="binance.com-futures",
                                               keep_threshold="20%",
                                               market=market,
                                               print_notifications=True,
                                               reset_stop_loss_price=True,
                                               send_to_email_address="blah@example.com",
                                               send_from_email_address="blub@example.com",
                                               send_from_email_password="pass",
                                               send_from_email_server="mail.example.com",
                                               send_from_email_port=25,
                                               stop_loss_limit="3.5%",
                                               stop_loss_order_type="LIMIT",
                                               stop_loss_price=88,
                                               stop_loss_start_limit="1.5%",
                                               telegram_bot_token="telegram_bot_token",
                                               telegram_send_to="telegram_send_to")

    def callback_error(self, msg):
        print(f"STOP LOSS ERROR - ENGINE IS SHUTTING DOWN! - {msg}")
        self.ubtsl.stop_manager()

    def callback_finished(self, msg):
        print(f"STOP LOSS FINISHED - ENGINE IS SHUTTING DOWN! - {msg}")
        self.ubtsl.stop_manager()

    def callback_partially_filled(self, msg):
        print(f"STOP LOSS PARTIALLY_FILLED - ENGINE IS STILL RUNNING! - {msg}")
