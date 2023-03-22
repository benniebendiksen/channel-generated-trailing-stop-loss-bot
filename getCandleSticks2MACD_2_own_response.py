import math
from datetime import datetime
import pandas as pd
import numpy as np
import paramiko
from paramiko import SSHClient
from paramiko import AutoAddPolicy

pd.options.display.max_columns = 10

# string = "2023-02-15 02:23:00"
# datetimeStrpTime = datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
# normalsec = datetimeStrpTime.timestamp()
# st or et is a string that match the date pattern: %Y-%m-%d %H:%M:%S.%f, ex: 2023-02-15 02:23:00.001
def fetchRemoteClientDataFrameWithArgs(coinpair, interval, limit, st='-1.0', et='-1.0'):
    ip_addr = '18.183.102.61'
    # port = 5000
    user = 'ec2-user'
    pri_key = paramiko.RSAKey.from_private_key_file("/Users/jie/Desktop/tradingbot/key/MY_AWS_KEYS.pem")
    # print(pri_key)
    # cmd='pwd'
    # cmd='python JL_temp/is_3_odd.py'
    # cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py'
    if st == '-1.0' or et == '-1.0':
        cmd = 'python trend-activated-trailing-stop-loss-bot/src/RunRemoteClientDataWithArgs.py ' + coinpair + ' ' + \
              str(interval) + ' ' + \
              str(limit)

    else:
        print("startTime:" + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
        print(datetime.fromtimestamp(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()))
        print("endTime:" + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000))
        print(datetime.fromtimestamp(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()))
        cmd = 'python JL_temp/src/RemoteGetFutureDataWithSpecificInterval_In_Seconds.py ' + coinpair + ' ' \
              + str(interval) + ' ' \
              + str(limit) + ' ' \
              + str(float(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' ' \
              + str(float(datetime.strptime(et, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000) + ' '
    # cmd='ls'
    s = SSHClient()
    s.set_missing_host_key_policy(AutoAddPolicy())
    print("[+] Start ssh into:" + ip_addr)
    # s.connect(ip, port, user, passwd)
    s.connect(hostname='18.183.102.61', username=user, pkey=pri_key)
    print("[+] SSH established !")
    stdin, stdout, stderr = s.exec_command(cmd)
    print("[+] cmd: ")
    print(cmd)
    print("[+] output: ")
    tempJSON_str = stdout.read().decode('ascii')
    print(tempJSON_str)

    # tempJSON = json.loads(tempJSON_str)
    # print(tempJSON)
    temp_json_file = open("../../Downloads/df_pricesJson2.json", "wt")
    n = temp_json_file.write(tempJSON_str)
    temp_json_file.close()

    tempPD = pd.read_json('../../Downloads/df_pricesJson2.json', orient='split')
    # print(tempPD)

    # client = Client(api_key="QjK5Z0MyX74ykrdEAPoWwJvzcdo0g2eIS7gfSqyISlj5HHjsUmRXctkcfROJeiv3",
    #                api_secret="EzYEiocX5ERenyqCb8qf9PrgU1ew9X4MqXut8ZdHuuCJJh65seLYmo96p94bPbIf")

    if stderr.read() != None:
        print("[+] error: ")
        print(stderr.read())

    s.close()

    # testing
    # print("success")
    # print(tempPD)

    return tempPD


# match the format "%Y-%m-%d %H:%M:%S" for the time
def print_candlestick(coinpair="BTCUSDT", startTime='2023-02-15 02:19:00', endTime='2023-02-15 02:20:00'):
    df_prices = fetchRemoteClientDataFrameWithArgs(coinpair, "10", 1,
                                                        startTime, endTime)
    print(df_prices)


def get_candlestick(coinpair="BTCUSDT", amount = 20, startTime='-1.0', endTime='-1.0'):
    df_prices = fetchRemoteClientDataFrameWithArgs(coinpair, "10", amount,
                                                        startTime, endTime)
    return df_prices

def filter_df_withGivenKeyWord_Value(df: pd.DataFrame, key, value):
    temp_df = df.copy()
    for i in range(0, df[df.columns[0]].count()):
        if temp_df[key][i] == value:
            temp_df = temp_df.drop([i])

    #print(temp_df.drop([0,1,2,3,4,5,6,7,8,9,10]))
    return temp_df

def compute_ema_array(close_array, length):
    if len(close_array) >= length:
        #compute length array first
        sum = math.fsum(close_array[0:length]) / length

        ema_array = []
        for i in range(0, length-1):
            ema_array.append(0.0)

        ema_array.append(sum)


        alpha = 2 / (length + 1)
        prev_ema = 0.0
        for i in range(length, len(close_array)):
            index_i_close_price = close_array[i]
            if i == length:
                prev_ema = sum
            else:
                prev_ema = ema_array[-1]
            #prev_ema = ema_array[-1] if i != length else sum
            index_i_ema = alpha * index_i_close_price + prev_ema * (1-alpha)
            ema_array.append(index_i_ema)

        return ema_array
    else:
        return []

def computeMACDWithGivenDataFrame(input_df: pd.DataFrame, FAST, SLOW, SIGNAL_LENGTH):
    df = input_df.copy()

    close_array = df[1].tolist()
    ma_fast_array = compute_ema_array(close_array, FAST)
    ma_slow_array = compute_ema_array(close_array, SLOW)
    #print("ma_fast_array length: "+str(len(ma_fast_array)))
    #print(ma_fast_array)
    #print("ma_slow_array length: "+str(len(ma_slow_array)))
    #print(ma_slow_array)
    macd_array = []

    for i in range(SLOW-1, len(ma_fast_array)):
        macd_array.append(ma_fast_array[i] - ma_slow_array[i])

    #signal_array = compute_ema_array(macd_array[FAST:], SIGNAL_LENGTH)
    signal_array = compute_ema_array(macd_array, SIGNAL_LENGTH)


    #print("macd length: "+str(len(macd_array)))
    #print(macd_array)
    #print("signal length: "+str(len(signal_array)))
    #print(signal_array)

    histogram = []
    for i in range(SIGNAL_LENGTH-1, len(signal_array)):
        histogram.append(macd_array[i]-signal_array[i])
    #print("histogram length: "+str(len(histogram)))
    #print(histogram)

    for i in range(0, SLOW-1):
        macd_array.insert(0, 0.0)
        signal_array.insert(0, 0.0)
    for i in range(0, SLOW+SIGNAL_LENGTH-2):
        histogram.insert(0, 0.0)

    pos_array = []
    possig_array = []
    up_or_down_array = []
    reverse = False
    for i in range(0, df.shape[0]):
        pos_array.append(0)
        possig_array.append(0)

    for i in range(SIGNAL_LENGTH+SLOW-2, df.shape[0]):
        if signal_array[i] < macd_array[i]:
            pos_array[i] = 1
        elif signal_array[i] > macd_array[i]:
            pos_array[i] = -1
        else:
            pos_array[i] = 0


    for i in range(0, df.shape[0]-1):
        if reverse and pos_array[i] == 1:
            possig_array[i+1] = -1
        elif reverse and pos_array[i] == -1:
            possig_array[i+1] = 1
        else:
            possig_array[i+1] = pos_array[i]

    prev_label = ""
    for i in possig_array:
        if i == 1:
            if prev_label != "Long":
                up_or_down_array.append("MacdLE")
                prev_label = "Long"
            else:
                up_or_down_array.append("None")
        elif i == -1:
            if prev_label != "Short":
                up_or_down_array.append("MacdSE")
                prev_label = "Short"
            else:
                up_or_down_array.append("None")
        else:
            up_or_down_array.append("None")

    #print(len(up_or_down_array))
    #print(up_or_down_array)
    print(tempDF)
    df.insert(2, "macd", np.array(macd_array), True)
    df.insert(3, "signal", np.array(signal_array), True)
    df.insert(4, "UP_OR_DOWN", np.array(up_or_down_array), True)
    return df

#tempDF = get_candlestick(coinpair="BTCUSDT", amount=150)
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=1440)
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=1440)
tempDF = get_candlestick(coinpair="BTCUSDT", amount=1000, startTime='2023-03-21 16:40:00', endTime='2023-03-21 17:10:00')
print(tempDF)

#tempDF.iloc[:, 0] = tempDF.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp((int(x) + 1) / 1e3))
tempDF.iloc[:, 0] = tempDF.iloc[:, 0].apply(lambda x: datetime.fromtimestamp((int(x) + 1) / 1e3))
print(tempDF)

#print(RSI_PD)
MA_FAST = 18
MA_SLOW = 30
SIGNAL_LENGTH = 18

print(filter_df_withGivenKeyWord_Value(computeMACDWithGivenDataFrame(tempDF, MA_FAST, MA_SLOW, SIGNAL_LENGTH), 'UP_OR_DOWN', 'None'))