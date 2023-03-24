from datetime import datetime
from src.Config import Config
import numpy
import pandas as pd
import numpy as np
import paramiko
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import json
import math
import statistics

# pd.set_option('max_columns', None)
pd.options.display.max_columns = 10


# string = "2023-02-15 02:23:00"
# datetimeStrpTime = datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
# normalsec = datetimeStrpTime.timestamp()
# st or et is a string that match the date pattern: %Y-%m-%d %H:%M:%S.%f, ex: 2023-02-15 02:23:00.001
def fetchRemoteClientDataFrameWithArgs(coinpair_name, interval, limit, st='-1.0', et='-1.0'):
    user = 'ec2-user'
    pri_key = paramiko.RSAKey.from_private_key_file(Config.REMOTE_KEYS_PATH)
    file_name = Config.AGGTRADE_FILENAME
    if st == '-1.0' or et == '-1.0':
        # cmd = 'python JL_temp/src/RunRemoteClientDataWithArgs.py ' + coinpair + ' ' + \
        cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py ' + coinpair_name + ' ' + \
              str(interval) + ' ' + \
              str(limit)

    else:
        # print("startTime:" + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
        startTime = datetime.fromtimestamp(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp())
        print(f"startTime:\n{startTime}")
        # print("endTime:" + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
        endTime = datetime.fromtimestamp(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp())
        print(f"endTime: \n{endTime}")
        cmd = 'python JL_temp/src/RemoteGetFutureDataWithSpecificInterval_In_Seconds.py ' + coinpair_name + ' ' \
              + str(interval) + ' ' \
              + str(limit) + ' ' \
              + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' ' \
              + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' '
    s = SSHClient()
    s.set_missing_host_key_policy(AutoAddPolicy())
    s.connect(hostname=Config.REMOTE_ADDRESS, username=user, pkey=pri_key)
    print(f"ssh into: {Config.REMOTE_ADDRESS} established")
    temp_json_file = open(file_name, "wt")
    stdin, stdout, stderr = s.exec_command(cmd)
    tempJSON_str = stdout.read().decode('ascii')
    n = temp_json_file.write(tempJSON_str)
    temp_json_file.close()
    tempPD = pd.read_json(file_name, orient='split')
    # if stderr.read() != None:
    #     print("[+] error: ")
    #     print(stderr.read())
    s.close()
    return tempPD


# match the format "%Y-%m-%d %H:%M:%S" for the time
def get_candlestick(coinpair="BTCUSDT", amount=20, startTime='2023-02-15 02:19:00', endTime='2023-02-15 02:20:00'):
    df_prices = fetchRemoteClientDataFrameWithArgs(coinpair, "10", amount,
                                                   startTime, endTime)
    return df_prices


def computeBollWithGivenCloseArray(close_array):
    basis = math.fsum(close_array) / length
    # print(basis)
    multiplier = 2.0
    # ta.stdev(source, length), where source is candlesticks close price, length is 20
    ta_std = np.std(close_array)
    # ta_std = statistics.stdev(close_array)
    # print("Standard Deviation of the sample is % s " % (ta_std))
    dev = multiplier * ta_std
    upper = basis + dev
    lower = basis - dev
    # print("upper: " + str(upper))
    # print("lower: " + str(lower))
    # print("computeBoll close array: ")
    # print(close_array)
    return [close_array[len(close_array) - 1], basis, dev, upper, lower]


def computeBollWithGivenDataFrame(input_df: pd.DataFrame, length=20):
    df = input_df.copy()
    close_array = np.array(df[1].tolist())
    basis_array = []
    dev_array = []
    upperBand_array = []
    lowerBand_array = []
    BBand_SE_or_LE = []
    prev_label_list = []
    for i in range(0, length - 1):
        basis_array.append(0.0)
        dev_array.append(0.0)
        upperBand_array.append(0.0)
        lowerBand_array.append(0.0)
        BBand_SE_or_LE.append("None")

    prev_label = ""
    first_label_checked = False
    first_label_index = -1
    for i in range(length - 1, len(close_array)):
        temp_array = close_array[i + 1 - length:i + 1]
        basis = math.fsum(temp_array) / length
        basis_array.append(basis)
        multiplier = 2.0
        ta_std = np.std(temp_array)
        dev = multiplier * ta_std
        dev_array.append(dev)
        upper = basis + dev
        lower = basis - dev
        upperBand_array.append(upper)
        lowerBand_array.append(lower)
        # if i != length-1 and i != length:
        if i > length:
            prev_close = temp_array[-2]
            previous_pre_close = temp_array[-3]
            prev_upper = upperBand_array[-2]
            previous_prev_upper = upperBand_array[-3]
            prev_lower = lowerBand_array[-2]
            previous_prev_lower = lowerBand_array[-3]
            if prev_close < prev_upper and previous_pre_close >= previous_prev_upper:
                if prev_label != "BBandSE":
                    BBand_SE_or_LE.append("BBandSE")
                    prev_label = "BBandSE"
                    if not first_label_checked:
                        first_label_checked = True
                        first_label_index = i
                else:
                    BBand_SE_or_LE.append("None")
            elif prev_close > prev_lower and previous_pre_close <= previous_prev_lower:
                if prev_label != "BBandLE":
                    BBand_SE_or_LE.append("BBandLE")
                    prev_label = "BBandLE"
                    if not first_label_checked:
                        first_label_checked = True
                        first_label_index = i
                else:
                    BBand_SE_or_LE.append("None")

            else:
                BBand_SE_or_LE.append("None")
        else:
            BBand_SE_or_LE.append("None")

        # print()

    # print("first_label_index: "+ str(first_label_index))
    df.insert(2, "UpperBand", np.array(upperBand_array), True)
    df.insert(3, "LowerBand", np.array(lowerBand_array), True)
    if first_label_index != -1:
        BBand_SE_or_LE[first_label_index] = 'None'

    df.insert(4, "SE_OR_LE", np.array(BBand_SE_or_LE), True)
    return df


def filter_DF4Bollinger(df: pd.DataFrame):
    temp_df = df.copy()
    for i in range(0, df[df.columns[0]].count()):
        if temp_df['SE_OR_LE'][i] == 'None':
            temp_df = temp_df.drop([i])

    # print(temp_df.drop([0,1,2,3,4,5,6,7,8,9,10]))
    return temp_df


def filter_df_withGivenKeyWord_Value(df: pd.DataFrame, key, value):
    temp_df = df.copy()
    for i in range(0, df[df.columns[0]].count()):
        if temp_df[key][i] == value:
            temp_df = temp_df.drop([i])
    return temp_df


length = 180
tempDF = get_candlestick(coinpair="BTCUSDT", amount=length + 2, startTime='2023-03-23 20:30:00',
                         endTime='2023-03-23 21:00:00')

# tempDF = get_candlestick(coinpair="BTCUSDT", amount=length, startTime='-1.0', endTime='-1.0')
close_array = tempDF[1].tolist()
# tempDF.iloc[:, 0] = tempDF.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp((int(x) + 1) / 1e3))
tempDF.iloc[:, 0] = tempDF.iloc[:, 0].apply(lambda x: datetime.fromtimestamp((int(x) + 1) / 1e3))
print(f"Candlestick Close Values DF:\n{tempDF}")
filtered_df = filter_df_withGivenKeyWord_Value(computeBollWithGivenDataFrame(tempDF), 'SE_OR_LE', 'None')
print(f"Candlestick DF Filtered for Signals:\n{filtered_df}")
