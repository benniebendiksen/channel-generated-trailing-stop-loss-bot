from src.BaseClass import BaseClass
from datetime import datetime
import pandas as pd
import paramiko


class SSHClientSingleton(BaseClass):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config):
        self.config = config
        self.ssh_client = self.establish_remote_connection()

    def establish_remote_connection(self):
        user = 'ec2-user'
        pri_key = paramiko.RSAKey.from_private_key_file(
            self.config.REMOTE_KEYS_PATH)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=self.config.REMOTE_ADDRESS, username=user, pkey=pri_key)
        print(f"ssh into: {self.config.REMOTE_ADDRESS} established")
        return ssh_client

    def fetch_klines_remotely(self, ssh_client, coinpair_name="btcusdt", candle_time_interval ='1m', num_candles = 5,
                              st='-1.0', et='-1.0'):
        if st == '-1.0' or et == '-1.0':
            cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py ' + coinpair_name + ' ' + \
                  str(candle_time_interval) + ' ' + \
                  str(num_candles)
        else:
            print("startTime:" + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
            print(datetime.fromtimestamp(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()))
            print("endTime:" + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
            print(datetime.fromtimestamp(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()))
            cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py ' + \
                  coinpair_name \
                  + ' ' \
                  + str(candle_time_interval) + ' ' \
                  + str(num_candles) + ' ' \
                  + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' ' \
                  + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' '
        print(f"fetching klines for: {coinpair_name}")
        temp_json_file = open("df_prices_returned.json", "wt")
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        tempJSON_str = stdout.read().decode('ascii')
        n = temp_json_file.write(tempJSON_str)
        temp_json_file.close()
        # if stderr.read() != None:
        #     print("[+] error: ")
        #     print(stderr.read())
        return pd.read_json('df_prices_returned.json', orient='split')
