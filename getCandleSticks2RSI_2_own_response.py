import math
from datetime import datetime
import pandas as pd
import numpy as np
import paramiko
from paramiko import SSHClient
from paramiko import AutoAddPolicy

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

def computeRSIWithGivenDataFrame(input_df: pd.DataFrame, length = 14):
    df = input_df.copy()
    close_array = df[1].tolist()
    # current price - prev price > 0 is avg gain, < 0 is avg loss
    # find total gain and total loss
    gain_array = []
    loss_array = []
    gain_array.append(0)
    loss_array.append(0)
    for i in range(1, length + 1):
        gain_or_loss = close_array[i] - close_array[i - 1]
        gain_array.append(max(gain_or_loss, 0))
        loss_array.append(abs(min(gain_or_loss, 0)))

    avg_gain = math.fsum(gain_array) / length
    avg_loss = math.fsum(loss_array) / length
    print("before avg_gain: " + str(avg_gain))
    print("before avg_loss: " + str(avg_loss))

    close_array_after_14 = close_array[15:]
    # print(close_array_after_14)

    buy_or_sell_array = []
    RSI_array = []
    # fill 0s in
    for i in range(0, length + 1):
        buy_or_sell_array.append("None")
        RSI_array.append(0.0)

    prev_label = ""
    #first_label_checked = False
    #first_label_index = -1

    #skip first 2 labels
    first_two_labels_index = []
    if len(close_array_after_14) > 0:
        for i in range(0, len(close_array_after_14)):
            if i == 0:
                gain_or_loss = close_array_after_14[i] - close_array[length]
            else:
                gain_or_loss = close_array_after_14[i] - close_array_after_14[i - 1]
            # avg_gain = (avg_gain * 13 + max(gain_or_loss, 0)) / 14
            # avg_loss = (avg_loss * 13 + abs(min(gain_or_loss, 0))) / 14
            avg_gain = (avg_gain * 13 + max(gain_or_loss, 0)) / length
            avg_loss = (avg_loss * 13 + abs(min(gain_or_loss, 0))) / length
            RS = avg_gain / avg_loss
            RSI = 100.0 - 100.0 / (1.0 + RS)

            RSI_array.append(RSI)

            previous_RSI = RSI_array[-2]
            previous_prev_RSI = RSI_array[-3]
            overSold = 30.0
            overBought = 70.0
            # co = ta.crossover(vrsi, overSold)
            # The `source1`-series is defined as having crossed over `source2`-series if,
            # on the current bar, the value of `source1` is greater than the value of `source2`,
            # and on the previous bar,
            # the value of `source1` was less than or equal to the value of `source2`.
            if previous_RSI > overSold and previous_prev_RSI <= overSold:
                if prev_label != "RsiLE":
                    buy_or_sell_array.append("RsiLE")
                    prev_label = "RsiLE"
                    #if not first_label_checked:
                    if len(first_two_labels_index) < 2:
                        #first_label_checked = True
                        #first_label_index = len(RSI_array)-1
                        first_two_labels_index.append(len(RSI_array)-1)
                else:
                    buy_or_sell_array.append("None")

            # cu = ta.crossunder(vrsi, overBought)
            # The `source1`-series is defined as having crossed under `source2`-series if,
            # on the current bar, the value of `source1` is less than the value of `source2`,
            # and on the previous bar,
            # the value of `source1` was greater than or equal to the value of `source2`.
            elif previous_RSI < overBought and previous_prev_RSI >= overBought:
                if prev_label != "RsiSE":
                    buy_or_sell_array.append("RsiSE")
                    prev_label = "RsiSE"
                    #if not first_label_checked:
                    if len(first_two_labels_index) < 2:
                        #first_label_checked = True
                        #first_label_index = len(RSI_array)-1
                        first_two_labels_index.append(len(RSI_array)-1)
                else:
                    buy_or_sell_array.append("None")
            else:
                buy_or_sell_array.append("None")

    # print(pd.Series(RSI_array))
    # df.insert(2, "Age", [21, 23, 24, 21], True)
    df.rename(columns={tempDF.columns[0]: "datetime", tempDF.columns[1]: "close"}, inplace=True)
    df.insert(2, "RSI", np.array(RSI_array), True)
    #print("first_label index: "+str(first_label_index))
    #if first_label_index != -1:
    #    buy_or_sell_array[first_label_index] = 'None'
    if len(first_two_labels_index) > 0:
        for i in first_two_labels_index:
            buy_or_sell_array[i] = 'None'

    df.insert(3, "whichEntry", np.array(buy_or_sell_array), True)
    #print(df)
    return df

#tempDF = get_candlestick(coinpair="BTCUSDT", interval=14, startTime='2023-03-11 14:00:00', endTime='2023-03-11 14:15:00')
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=72, startTime='2023-03-11 14:40:00', endTime='2023-03-11 15:52:00')
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=60, startTime='2023-03-11 15:00:00', endTime='2023-03-11 16:00:00')
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=60, startTime='2023-03-11 15:00:00', endTime='2023-03-11 16:00:00')
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=120, startTime='2023-03-14 11:00:00', endTime='2023-03-14 13:00:00')
#tempDF = get_candlestick(coinpair="BTCUSDT", amount=800)
tempDF = get_candlestick(coinpair="BTCUSDT", amount=180, startTime='2023-03-21 20:43:00', endTime='2023-03-21 21:13:00')
#print(tempDF)

#tempDF.iloc[:, 0] = tempDF.iloc[:, 0].apply(lambda x: datetime.utcfromtimestamp((int(x) + 1) / 1e3))

tempDF.iloc[:, 0] = tempDF.iloc[:, 0].apply(lambda x: datetime.fromtimestamp((int(x) + 1) / 1e3))
print(tempDF)

length = 14

#RS = avg_gain / avg_loss
#RSI = 100.0 - 100.0 / (1.0 + RS)
#print("RSI: "+str(RSI))

#print(RSI_PD)
print(computeRSIWithGivenDataFrame(tempDF))
print(filter_df_withGivenKeyWord_Value(computeRSIWithGivenDataFrame(tempDF), 'whichEntry', 'None'))