import math
import numpy
import pandas
import decimal

# import stdio
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as pgPlot
from scipy.stats import linregress
# from sympy import Point, Line, Segment
import json
from src.helper001 import *
from src.helper001 import _x, _y

def futures_klines(**params):
    socks5_proxy = "54.249.188.136:1080"
    socks5_user = None
    socks5_pass = None
    socks5_ssl_verification = True

    client = Client(exchange="binance.com",
                    socks5_proxy_server=socks5_proxy,
                    socks5_proxy_user=socks5_user,
                    socks5_proxy_pass=socks5_pass,
                    socks5_proxy_ssl_verification=socks5_ssl_verification)

    return client._request_futures_api('get', 'klines', data=params)


# part 1
def BF_findSetOfLines(df: pd.DataFrame, specificXWickPoints:int=2, mustBE=False):
    print(df)
    check_trend = findTrend(df)
    setOfLines = []
    df_length = df.shape[0]
    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)
    # _test_setOfAllLines = []  # test only, comment or delete because it slows the process

    for i in range(0, df_length):
        print(i)
        # m vary depend on the current point on y axis, x is fixed
        # print(intervalList_TBD[i])
        px1 = i
        py1 = 0

        # set limit1
        limit1 = -1
        # check trend
        if check_trend == "UP":  # use bottom line
            py1 = df[3][i]  # set y to the lowest
            # when py1 is using the lowest value
            if df[1][i] > df[4][i]:  # red candle
                # if it is red candle, we use close for limit1
                limit1 = df[4][i]
            else:  # green candle
                # if it is green candle, we use open for limit1
                limit1 = df[1][i]
        elif check_trend == "DOWN":  # use top line
            py1 = df[2][i]  # set y to the highest
            # when py1 is using the highest value
            if df[1][i] > df[4][i]:  # red candle
                # if it is red candle, we use open for limit1
                limit1 = df[1][i]
            else:  # green candle
                # if it is green candle, we use close for limit1
                limit1 = df[4][i]

        # print(py1)
        for px2 in range(i+1, df_length):
            # if px1 == px2:
            #     continue

            limit2 = -1
            py2 = 0
            if check_trend == "UP":  # use bottom line
                py2 = df[3][px2]  # set y to the lowest

                # when py2 is using the lowest value
                if df[1][px2] > df[4][px2]:  # red candle
                    # if it is red candle, we use close for limit2
                    limit2 = df[4][px2]
                else:  # green candle
                    # if it is green candle, we use open for limit2
                    limit2 = df[1][px2]
            elif check_trend == "DOWN":  # use top line
                py2 = df[2][px2]  # set y to the highest
                # when py2 is using the highest value
                if df[1][i] > df[4][px2]:  # red candle
                    # if it is red candle, we use open for limit2
                    limit2 = df[1][px2]
                else:  # green candle
                    # if it is green candle, we use close for limit2
                    limit2 = df[4][px2]

            # TEST
            # setOfLines.append([[px1, py1], [px2, py2]])
            # TEST end

            # we have 2 points for making a line now
            loop1val_py1 = -1.0
            if check_trend == "UP":
            # if py1 <= limit1:
                loop1val_py1 = py1
            else:
                # tempint = py1
                loop1val_py1 = limit1
                limit1 = py1

            while (loop1val_py1 <= limit1):
                # print("loop1val_py1 <= limit1")
                # print(loop1val_py1)
                # print(limit1)
                # print("loop1val_py1 <= limit1 over")
                loop2val_py2 = -1.0
                # if py2 <= limit2:
                if check_trend == "UP":
                    loop2val_py2 = py2
                else:
                    loop2val_py2 = limit2
                    limit2 = py2

                while (loop2val_py2 <= limit2):
                    # print("loop1val_py2 <= limit2")
                    # print(loop2val_py2)
                    # print(limit2)
                    # print("loop1val_py2 <= limit2 over")
                    failed_conditions = False
                    df_length = df.shape[0]

                    # fromindex -> toindex
                    # loop3val_i -> every candle stick's X-axis
                    for loop3val_i in range(0, df_length):
                        # check whether a line intersect
                        # the body candle [(x, open), (x, close)]->vertical line

                        # TODO [?]
                        # [*] add conditions here
                        # Condition 1:
                        # if this is intersected with other candlestickbody, if not, add them to setOfLines

                        if segment_intersect([[loop3val_i, df[1][loop3val_i]], [loop3val_i, df[4][loop3val_i]]],
                                                  scale([[px1, loop1val_py1], [px2, loop2val_py2]], 100)):

                            failed_conditions = True # like failed intersection condition
                            break


                    # check whether a line intersect the body candle [(x, open), (x, close)]->vertical line
                    if failed_conditions:
                        # if this line intersect body, then it is not the line we wanted
                        # _test_setOfAllLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                        loop2val_py2 = loop2val_py2 + rounded_decimal_pow
                        continue
                    else:
                        # store the line
                        setOfLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                        # _test_setOfAllLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                        loop2val_py2 = loop2val_py2 + rounded_decimal_pow

                loop1val_py1 = loop1val_py1 + rounded_decimal_pow

    print("setOfLines: (passed intersection with candle body)")
    print(setOfLines)
    print(len(setOfLines))
    print()

    toBeReturnedSet = []

    # TODO: [!]
    # add final condition depending on trend up or trend down
    for setOfLines_index in range(0, len(setOfLines)):
        x = [_x(setOfLines[setOfLines_index][0]), _x(setOfLines[setOfLines_index][1])]
        y = [_y(setOfLines[setOfLines_index][0]), _y(setOfLines[setOfLines_index][1])]
        slope, intercept, r_value, p_value, std_err = linregress(x, y)


        # run a loop to check if the trendline and no candle is
        # above it when trending down
        # no candle is below if trending up
        belowORabove = False
        for px in range(0, df_length):
            py1 = 0
            if check_trend == "UP":  # trending up
                py1 = df[2][px]  # set y to the highest of current candlestick

                # y = mx + b
                if ((slope * px) + intercept) > py1:
                    belowORabove = True
                    break
            else:  # trending down
                py1 = df[3][px] # set y to the lowest of current candlestick

                # y = mx + b
                if ((slope * px) + intercept) < py1:
                    belowORabove = True
                    break

        if belowORabove:
            continue

        toBeReturnedSet.append(setOfLines[setOfLines_index])

    print("toBeReturnedSet: (passed if all candle is above or below)")
    print(toBeReturnedSet)

    # TODO [!]: find each line's wickpoints it touched
    toBeReturnedSet_intersectionWithOtherWickPoint = []
    # add wick point
    for setOfLines_index in range(0, len(toBeReturnedSet)):
        setOfIntersectedWick = []

        xList = [_x(toBeReturnedSet[setOfLines_index][0]), _x(toBeReturnedSet[setOfLines_index][1])]
        yList = [_y(toBeReturnedSet[setOfLines_index][0]), _y(toBeReturnedSet[setOfLines_index][1])]
        # p1 = [_x(toBeReturnedSet[setOfLines_index][0]), _y(toBeReturnedSet[setOfLines_index][0])]
        # p2 = [_x(toBeReturnedSet[setOfLines_index][1]), _y(toBeReturnedSet[setOfLines_index][1])]

        slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

        # run a loop that go through every candle in given dataframe
        # then find the wick point, and if it exists, add to the set
        for px in range(0, df_length):
            # init: used to check whether the point is startWickPoint <= [px, new_y] <= endWickPoint
            new_y = slope * px + intercept

            start, end = 0, 0
            # step1: find the start and end inteval [a, b] for the wickLine Segment at px
            if check_trend == "UP":  # use bottom line
                start = df[3][px]  # set y to the lowest
                if df[1][px] > df[4][px]:  # red candle
                    # use close when lowest
                    end = df[4][px]

                else:  # green candle
                    # use open when lowest
                    end = df[1][px]


                if start <= round(new_y, rounded_decimal) <= end:
                # if start == round(new_y, rounded_decimal):
                    # setOfIntersectedWick.append([px, new_y])
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])

            elif check_trend == "DOWN":  # use top line
                start = df[2][px]  # set y to the highest
                if df[1][px] > df[4][px]:  # red candle
                    # use open when highest
                    end = df[1][px]

                else:  # green candle
                    # use close when highest
                    end = df[4][px]

                # if px == 90:
                #     print("start & end:")
                #     print(start)
                #     print(end)
                #     print("start & end.")
                #     print("new_y:")
                #     print(new_y)
                #     print(round(new_y, rounded_decimal))
                #     print("new_y end.")

                if start >= round(new_y, rounded_decimal) >= end:
                # if start == round(new_y, rounded_decimal):
                    # setOfIntersectedWick.append([px, new_y])
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])


        toBeReturnedSet_intersectionWithOtherWickPoint.append(setOfIntersectedWick)

    # Test
    print("toBeReturnedSet_intersectionWithOtherWickPoint: (Passed if it intersect at least X wick points)")
    print(toBeReturnedSet_intersectionWithOtherWickPoint)
    print(len(toBeReturnedSet_intersectionWithOtherWickPoint))
    print("-=-=-=-=-=-=-=-=-")
    print(check_trend)
    # Test end

    # TODO [!]:
    # Condition 2:
    # for each line, determine num of wick intersection,
    # and store lines into their corresponding set
    # (set2, set3, set4 ... setN)
    lengthset = []
    for i in range(0, len(toBeReturnedSet)):
        lengthset.append(len(toBeReturnedSet_intersectionWithOtherWickPoint[i]))

    newTBRSet = []
    for i in range(0, len(toBeReturnedSet)):
        # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
        if mustBE is True and \
                specificXWickPoints == len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(toBeReturnedSet[i])
        elif specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(toBeReturnedSet[i])
    # max_limit = max(lengthset)
    # for i in range(0, len(toBeReturnedSet)):
    #     # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
    #     if max_limit <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
    #             newTBRSet.append(toBeReturnedSet[i])


    newTBRSet2 = []
    # TODO [!]: if trend UP and slope < 0, remove, and, if trend DOWN and slope > 0, remove
    for i in range(0, len(newTBRSet)):
        xList = [_x(toBeReturnedSet[i][0]), _x(toBeReturnedSet[i][1])]
        yList = [_y(toBeReturnedSet[i][0]), _y(toBeReturnedSet[i][1])]
        slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

        if check_trend == "UP":  # trending up
            # TODO [!]: if trend UP and slope < 0, remove, and, if trend DOWN and slope > 0, remove
            if slope < 0:
                continue
        elif check_trend == "DOWN":
            if slope > 0:
                continue

        newTBRSet2.append(newTBRSet[i])


    # TEST
    # print(_test_setOfAllLines)
    # TEST end
    # this set is filtered that only lines that not intersect with the other candle stick bodies
    # return setOfLines  # the original set of lines without new filterings (2 TODOs)
    # return toBeReturnedSet
    # return newTBRSet
    return newTBRSet2
    # return _test_setOfAllLines

# part 2
# Get top line if trend up, get bottom line if trend down, only changing b
# starting from the highest set, get top line if trend up, get bottom line if trend down,
# only changing b. Find opposite wick line with most wick intersections
def BF_findSetOfLines2(df: pd.DataFrame, setOfLines_orig: list, specificXWickPoints:int=0, mustBE=False):
    # note: df, [0] time, [1] open, [2] highest, [3] lowest, [4] close
    check_trend = findTrend(df)
    df_length = df.shape[0]

    # TODO: WARNING [!] if this method is gonna be running in a for loop, rounded decimal must be done
    # outside the loop, otherwise this increases the running time
    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)
    if check_trend == "DOWN":
        rounded_decimal_pow = rounded_decimal_pow * 1.0
    else:
        rounded_decimal_pow = rounded_decimal_pow * -1.0

    setOfLines2 = []
    setOfLines2_interval = []

    for i in range(0, len(setOfLines_orig)):
        p1, p2 = setOfLines_orig[i][0], setOfLines_orig[i][1]
        p3, p4 = None, None
        # xList = [_x(p1), _x(p2)]
        # yList = [_y(p1), _y(p2)]
        # slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

        # if check_trend == "UP":
        #     p3, p4 = [_x(p1), _y(p1) - intercept + highestPrice - b_m1],\
        #              [_x(p2), _y(p2) - intercept + highestPrice - b_m1]
        # elif check_trend == "DOWN":
        #     p3, p4 = [_x(p1), _y(p1) - intercept + lowestPrice + b_m1],\
        #              [_x(p2), _y(p2) - intercept + lowestPrice + b_m1]
        #
        # if p3 is not None and p4 is not None:
        #     setOfLines2.append([p3, p4])

        # loop1val_py1 = 0.001
        loop1val_py1 = rounded_decimal_pow
        failed_conditions = False
        while (True):  # the line
            p3, p4 = [_x(p1), _y(p1) - loop1val_py1], \
                     [_x(p2), _y(p2) - loop1val_py1]

            # fromindex -> toindex
            # loop3val_i -> every candle stick's X-axis
            count = 0
            for loop3val_i in range(0, df_length):
                if not segment_intersect([[loop3val_i, df[1][loop3val_i]], [loop3val_i, df[4][loop3val_i]]],
                                         scale([p3, p4], 100)):
                    count = count + 1

            if count == df_length:
                failed_conditions = True

            # check whether a line intersect the body candle [(x, open), (x, close)]->vertical line
            if failed_conditions:
                # if this line intersect body, then it is not the line we wanted

                # _test_setOfAllLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                # loop1val_py1 = loop1val_py1 + 0.1
                setOfLines2.append([p3, p4])
                setOfLines2_interval.append(loop1val_py1)
                break

            # loop1val_py1 = loop1val_py1 + 0.001
            loop1val_py1 = loop1val_py1 + rounded_decimal_pow

    # TODO [!]: find each line's wickpoints it touched
    toBeReturnedSet_intersectionWithOtherWickPoint = []
    # add wick point
    for setOfLines_index in range(0, len(setOfLines2)):
        interval = setOfLines2_interval[setOfLines_index]
        setOfIntersectedWick = []

        xList = [_x(setOfLines2[setOfLines_index][0]), _x(setOfLines2[setOfLines_index][1])]
        yList = [_y(setOfLines2[setOfLines_index][0]), _y(setOfLines2[setOfLines_index][1])]
        slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

        # run a loop that go through every candle in given dataframe
        # then find the wick point, and if it exists, add to the set
        for px in range(0, df_length):
            # init: used to check whether the point is startWickPoint <= [px, new_y] <= endWickPoint
            new_y = slope * px + intercept

            start, end = 0, 0
            # step1: find the start and end inteval [a, b] for the wickLine Segment at px
            if check_trend == "UP":  # use bottom line
                start = df[2][px]  # set y to the lowest
                if df[1][px] > df[4][px]:  # red candle
                    # use open when lowest
                    end = df[1][px]

                else:  # green candle
                    # use close when lowest
                    end = df[4][px]

                if start >= round(new_y, rounded_decimal) >= end:
                    # setOfIntersectedWick.append([px, new_y])
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])

            elif check_trend == "DOWN":  # use top line
                start = df[3][px]  # set y to the lowest
                if df[1][px] > df[4][px]:  # red candle
                    # use close when highest
                    end = df[4][px]

                else:  # green candle
                    # use open when highest
                    end = df[1][px]


                # if px == 16:
                #     print("start & end:")
                #     print(start)
                #     print(end)
                #     print("start & end.")
                #     print("new_y:")
                #     print(new_y)
                #     print(round(new_y, rounded_decimal))
                #     print("new_y end.")


                if start <= round(new_y, rounded_decimal) <= end:
                    # setOfIntersectedWick.append([px, new_y])
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])

        toBeReturnedSet_intersectionWithOtherWickPoint.append(setOfIntersectedWick)

    # print("wickSet:")
    # print(toBeReturnedSet_intersectionWithOtherWickPoint)


    newTBRSet = []
    for i in range(0, len(setOfLines2)):
        # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
        if mustBE is True and \
                specificXWickPoints == len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(setOfLines2[i])
        elif specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(setOfLines2[i])

    # return setOfLines2
    print("method2 return:")
    print(newTBRSet)
    return newTBRSet

# part 3
# Find third line, condition: Max wick point intersection, minimize body interaction.
def BF_findSetOfLines3(df: pd.DataFrame, setOfLines1: list, setOfLines2: list):
    # plan: get all potential lines between line1 and line2 we found
    # and record its number of wick intersection and number of body interaction
    # get an array that compute the equation:
    # result = number of wick intersection * weight - number of body interaction * weight
    # where weight i will place 1 for now
    # max(that array) would be the optimized line we wanted? [!] might need better

    # note: df, [0] time, [1] open, [2] highest, [3] lowest, [4] close
    check_trend = findTrend(df)
    df_length = df.shape[0]

    # TODO: WARNING [!] if this method is gonna be running in a for loop, rounded decimal must be done
    # outside the loop, otherwise this increases the running time
    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)
    posOrNeg = 1.0
    if check_trend == "DOWN":
        posOrNeg = 1.0
    else:
        posOrNeg = -1.0

    # rounded_decimal_pow = rounded_decimal_pow * posOrNeg
    rounded_decimal_pow = rounded_decimal_pow

    setOfLines3 = []
    setOfLines3_recordedVal = []
    setOfLine3_count = []

    for i in range(0, len(setOfLines1)):
        # potentialLines3set_between_1n2 = []
        # potentialLines3set_between_1n2_recordedVal = []
        p1, p2 = setOfLines1[i][0], setOfLines1[i][1]  # line1
        p3, p4 = setOfLines2[i][0], setOfLines2[i][1]  # line2
        p5, p6 = None, None

        diff = abs(_y(p1)-_y(p3))


        # loop1val_py1 = 0.001
        loop1val_py1 = rounded_decimal_pow
        failed_conditions = False
        while (loop1val_py1 < diff):  # the line
            p5, p6 = [_x(p1), _y(p1) - loop1val_py1 * posOrNeg], \
                     [_x(p2), _y(p2) - loop1val_py1 * posOrNeg]

            xList = [_x(p5), _x(p6)]
            yList = [_y(p5), _y(p6)]
            slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

            # fromindex -> toindex
            # loop3val_i -> every candle stick's X-axis
            seg_count = 0
            wick_count = 0
            for px in range(0, df_length):
                if segment_intersect([[px, df[1][px]], [px, df[4][px]]],
                                         scale([p3, p4], 100)):
                    seg_count = seg_count + 1

                # check num of intersection
                # init: used to check whether the point is startWickPoint <= [px, new_y] <= endWickPoint
                new_y = slope * px + intercept

                start, end = 0, 0
                # step1: find the start and end inteval [a, b] for the wickLine Segment at px
                if check_trend == "UP":  # use bottom line
                    # Top wick only
                    # start = df[2][px]  # set y to the lowest
                    # if df[1][px] > df[4][px]:  # red candle
                    #     # use open when lowest
                    #     end = df[1][px]
                    #
                    # else:  # green candle
                    #     # use close when lowest
                    #     end = df[4][px]
                    #
                    # if start >= round(new_y, rounded_decimal) >= end:
                    #     wick_count = wick_count + 1

                    # Bottom wick only
                    start = df[3][px]  # set y to the lowest
                    if df[1][px] > df[4][px]:  # red candle
                        # use close when highest
                        end = df[4][px]

                    else:  # green candle
                        # use open when highest
                        end = df[1][px]

                    if start <= round(new_y, rounded_decimal) <= end:
                        wick_count = wick_count + 1

                elif check_trend == "DOWN":  # use top line
                    # Bottom wick only
                    # start = df[3][px]  # set y to the lowest
                    # if df[1][px] > df[4][px]:  # red candle
                    #     # use close when highest
                    #     end = df[4][px]
                    #
                    # else:  # green candle
                    #     # use open when highest
                    #     end = df[1][px]
                    #
                    # if start <= round(new_y, rounded_decimal) <= end:
                    #     wick_count = wick_count + 1

                    # Top wick only
                    start = df[2][px]  # set y to the lowest
                    if df[1][px] > df[4][px]:  # red candle
                        # use open when lowest
                        end = df[1][px]

                    else:  # green candle
                        # use close when lowest
                        end = df[4][px]

                    if start >= round(new_y, rounded_decimal) >= end:
                        wick_count = wick_count + 1

            # potentialLines3set_between_1n2.append([p5, p6])
            # potentialLines3set_between_1n2_recordedVal.append(wick_count-seg_count)
            setOfLines3.append([p5, p6])
            setOfLines3_recordedVal.append(wick_count-seg_count)

            # loop1val_py1 = loop1val_py1 + 0.001
            loop1val_py1 = loop1val_py1 + rounded_decimal_pow

        # if len(potentialLines3set_between_1n2_recordedVal) > 0:
        #     limit = max(potentialLines3set_between_1n2_recordedVal)
        #     for i in range(0, len(potentialLines3set_between_1n2)):
        #         # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
        #         # TODO
        #         if potentialLines3set_between_1n2_recordedVal[i] >= limit:
        #             setOfLines3.append(potentialLines3set_between_1n2[i])
        #             setOfLines3_recordedVal.append(potentialLines3set_between_1n2_recordedVal[i])
        setOfLine3_count.append(len(setOfLines3))


    print("num of wick point touched - num of intersection with body")
    print(len(setOfLines3))
    print(setOfLines3_recordedVal)
    print(setOfLine3_count)
    newTBRSet = []
    last_index_exit = -1
    if len(setOfLines3_recordedVal) > 0:
        limit = max(setOfLines3_recordedVal)
        for i in range(0, len(setOfLines3)):
            # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
            # TODO
            if setOfLines3_recordedVal[i] >= limit:
                newTBRSet.append(setOfLines3[i])
                last_index_exit = i

        for j in range(0, len(setOfLine3_count)):
            if last_index_exit < setOfLine3_count[j]:
                last_index_exit = j+1
                break

    # return setOfLines3
    return [newTBRSet, last_index_exit]


# part 4
# the conditions for line 4 are: line4 must be as close to twice the distance
# from line3 as line3 is from top (bottom) wick line
# and, additionally, line4 must have to most candlewick intersections
def BF_findSetOfLines4(df: pd.DataFrame, setOfLines1: list, setOfLines2: list, setOfLines3: list):
    check_trend = findTrend(df)
    df_length = df.shape[0]
    setOfxDistLines = []
    setOfx2DistLines = []
    testLines = []  # this is used to print wanted setOfLines, can be removed

    # TODO: WARNING [!] if this method is gonna be running in a for loop, rounded decimal must be done
    # outside the loop, otherwise this increases the running time
    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)
    posOrNeg = 1.0
    if check_trend == "DOWN":
        posOrNeg = 1.0
    else:
        posOrNeg = -1.0

    # rounded_decimal_pow = rounded_decimal_pow * posOrNeg
    rounded_decimal_pow = rounded_decimal_pow

    setOfLines4 = []
    setOfLines4_recordedVal = []

    # [?] plan
    y_max = np.max(df[2])
    y_min = np.min(df[3])


    for i in range(0, len(setOfLines1)):
        p1, p2 = setOfLines1[i][0], setOfLines1[i][1]  # line 1
        p3, p4 = setOfLines2[i][0], setOfLines2[i][1]  # line 2

        # translate line1 by 5% before calculating xDist_1
        # new_y = 5% of y-axis abs(line_y1 - line_y2),
        # translate line_y1 by new_y -> [px, line_y1 + new_y], after 2 line, when x1dist is defined
        # new_y = abs(abs(_y(p1)) - abs(_y(p3))) * 0.05 * posOrNeg
        new_y = abs(y_max - y_min) * 0.05 * posOrNeg
        if check_trend == "DOWN":
            # translation_high = abs(abs(_y(p1)) - abs(y_max)) * posOrNeg
            if df[2][_x(p1)] > df[2][_x(p2)]:
                translation_high = abs(abs(_y(p1)) - abs(df[2][_x(p1)])) * posOrNeg
            else:
                translation_high = abs(abs(_y(p1)) - abs(df[2][_x(p2)])) * posOrNeg
        else:
            if df[3][_x(p1)] > df[3][_x(p2)]:
                translation_high = abs(abs(_y(p1)) - abs(df[3][_x(p1)])) * posOrNeg
            else:
                translation_high = abs(abs(_y(p1)) - abs(df[3][_x(p2)])) * posOrNeg
        # tp1, tp2 = [_x(p1), _y(p1)+new_y], [_x(p2), _y(p2)+new_y]  # new line 1
        tp1, tp2 = [_x(p1), _y(p1)+translation_high+new_y], [_x(p2), _y(p2)+translation_high+new_y]  # new line 1
        # tp1, tp2 = [_x(p1), _y(p1)+translation_high], [_x(p2), _y(p2)+translation_high]  # new line 1
        testLines.append([tp1, tp2])

        # run a loop go through
        for j in range(0, len(setOfLines3)):
            p5, p6 = setOfLines3[j][0], setOfLines3[j][1]  # line 3
            x_dist = 1 * abs(_y(p1) - _y(p5))
            # diff = _y(p5) - _y(p3)
            diff = 2 * abs(_y(p1) - _y(p5))
            # print(diff)
            x_distLine = [[_x(p5), _y(p5) - x_dist * posOrNeg],
                          [_x(p6), _y(p6) - x_dist * posOrNeg]
                          ]
            x2_distLine = [[_x(p5), _y(p5) - diff * posOrNeg],
                           [_x(p6), _y(p6) - diff * posOrNeg]
                          ]
            setOfxDistLines.append(x_distLine)
            setOfx2DistLines.append(x2_distLine)

            possibleLine4Set = []
            possibleLine4Set_recordVal = []
            # loop1val_py1 = 0.001
            # loop1val_py1 = rounded_decimal_pow
            loop1val_py1 = x_dist
            failed_conditions = False
            while (loop1val_py1 < diff):  # the line
                p7, p8 = [_x(p5), _y(p5) - loop1val_py1 * posOrNeg], \
                         [_x(p6), _y(p6) - loop1val_py1 * posOrNeg]

                xList = [_x(p7), _x(p8)]
                yList = [_y(p7), _y(p8)]
                slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

                # fromindex -> toindex
                # loop3val_i -> every candle stick's X-axis
                seg_count = 0
                wick_count = 0
                for px in range(0, df_length):
                    if segment_intersect([[px, df[1][px]], [px, df[4][px]]],
                                         scale([p7, p8], 100)):
                        seg_count = seg_count + 1


                    # check num of intersection
                    # init: used to check whether the point is startWickPoint <= [px, new_y] <= endWickPoint
                    new_y = slope * px + intercept

                    start, end = 0, 0
                    # step1: find the start and end inteval [a, b] for the wickLine Segment at px
                    if check_trend == "UP":  # use bottom line
                        # Top wick only
                        start = df[2][px]  # set y to the lowest
                        if df[1][px] > df[4][px]:  # red candle
                            # use open when lowest
                            end = df[1][px]

                        else:  # green candle
                            # use close when lowest
                            end = df[4][px]

                        if start >= round(new_y, rounded_decimal) >= end:
                            wick_count = wick_count + 1

                        # # Bottom wick only
                        # start = df[3][px]  # set y to the lowest
                        # if df[1][px] > df[4][px]:  # red candle
                        #     # use close when highest
                        #     end = df[4][px]
                        #
                        # else:  # green candle
                        #     # use open when highest
                        #     end = df[1][px]
                        #
                        # if start <= round(new_y, rounded_decimal) <= end:
                        #     wick_count = wick_count + 1

                    elif check_trend == "DOWN":  # use top line
                        # Bottom wick only
                        start = df[3][px]  # set y to the lowest
                        if df[1][px] > df[4][px]:  # red candle
                            # use close when highest
                            end = df[4][px]

                        else:  # green candle
                            # use open when highest
                            end = df[1][px]

                        if start <= round(new_y, rounded_decimal) <= end:
                            wick_count = wick_count + 1

                        # # Top wick only
                        # start = df[2][px]  # set y to the lowest
                        # if df[1][px] > df[4][px]:  # red candle
                        #     # use open when lowest
                        #     end = df[1][px]
                        #
                        # else:  # green candle
                        #     # use close when lowest
                        #     end = df[4][px]
                        #
                        # if start >= round(new_y, rounded_decimal) >= end:
                        #     wick_count = wick_count + 1

                possibleLine4Set.append([p7, p8])
                # possibleLine4Set_recordVal.append(wick_count - seg_count)
                possibleLine4Set_recordVal.append(wick_count)

                # loop1val_py1 = loop1val_py1 + 0.001
                loop1val_py1 = loop1val_py1 + rounded_decimal_pow

            # pick line 4 that had the highest max
            # meaning, each line4 was the max for the corresponding line3's set of line4s
            # but, across line3s, there will be at least one line4 that is the max of those maxes
            # if there is more than one line4 here with same ultimate max value
            # pick the one closest to 1x dist that's it
            # this will give you one line3 and one line4
            if len(possibleLine4Set) > 0:
                tempList = []
                limit = max(possibleLine4Set_recordVal)
                for i in range(0, len(possibleLine4Set)):
                    if possibleLine4Set_recordVal[i] >= limit:
                        tempList.append(possibleLine4Set[i])

                if len(tempList) == 1:
                    setOfLines4.append(tempList[0])
                    setOfLines4_recordedVal.append(limit)
                elif len(tempList) > 1:
                    # pick the closest line
                    minDist = float('inf')
                    resultIndex = -1
                    for i in range(0, len(tempList)):
                        # temp_p1, temp_p2 = tempList[i][0], tempList[i][1]
                        temp_p1 = tempList[i][0]
                        if abs(_y(temp_p1) - _y(x_distLine[0])) < minDist:
                            minDist = abs(_y(temp_p1) - _y(x_distLine[0]))
                            resultIndex = i

                    if resultIndex != -1:
                        setOfLines4.append(tempList[resultIndex])
                        setOfLines4_recordedVal.append(limit)

                # else:
                    # ?


    print("setOfLines4:")
    print(setOfLines4)
    print(setOfLines4_recordedVal)
    newTBRSet = []
    limit = max(setOfLines4_recordedVal)
    for i in range(0, len(setOfLines4)):
        # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
        # TODO
        if setOfLines4_recordedVal[i] >= limit:
            newTBRSet.append(setOfLines4[i])

    # return [newTBRSet, setOfxDistLines, setOfx2DistLines]
    return [newTBRSet, setOfxDistLines, setOfx2DistLines, testLines, limit]  # for test only
    # return setOfLines4


def BF_findBestLine(df: pd.DataFrame, AllSetOfLines4: list):

    return


def drawLines(df: pd.DataFrame, figure1: pgPlot.Figure, l1: list,
              fromIndex: int, toIndex: int, name: str = "slope"):
    def readLine1(df: pd.DataFrame, l2: list) -> list:
        l3 = []
        for i in l2:
            xList = []
            yList = []
            tsList = []
            xList.append(i[0][0])
            xList.append(i[1][0])
            yList.append(i[0][1])
            yList.append(i[1][1])
            l3.append([xList, yList, tsList])

        return l3

    timestamplist = [df[0][0], df[0][toIndex-fromIndex-1]]
    dateTimelist = [convertTimeStamp2DateTime(i) for i in timestamplist]
    l2 = readLine1(df, l1)
    strName1 = name + " " + "1"
    count = 1

    for i in l2:
        # timestamplist = [int(j) for j in i[2]]
        # dateTimelist = [convertTimeStamp2DateTime(i) for i in timestamplist]
        x = [int(j)+fromIndex for j in i[0]]
        y = i[1]
        # https://stackoverflow.com/questions/9538525/calculating-slopes-in-numpy-or-scipy
        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        # y = mx + b
        new_x_list = [fromIndex, toIndex-1]
        # new_y_list = [slope * 0 + intercept, slope * (toIndex-fromIndex) + intercept]
        new_y_list = [slope * fromIndex + intercept, slope * (toIndex-1) + intercept]

        figure1.add_trace(
            # pgPlot.Scatter(x=x, y=y, mode='lines', name=strName1))
            pgPlot.Scatter(x=new_x_list, y=new_y_list, mode='lines', name=strName1))
            # pgPlot.Scatter(x=dateTimelist, y=new_y_list, mode='lines', name=strName1))

        count = count + 1
        strName1 = name + " " + str(count)


def visualization(df: pd.DataFrame) -> pgPlot.Figure:
    timestamplist = df[0].tolist()
    timestamplist = [int(i) for i in timestamplist]
    dateTimelist = [convertTimeStamp2DateTime(i) for i in timestamplist]
    openList = df[1].tolist()
    openList = [float(i) for i in openList]
    priceList = df[4].tolist()
    priceList = [float(i) for i in priceList]
    highList = df[2].tolist()
    highList = [float(i) for i in highList]
    lowList = df[3].tolist()
    lowList = [float(i) for i in lowList]

    # fig = pgPlot.Figure(data=[pgPlot.Candlestick(x=dateTimelist,
    #                                              open=openList, high=highList,
    #                                              low=lowList, close=priceList)])
    fig = pgPlot.Figure(data=[pgPlot.Candlestick(x=df.index,
                                                 open=openList, high=highList,
                                                 low=lowList, close=priceList)])

    return fig

#TODO- clean up code by 1) confirming/eliminating all other current TODOs
#TODO - benchmark to determine number of candlesticks for which algorithm becomes slow (slow = more than 20 secs)
# Python timeit
#TODO - run algorithm with sliding window size of 1 candlestick (same range from-to)
#TODO - extend lines after solution found
####TODO - make code readable by adding comments where you can
def run_algorithm(client, symbol, start_stamp, end_stamp, from_index=None, to_index=None):
    st = convertDateStr2TimeStamp(start_stamp)
    et = convertDateStr2TimeStamp(end_stamp)
    fromIndex, toIndex = 120, 220
    klines_1m = client.futures_klines(symbol=symbol, interval="1m", startTime=st, endTime=et, limit=1000)
    array_response = np.array(klines_1m).tolist()
    df_prices = pd.DataFrame(klines_1m)
    df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: int(x))
    df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
    df_prices.iloc[:, 2] = df_prices.iloc[:, 2].apply(lambda x: float(x))
    df_prices.iloc[:, 3] = df_prices.iloc[:, 3].apply(lambda x: float(x))
    df_prices.iloc[:, 4] = df_prices.iloc[:, 4].apply(lambda x: float(x))
    print(f"KLINES: {df_prices}")
    tempDF = df_prices.iloc[fromIndex:toIndex]

    df1 = pd.DataFrame()
    frames = [tempDF, df1]
    tempDF = pd.concat(frames, ignore_index=True)
    print(df_prices.to_string())
    # setLines = BF_findSetOfLines(tempDF)
    setLines = BF_findSetOfLines(tempDF, 2, True)
    graph = visualization(df_prices)
    setLines2 = BF_findSetOfLines2(tempDF, setLines)
    if len(setLines) == len(setLines2):
        AllSetOfLines4 = []
        AllSetOfLines4_num_wickIntersected = []
        for i in range(0, len(setLines)):
            temp1, temp2 = [setLines[i]], [setLines2[i]]
            setLines3 = BF_findSetOfLines3(tempDF, temp1, temp2)
            for j in range(0, len(setLines3[0])):
                temp3 = [setLines3[0][j]]
                setLines4 = BF_findSetOfLines4(tempDF, temp1, temp2, temp3)
                num_wickIntersected = setLines4[-1]
                # AllSetOfLines4.append([setLines4, temp3, temp2, temp1])
                AllSetOfLines4.append([temp1, temp2, temp3, setLines4])
                AllSetOfLines4_num_wickIntersected.append(num_wickIntersected)

        max_wick = max(AllSetOfLines4_num_wickIntersected)
        newTBRSet = []
        for i in range(0, len(AllSetOfLines4)):
            # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
            # TODO
            if AllSetOfLines4_num_wickIntersected[i] >= max_wick:
                newTBRSet.append(AllSetOfLines4[i])

        for i in range(0, len(newTBRSet)):
            temp1 = newTBRSet[i][0]
            temp2 = newTBRSet[i][1]
            temp3 = newTBRSet[i][2]
            setLines4 = newTBRSet[i][3]

            drawLines(tempDF, graph, temp1, fromIndex, toIndex, "L1_")
            drawLines(tempDF, graph, temp2, fromIndex, toIndex, "L2_")
            drawLines(tempDF, graph, temp3, fromIndex, toIndex, "L3_")
            drawLines(tempDF, graph, setLines4[0], fromIndex, toIndex, "L4_")
            drawLines(tempDF, graph, setLines4[1], fromIndex, toIndex, "L3_xdist_")
            drawLines(tempDF, graph, setLines4[2], fromIndex, toIndex, "L3_x2dist_")
            drawLines(tempDF, graph, setLines4[3], fromIndex, toIndex, "L1_new_")

        graph.show()



# if __name__ == "__main__":
#     pass
    # get real time DF
    # klines_1m = futures_klines(symbol="BTCUSDT", limit=1000, interval=Client.KLINE_INTERVAL_1MINUTE)
    # array_response = np.array(klines_1m)
    # list_response = array_response[:, [0, 4]].tolist()  # subset by open timestamp and 'close' fields
    # df_prices = pd.DataFrame(list_response)  # convert to dataframe
    # get real time DF ends


    # df_prices = pd.read_pickle("t1.txt")
    # df_prices = pd.read_json("df_prices_DOGEUSDT.json", orient='split')
    # df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: int(x))
    # df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
    # df_prices.iloc[:, 2] = df_prices.iloc[:, 2].apply(lambda x: float(x))
    # df_prices.iloc[:, 3] = df_prices.iloc[:, 3].apply(lambda x: float(x))
    # df_prices.iloc[:, 4] = df_prices.iloc[:, 4].apply(lambda x: float(x))
    #
    #
    # # print(df_prices.to_string())
    # fromIndex, toIndex = 120, 220        # UP DOGEUSDT
    # # fromIndex, toIndex = 400, 496      # Down  pd.read_pickle("t1.txt")
    #
    # tempDF = df_prices.iloc[fromIndex:toIndex]
    #
    # df1 = pd.DataFrame()
    # frames = [tempDF, df1]
    # tempDF = pd.concat(frames, ignore_index=True)
    # print(df_prices.to_string())
    # # setLines = BF_findSetOfLines(tempDF)
    # setLines = BF_findSetOfLines(tempDF, 2, True)
    # # setLines = BF_findSetOfLines(tempDF, 3)
    # # setLines = BF_findSetOfLines(tempDF, 4)
    #
    #
    # # print("setLines:")
    # # print(setLines)
    # # print("------------")
    #
    # graph = visualization(df_prices)
    # setLines2 = BF_findSetOfLines2(tempDF, setLines)
    # if len(setLines) == len(setLines2):
    #     AllSetOfLines4 = []
    #     AllSetOfLines4_num_wickIntersected = []
    #     for i in range(0, len(setLines)):
    #         temp1, temp2 = [setLines[i]], [setLines2[i]]
    #         setLines3 = BF_findSetOfLines3(tempDF, temp1, temp2)
    #         for j in range(0, len(setLines3[0])):
    #             temp3 = [setLines3[0][j]]
    #             setLines4 = BF_findSetOfLines4(tempDF, temp1, temp2, temp3)
    #             num_wickIntersected = setLines4[-1]
    #             # AllSetOfLines4.append([setLines4, temp3, temp2, temp1])
    #             AllSetOfLines4.append([temp1, temp2, temp3, setLines4])
    #             AllSetOfLines4_num_wickIntersected.append(num_wickIntersected)
    #
    #             # drawing part
    #             # step1, reset graph
    #             # step2, draw lines and show graph
    #             # graph = visualization(df_prices)
    #             # drawLines(tempDF, graph, temp1,  fromIndex, toIndex, "L1_")
    #             # drawLines(tempDF, graph, temp2, fromIndex, toIndex, "L2_")
    #             # drawLines(tempDF, graph, temp3, fromIndex, toIndex, "L3_"+str(setLines3[1])+"_")
    #             # drawLines(tempDF, graph, setLines4[0], fromIndex, toIndex, "L4_")
    #             # drawLines(tempDF, graph, setLines4[1], fromIndex, toIndex, "L3_xdist_")
    #             # drawLines(tempDF, graph, setLines4[2], fromIndex, toIndex, "L3_x2dist_")
    #             # drawLines(tempDF, graph, setLines4[3], fromIndex, toIndex, "L1_new_")
    #             # graph.show()
    #             # stdio.readInt()
    #
    #     max_wick = max(AllSetOfLines4_num_wickIntersected)
    #     newTBRSet = []
    #     for i in range(0, len(AllSetOfLines4)):
    #         # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
    #         # TODO
    #         if AllSetOfLines4_num_wickIntersected[i] >= max_wick:
    #             newTBRSet.append(AllSetOfLines4[i])
    #
    #     for i in range(0, len(newTBRSet)):
    #         temp1 = newTBRSet[i][0]
    #         temp2 = newTBRSet[i][1]
    #         temp3 = newTBRSet[i][2]
    #         setLines4 = newTBRSet[i][3]
    #
    #         drawLines(tempDF, graph, temp1,  fromIndex, toIndex, "L1_")
    #         drawLines(tempDF, graph, temp2, fromIndex, toIndex, "L2_")
    #         drawLines(tempDF, graph, temp3, fromIndex, toIndex, "L3_")
    #         drawLines(tempDF, graph, setLines4[0], fromIndex, toIndex, "L4_")
    #         drawLines(tempDF, graph, setLines4[1], fromIndex, toIndex, "L3_xdist_")
    #         drawLines(tempDF, graph, setLines4[2], fromIndex, toIndex, "L3_x2dist_")
    #         drawLines(tempDF, graph, setLines4[3], fromIndex, toIndex, "L1_new_")
    #
    #     graph.show()


    # drawLines(tempDF, graph, setLines,  fromIndex, toIndex, "L1_")
    # drawLines(tempDF, graph, setLines2, fromIndex, toIndex, "L2_")
    # drawLines(tempDF, graph, setLines3[0], fromIndex, toIndex, "L3_"+str(setLines3[1])+"_")
    # drawLines(tempDF, graph, setLines4[0], fromIndex, toIndex, "L4_")
    # drawLines(tempDF, graph, setLines4[1], fromIndex, toIndex, "L3_xdist_")
    # drawLines(tempDF, graph, setLines4[2], fromIndex, toIndex, "L3_x2dist_")
    # drawLines(tempDF, graph, setLines4[3], fromIndex, toIndex, "L1_new_")
    # graph.show()