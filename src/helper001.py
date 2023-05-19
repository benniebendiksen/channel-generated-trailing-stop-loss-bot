import pandas as pd
import numpy as np
import decimal
from datetime import datetime


# https://stackoverflow.com/questions/6189956/easy-way-of-finding-decimal-places
def find_decimals(value):
    # return (int(abs(decimal.Decimal(str(value)).as_tuple().exponent)))
    return int(abs(decimal.Decimal(str(value)).as_tuple().exponent))


# format: "2023-02-15 02:23:00"
def convertDateStr2TimeStamp(dateString):
    return int(datetime.strptime(dateString, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000


def convertTimeStamp2DateTime(integer):
    return datetime.fromtimestamp(integer*1.0/1000)


def findCandleInterception(df: pd.DataFrame) -> list:
    interceptionList_high = []
    interceptionList_low = []
    length = df.shape[0]
    # initial_index = df.index[0]
    # for i in range(initial_index, initial_index+length):
    for i in range(0, length):
        # 0 time, 1 open price, 2 highest, 3 lowest, 4 close price
        if df[1][i] > df[4][i]:  # red candle
            i_top_price = df[1][i]
            i_bottom_price = df[4][i]
        else:  # green candle
            i_top_price = df[4][i]
            i_bottom_price = df[1][i]

        tempHighList = []
        tempLowList = []
        i_high = df[2][i]
        i_low = df[3][i]
        # for j in range(initial_index, initial_index+length):
        for j in range(0, length):
            if i == j:
                continue

            if df[1][j] > df[4][j]:  # red candle
                j_top_price = df[1][j]
                j_bottom_price = df[4][j]
            else:  # green candle
                j_top_price = df[4][j]
                j_bottom_price = df[1][j]

            j_high = df[2][j]
            j_low = df[3][j]
            # x1 <= y2 && y1 <= x2
            # https://stackoverflow.com/questions/3269434/whats-the-most-efficient-way-to-test-if-two-ranges-overlap
            if i_top_price <= j_high and j_top_price <= i_high:
                tempHighList.append(j)  # dataframe index num
                # tempHighList.append(j_high)
            if j_low <= i_bottom_price and i_low <= j_bottom_price:
                tempLowList.append(j)  # dataframe index num
                # tempLowList.append(j_low)

        interceptionList_high.append(tempHighList)
        interceptionList_low.append(tempLowList)

    return [interceptionList_high, interceptionList_low]


def findTrend(df: pd.DataFrame) -> str:
    # df[4] is close, df[1] is open
    # list of close vals - list of open vals
    df_sum = np.sum(df[4]-df[1])

    trend = "None"
    if df_sum > 0:
        trend = "UP"
    elif df_sum < 0:
        trend = "DOWN"
    return trend


# https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return [0, 0]

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return [x, y]


# return x
def _x(point):
    return point[0]


# return y
def _y(point):
    return point[1]


def scale(line1, factor):
    x1, x2 = scale_dimension(_x(line1[0]), _x(line1[1]), factor)
    y1, y2 = scale_dimension(_y(line1[0]), _y(line1[1]), factor)
    return [[x1, y1], [x2, y2]]


def scale_dimension(dim1, dim2, factor):
    base_length = dim2 - dim1
    ret1 = dim1 - (base_length * (factor - 1) / 2)
    ret2 = dim2 + (base_length * (factor - 1) / 2)
    return ret1, ret2


# https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
def ccw(A, B, C):
    # return (C.y-A.y) * (B.x-A.x) > (B.y-A.y) * (C.x-A.x)
    return (_y(C)-_y(A)) * (_x(B)-_x(A)) > (_y(B)-_y(A)) * (_x(C)-_x(A))


# Return true if line segments AB and CD intersect
def segment_intersect(line1, line2):  # A,B -> line1, C,D-> line2
    # return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    return ccw(line1[0], line2[0], line2[1]) != ccw(line1[1], line2[0], line2[1])\
       and ccw(line1[0], line1[1], line2[0]) != ccw(line1[0], line1[1], line2[1])


def findEdgeOfTargetCandleStickForLine1(df: pd.DataFrame, check_trend: str, targetCandleIndex: int) -> list:
    # Edge = None
    if check_trend == "UP":  # use bottom line
        py1 = df[3][targetCandleIndex]  # set y to the lowest
        # when py1 is using the lowest value
        if df[1][targetCandleIndex] > df[4][targetCandleIndex]:  # red candle
            # if it is red candle, we use close for limit1
            Edge = df[4][targetCandleIndex]
        else:  # green candle
            # if it is green candle, we use open for limit1
            Edge = df[1][targetCandleIndex]
    # elif check_trend == "DOWN":  # use top line
    else:  # trend is Down, use top line
        py1 = df[2][targetCandleIndex]  # set y to the highest
        # when py1 is using the highest value
        if df[1][targetCandleIndex] > df[4][targetCandleIndex]:  # red candle
            # if it is red candle, we use open for limit1
            Edge = df[1][targetCandleIndex]
        else:  # green candle
            # if it is green candle, we use close for limit1
            Edge = df[4][targetCandleIndex]

    return [py1, Edge]