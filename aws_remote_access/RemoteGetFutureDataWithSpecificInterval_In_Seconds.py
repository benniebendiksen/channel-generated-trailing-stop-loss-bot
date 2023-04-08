import sys

import numpy as np
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
import pandas as pd
from datetime import datetime

# def futures_klines(**params):
#     client = Client()
#     return client._request_futures_api('get', 'klines', data=params)
#
# print(futures_klines(symbol='BTCUSDT', limit=100, interval= '1m'))

def get_future_aggregate(**params):
    API_KEY="blah"
    API_SECRET="blurb"
    client = Client(api_key=API_KEY, api_secret=API_SECRET)
    #res = client.get_exchange_info()
    #print(client.response.headers)
    return client._request_futures_api('get', 'aggTrades', data=params)


def response_price_closest_timeStamp(list, timeStamp, start_index = 0):
    index = -1
    #print("id: " + str(id(list)))
    temp_price = "-1.0"
    temp_timestamp = "-1"

    for i in range(start_index, len(list)):
        if timeStamp-list[i]['T'] > 0:
            temp_timestamp = list[i]['T']
            temp_price = list[i]['p']
            index = i

    print([temp_price, temp_timestamp, index])
    return [temp_price, temp_timestamp, index]

#1m
#interval in seconds
def get_close_price_array(coinpair='BTCUSDT', interval=10, startTime=1679018939000, endTime=1679018940000):
    temp_start_time = startTime
    next_interval_timestamp = temp_start_time + interval*1000

    response_start_time = startTime
    reponse_next_30s_timestamp = response_start_time + 1000*30
    close_price_array = [] #[[close, opentime, closetime], [close, opentime, closetime]...]
    price = 0.0
    temp_current_open_time = startTime
    temp_current_response = get_future_aggregate(symbol=coinpair, limit=1000,
                                                 startTime=response_start_time, endTime=reponse_next_30s_timestamp)

    #print(temp_current_response)

    #print(temp_current_response)
    counter = 0
    while (temp_start_time <= endTime):
        #get close price
        if temp_start_time >= next_interval_timestamp:
            #price = float(temp_current_response[-1]['p'])
            #temp_current_close_time  = str(temp_current_response[-1]['T'])
            #print("temp_current_response: "+str(temp_current_open_time))
            #print("next_interval_timestamp: "+str(next_interval_timestamp))
            temp_close_price_result = response_price_closest_timeStamp(temp_current_response, next_interval_timestamp)
            close_price_array.append([temp_close_price_result[0], str(temp_current_open_time), str(temp_close_price_result[1])])
            temp_current_open_time = next_interval_timestamp
            next_interval_timestamp = next_interval_timestamp + interval * 1000

            #print("closetime: "+temp_current_close_time)
            #print("next10s time:"+str(next_10s_timestamp))

        #     temp_start_time = temp_start_time + 1000
        # else:
        #     temp_start_time = temp_start_time + 1000

        if temp_start_time >= reponse_next_30s_timestamp:
            response_start_time = reponse_next_30s_timestamp
            reponse_next_30s_timestamp = response_start_time + 1000 * 30
            temp_current_response = get_future_aggregate(symbol='BTCUSDT', limit=1000,
                                                         startTime=response_start_time,
                                                         endTime=reponse_next_30s_timestamp)
            base_int = 1
            while (len(temp_current_response) >= 1000*base_int):
                base_int = base_int+1
                temp_current_response = temp_current_response + get_future_aggregate(symbol='BTCUSDT', limit=1000,
                                                         startTime=temp_current_response[-1]['T'],
                                                         endTime=reponse_next_30s_timestamp)

        temp_start_time = temp_start_time + 1000


    return close_price_array

def runRemoteClientData(coinpair = "BTCUSDT", interval = 60, limit = 1000, st = 0, et = 0):
    response = get_close_price_array(coinpair=coinpair, interval=interval, startTime=st, endTime=et)

    array_response = np.array(response)
    list_response = array_response[:, [1, 0]].tolist()  # subset by timestamp and 'close' fields
    df_prices = pd.DataFrame(list_response)  # convert to dataframe
    #print(df_prices)

    df_prices.to_json('df_prices.json', orient='split')
    file1 = open('df_prices.json')
    #tempJSON = json.load(file1)
    #print(tempJSON)
    file2 = open('df_prices.json', 'r')
    print(file2.read())

if len(sys.argv) <= 3:
    runRemoteClientData()
elif len(sys.argv) >= 6:
    runRemoteClientData(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(float(sys.argv[4])), int(float(sys.argv[5])))
else:
    runRemoteClientData(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))