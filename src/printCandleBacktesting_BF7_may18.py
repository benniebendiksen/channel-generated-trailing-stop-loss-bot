import math
from unicorn_binance_rest_api.manager import BinanceRestApiManager as Client
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as pgPlot
from scipy.stats import linregress
from src.helper001 import *
from src.helper001 import _x, _y
from src.pptGenerateForVisualization import generatePPT
import os


# part 1
def BF_findSetOfLines(df: pd.DataFrame, specificXWickPoints: int = 2, mustBE=False, stepRatio=0.2):
    # print(df)
    check_trend = findTrend(df)
    # print(check_trend)
    setOfLines = []
    df_length = df.shape[0]
    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)

    # part1, return a set of lines that do not intersect with any candlestick body
    for px1 in range(0, df_length):
        py1 = 0

        # set limit1, edgeList [py1, limit1]
        edgeList = findEdgeOfTargetCandleStickForLine1(df, check_trend, px1)
        py1 = edgeList[0]
        limit1 = edgeList[1]
        edgeList = None

        for px2 in range(px1+1, df_length):
            edgeList = findEdgeOfTargetCandleStickForLine1(df, check_trend, px2)
            py2 = edgeList[0]
            limit2 = edgeList[1]
            edgeList = None

            if np.abs(limit1 - py1) != 0.0:
                step_abs_val1 = np.abs(limit1 - py1) * stepRatio
            else:
                step_abs_val1 = rounded_decimal_pow

            if check_trend == "UP":
                loop1val_py1 = py1
            else:
                loop1val_py1 = limit1
                limit1 = py1

            while (loop1val_py1 <= limit1):
                if check_trend == "UP":
                    loop2val_py2 = py2
                else:
                    loop2val_py2 = limit2
                    limit2 = py2

                if np.abs(limit2 - py2) != 0.0:
                    step_abs_val2 = np.abs(limit2 - py2) * stepRatio
                else:
                    step_abs_val2 = rounded_decimal_pow

                while (loop2val_py2 <= limit2):
                    failed_conditions = False
                    df_length = df.shape[0]

                    # loop3val_i -> every candle stick's X-axis
                    for loop3val_i in range(0, df_length):
                        # [*] can add extra conditions here if needed
                        # Condition 1:
                        # if this is intersected with other candlestickbody, if not, add them to setOfLines
                        if segment_intersect([[loop3val_i, df[1][loop3val_i]], [loop3val_i, df[4][loop3val_i]]],
                                                  scale([[px1, loop1val_py1], [px2, loop2val_py2]], 100)):

                            failed_conditions = True # like failed intersection condition
                            break


                    # check whether a line intersect the body candle [(x, open), (x, close)]->vertical line
                    if failed_conditions:
                        loop2val_py2 = loop2val_py2 + step_abs_val2
                        continue
                    else:
                        # store the line
                        setOfLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                        loop2val_py2 = loop2val_py2 + step_abs_val2

                loop1val_py1 = loop1val_py1 + step_abs_val1

    toBeReturnedSet = []

    # part2, return a set of lines that ensure all candles are above or below the line depend on trend
    # add final condition depending on trend up or trend down
    # all lines must be below or above depend on the trend
    for setOfLines_index in range(0, len(setOfLines)):
        x = [_x(setOfLines[setOfLines_index][0]), _x(setOfLines[setOfLines_index][1])]
        y = [_y(setOfLines[setOfLines_index][0]), _y(setOfLines[setOfLines_index][1])]
        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        # run a loop to check if the trendline and no candle is
        # above it when trending down
        # no candle is below if trending up
        belowORabove = False
        for px in range(0, df_length):
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

    # part3, return a set that contain wickpoint interested based on the line's index
    # find each line's wickpoints it touched, and add those wick point to a set
    toBeReturnedSet_intersectionWithOtherWickPoint = []
    for setOfLines_index in range(0, len(toBeReturnedSet)):
        setOfIntersectedWick = []

        xList = [_x(toBeReturnedSet[setOfLines_index][0]), _x(toBeReturnedSet[setOfLines_index][1])]
        yList = [_y(toBeReturnedSet[setOfLines_index][0]), _y(toBeReturnedSet[setOfLines_index][1])]

        slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

        # run a loop that go through every candle in given dataframe
        # then find the wick point, and if it exists, add to the set
        for px in range(0, df_length):
            # init: used to check whether the point is startWickPoint <= [px, new_y] <= endWickPoint
            new_y = slope * px + intercept

            # step1: find the start and end inteval [a, b] for the wickLine Segment at px
            EdgeList = findEdgeOfTargetCandleStickForLine1(df, check_trend, px)
            start = EdgeList[0]  # py
            end = EdgeList[1]  # limit
            if check_trend == "UP":  # use bottom line
                if start <= round(new_y, rounded_decimal) <= end:
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])
            elif check_trend == "DOWN":  # use top line
                if start >= round(new_y, rounded_decimal) >= end:
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])

        toBeReturnedSet_intersectionWithOtherWickPoint.append(setOfIntersectedWick)

    # [*] or add conditions outside the last loop
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


    newTBRSet2 = []
    # part4, return a set of line where the line goes up or down depend on the trend
    # if trend UP and slope < 0, remove, and, if trend DOWN and slope > 0, remove
    for i in range(0, len(newTBRSet)):
        xList = [_x(toBeReturnedSet[i][0]), _x(toBeReturnedSet[i][1])]
        yList = [_y(toBeReturnedSet[i][0]), _y(toBeReturnedSet[i][1])]
        slope, intercept, r_value, p_value, std_err = linregress(xList, yList)

        if check_trend == "UP":  # trending up
            # if trend UP and slope < 0, remove, and, if trend DOWN and slope > 0, remove
            if slope < 0:
                continue
        elif check_trend == "DOWN":
            if slope > 0:
                continue

        newTBRSet2.append(newTBRSet[i])

    return newTBRSet2

# part 2
# Get top line if trend up, get bottom line if trend down, only changing b
# starting from the highest set, get top line if trend up, get bottom line if trend down,
# only changing b. Find opposite wick line with most wick intersections
def BF_findSetOfLines2(df: pd.DataFrame, setOfLines_orig: list, specificXWickPoints:int=0, mustBE=False):
    # note: df, [0] time, [1] open, [2] highest, [3] lowest, [4] close
    check_trend = findTrend(df)
    df_length = df.shape[0]

    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)
    if check_trend == "DOWN":
        rounded_decimal_pow = rounded_decimal_pow * 1.0
    else:
        rounded_decimal_pow = rounded_decimal_pow * -1.0

    setOfLines2 = []

    for i in range(0, len(setOfLines_orig)):
        p1, p2 = setOfLines_orig[i][0], setOfLines_orig[i][1]

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
                setOfLines2.append([p3, p4])
                break

            loop1val_py1 = loop1val_py1 + rounded_decimal_pow

    # find each line's wickpoints it touched
    toBeReturnedSet_intersectionWithOtherWickPoint = []
    for setOfLines_index in range(0, len(setOfLines2)):
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

                if start <= round(new_y, rounded_decimal) <= end:
                    setOfIntersectedWick.append([px, round(new_y, rounded_decimal)])

        toBeReturnedSet_intersectionWithOtherWickPoint.append(setOfIntersectedWick)

    newTBRSet = []
    for i in range(0, len(setOfLines2)):
        if mustBE is True and \
                specificXWickPoints == len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(setOfLines2[i])
        elif specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(setOfLines2[i])

    return newTBRSet

# part 3
# Find third line, condition: Max wick point intersection, minimize body interaction.
def BF_findSetOfLines3(df: pd.DataFrame, setOfLines1: list, setOfLines2: list, stepRatio=0.2):
    # plan: get all potential lines between line1 and line2 we found
    # and record its number of wick intersection and number of body interaction
    # get an array that compute the equation:
    # result = number of wick intersection * weight - number of body interaction * weight
    # where weight i will place 1 for now
    # max(that array) would be the optimized line we wanted? [!] might need better

    # note: df, [0] time, [1] open, [2] highest, [3] lowest, [4] close
    check_trend = findTrend(df)
    df_length = df.shape[0]

    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)

    if check_trend == "DOWN":
        posOrNeg = 1.0
    else:
        posOrNeg = -1.0

    setOfLines3 = []
    setOfLines3_recordedVal = []
    setOfLine3_count = []

    for i in range(0, len(setOfLines1)):
        p1, p2 = setOfLines1[i][0], setOfLines1[i][1]  # line1
        p3, p4 = setOfLines2[i][0], setOfLines2[i][1]  # line2


        # shift line1 by some distance depend on stepRatio and diff between line1 and line2
        diff = np.abs(_y(p1)-_y(p3))
        loop1val_py1 = rounded_decimal_pow

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
                    # Line touch Bottom wick only
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
                    # Line touch Top wick only
                    start = df[2][px]  # set y to the lowest
                    if df[1][px] > df[4][px]:  # red candle
                        # use open when lowest
                        end = df[1][px]

                    else:  # green candle
                        # use close when lowest
                        end = df[4][px]

                    if start >= round(new_y, rounded_decimal) >= end:
                        wick_count = wick_count + 1

            setOfLines3.append([p5, p6])
            setOfLines3_recordedVal.append(wick_count-seg_count)

            if diff != 0.0:
                loop1val_py1 = loop1val_py1 + diff*stepRatio
            else:
                loop1val_py1 = loop1val_py1 + rounded_decimal_pow

        setOfLine3_count.append(len(setOfLines3))

    newTBRSet = []
    last_index_exit = -1
    if len(setOfLines3_recordedVal) > 0:
        limit = max(setOfLines3_recordedVal)
        for i in range(0, len(setOfLines3)):
            if setOfLines3_recordedVal[i] >= limit:
                newTBRSet.append(setOfLines3[i])
                last_index_exit = i

        for j in range(0, len(setOfLine3_count)):
            if last_index_exit < setOfLine3_count[j]:
                last_index_exit = j+1
                break

    return [newTBRSet, last_index_exit]


# part 4
# the conditions for line 4 are: line4 must be as close to twice the distance
# from line3 as line3 is from top (bottom) wick line
# and, additionally, line4 must have to most candlewick intersections
def BF_findSetOfLines4(df: pd.DataFrame, setOfLines1: list,
                       setOfLines2: list, setOfLines3: list, stepRatio=0.2):
    check_trend = findTrend(df)
    df_length = df.shape[0]
    setOfxDistLines = []
    setOfx2DistLines = []
    newLine1Set = []  # this is used to print wanted setOfLines, can be removed

    rounded_decimal = find_decimals(df[1][0])
    rounded_decimal_pow = math.pow(0.1, rounded_decimal)

    if check_trend == "DOWN":
        posOrNeg = 1.0
    else:
        posOrNeg = -1.0

    setOfLines4 = []
    setOfLines4_recordedVal = []

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
        # new Line1
        tp1, tp2 = [_x(p1), _y(p1)+translation_high+new_y], [_x(p2), _y(p2)+translation_high+new_y]
        newLine1Set.append([tp1, tp2])

        # run a loop go through
        for j in range(0, len(setOfLines3)):
            p5, p6 = setOfLines3[j][0], setOfLines3[j][1]  # line 3
            x_dist = 1 * np.abs(_y(p1) - _y(p5))
            diff = 2 * np.abs(_y(p1) - _y(p5))

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
            loop1val_py1 = x_dist
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
                        # Line touch Top wick only
                        start = df[2][px]  # set y to the lowest
                        if df[1][px] > df[4][px]:  # red candle
                            # use open when lowest
                            end = df[1][px]

                        else:  # green candle
                            # use close when lowest
                            end = df[4][px]

                        if start >= round(new_y, rounded_decimal) >= end:
                            wick_count = wick_count + 1


                    elif check_trend == "DOWN":  # use top line
                        # Line touch Bottom wick only
                        start = df[3][px]  # set y to the lowest
                        if df[1][px] > df[4][px]:  # red candle
                            # use close when highest
                            end = df[4][px]

                        else:  # green candle
                            # use open when highest
                            end = df[1][px]

                        if start <= round(new_y, rounded_decimal) <= end:
                            wick_count = wick_count + 1

                possibleLine4Set.append([p7, p8])
                possibleLine4Set_recordVal.append(wick_count)

                if diff != 0.0:
                    loop1val_py1 = loop1val_py1 + diff*stepRatio
                else:
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
                        temp_p1 = tempList[i][0]
                        if np.abs(_y(temp_p1) - _y(x_distLine[0])) < minDist:
                            minDist = np.abs(_y(temp_p1) - _y(x_distLine[0]))
                            resultIndex = i

                    if resultIndex != -1:
                        setOfLines4.append(tempList[resultIndex])
                        setOfLines4_recordedVal.append(limit)

                # else:
                    # ?


    newTBRSet = []
    limit = max(setOfLines4_recordedVal)
    for i in range(0, len(setOfLines4)):
        if setOfLines4_recordedVal[i] >= limit:
            newTBRSet.append(setOfLines4[i])

    return [newTBRSet, setOfxDistLines, setOfx2DistLines, newLine1Set, limit]


def drawLines(df: pd.DataFrame, figure1: pgPlot.Figure, l1: list,
              fromIndex: int, toIndex: int, name: str = "slope"):
    def readLine1(l2: list) -> list:
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

    # timestamplist = [df[0][0], df[0][toIndex-fromIndex-1]]
    # dateTimelist = [convertTimeStamp2DateTime(i) for i in timestamplist]
    l2 = readLine1(l1)
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


def drawLines_dash(df: pd.DataFrame, graph: pgPlot.Figure, p1_and_p2_list: list,
              fromIndex: int, toIndex: int, name: str = "slope"):
    def convert4linregressArgs(p1_and_p2_list: list) -> list:
        l = []
        for i in p1_and_p2_list:
            xList = []
            yList = []
            xList.append(i[0][0])
            xList.append(i[1][0])
            yList.append(i[0][1])
            yList.append(i[1][1])
            l.append([xList, yList])

        return l

    # timestamplist = [df[0][0], df[0][toIndex-fromIndex-1]]
    # dateTimelist = [convertTimeStamp2DateTime(i) for i in timestamplist]
    X_And_Y_List = convert4linregressArgs(p1_and_p2_list)
    strName1 = name + " " + "1"
    count = 1

    for i in X_And_Y_List:
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

        graph.add_trace(
            # pgPlot.Scatter(x=x, y=y, mode='lines', name=strName1))
            pgPlot.Scatter(x=new_x_list, y=new_y_list, line=dict(width=1,
                              dash='dash'), name=strName1))
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


def run_algorithm(client:Client, symbol:str, start_stamp:str, end_stamp:str, windowSize:int=50):
    st = convertDateStr2TimeStamp(start_stamp)
    et = convertDateStr2TimeStamp(end_stamp)
    fromIndex, toIndex = -1, -1
    klines_1m = client.futures_klines(symbol=symbol, interval="1m", startTime=st, endTime=et, limit=1000)
    array_response = np.array(klines_1m).tolist()
    df_prices = pd.DataFrame(klines_1m)

    # TEST ONLY when client is not responding due to some issues
    # df_prices = pd.read_pickle("t1.txt")
    # TEST END

    df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: int(x))
    df_prices.iloc[:, 1] = df_prices.iloc[:, 1].apply(lambda x: float(x))
    df_prices.iloc[:, 2] = df_prices.iloc[:, 2].apply(lambda x: float(x))
    df_prices.iloc[:, 3] = df_prices.iloc[:, 3].apply(lambda x: float(x))
    df_prices.iloc[:, 4] = df_prices.iloc[:, 4].apply(lambda x: float(x))
    print(f"KLINES: {df_prices}")

    windowSize = windowSize
    dirName = "images_"+symbol+"_windowSize_"+str(windowSize)
    if not os.path.exists(dirName):
        os.makedirs(dirName)


    for tempWindowIndex in range(0, df_prices.shape[0] - windowSize):
        print(tempWindowIndex)
        fromIndex = tempWindowIndex
        toIndex = fromIndex + windowSize

        tempDF = df_prices.iloc[fromIndex:toIndex]
        check_trend = findTrend(tempDF)

        df1 = pd.DataFrame()
        frames = [tempDF, df1]
        tempDF = pd.concat(frames, ignore_index=True)
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

            if len(AllSetOfLines4_num_wickIntersected) <= 0:

                if tempWindowIndex < 10:
                    name = "fig000" + str(tempWindowIndex)
                elif tempWindowIndex < 100:
                    name = "fig00" + str(tempWindowIndex)
                elif tempWindowIndex < 1000:
                    name = "fig0" + str(tempWindowIndex)
                else:
                    name = "fig" + str(tempWindowIndex)

                imgPostfix = ".png"
                graph.write_image(dirName + "/" + name + imgPostfix)

                continue

            max_wick = max(AllSetOfLines4_num_wickIntersected)
            tempTBRSet = []
            for i in range(0, len(AllSetOfLines4)):
                # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                # TODO
                if AllSetOfLines4_num_wickIntersected[i] >= max_wick:
                    tempTBRSet.append(AllSetOfLines4[i])

            newTBRSet = []
            last_index = 0
            if len(tempTBRSet) > 1:

                def convert4linregressArgs(p1_and_p2_list: list) -> list:
                    l = []
                    for i in p1_and_p2_list:
                        xList = []
                        yList = []
                        xList.append(i[0][0])
                        xList.append(i[1][0])
                        yList.append(i[0][1])
                        yList.append(i[1][1])
                        l.append([xList, yList])

                    return l

                if findTrend(tempDF) == "DOWN":
                    tempSlope = float("inf")
                    for i in range(0, len(tempTBRSet)):
                        line = tempTBRSet[i][3][3]

                        xyList = convert4linregressArgs(line)[0]
                        slope, intercept, r_value, p_value, std_err = linregress(xyList[0], xyList[1])
                        if slope < tempSlope and slope > 0:
                            tempSlope = slope
                            last_index = i

                else:
                    # tempSlope = float("-inf")
                    tempSlope = float("inf")
                    for i in range(0, len(tempTBRSet)):
                        line = tempTBRSet[i][3][3]

                        xyList = convert4linregressArgs(line)[0]
                        slope, intercept, r_value, p_value, std_err = linregress(xyList[0], xyList[1])
                        # if slope > tempSlope and slope < 0:
                        if slope < tempSlope and slope > 0:
                            tempSlope = slope
                            last_index = i

            newTBRSet.append(tempTBRSet[last_index])

            for i in range(0, len(newTBRSet)):
                temp1 = newTBRSet[i][0]
                temp2 = newTBRSet[i][1]
                temp3 = newTBRSet[i][2]
                setLines4 = newTBRSet[i][3]

                # check if, for given x - point, abs(y_L1 - y_L1_new) > abs(y_L1 - y_L3)
                # if True, move L1_new such that abs(y_L1 - y_L1_new) == abs(y-L1 - y_L3)
                y_L1 = _y(temp1[0][0])
                y_L1_new = _y(setLines4[3][0][0])
                y_L3 = _y(temp3[0][0])
                lhs = abs(abs(y_L1) - abs(y_L1_new))
                rhs = abs(abs(y_L1) - abs(y_L3))
                if lhs > rhs:
                    val1 = lhs - rhs
                    if check_trend == "UP":
                        # setLines4[3] is [[[45, 0.39278399999999997], [46, 0.3930039999999999]]]
                        # [[p1, p2]], its [0] is [p1, p2]
                        # [p1,p2], [0] get p1, [1] get p3
                        # p1-> [x, y], [0] get x-axis, [1] get y-axis
                        setLines4[3][0][0][1] = setLines4[3][0][0][1] + val1
                        setLines4[3][0][1][1] = setLines4[3][0][1][1] + val1
                    else:
                        setLines4[3][0][0][1] = setLines4[3][0][0][1] - val1
                        setLines4[3][0][1][1] = setLines4[3][0][1][1] - val1

                def convert4linregressArgs(p1_and_p2_list: list) -> list:
                    l = []
                    for i in p1_and_p2_list:
                        xList = []
                        yList = []
                        xList.append(i[0][0])
                        xList.append(i[1][0])
                        yList.append(i[0][1])
                        yList.append(i[1][1])
                        l.append([xList, yList])

                    return l

                df_length = df_prices.shape[0]
                lastIntersected_px = -1
                newLine1xyList = convert4linregressArgs(setLines4[3])
                Line2xyList = convert4linregressArgs(temp2)
                compareList = []
                belowORabove = False
                for i in newLine1xyList:
                    x = [int(j) + fromIndex for j in i[0]]
                    y = i[1]
                    slope, intercept, r_value, p_value, std_err = linregress(x, y)

                    for px in range(toIndex, df_length):
                        py1 = 0
                        if check_trend == "DOWN":  # trending up
                            py1 = df_prices[2][px]  # set y to the highest of current candlestick

                            # y = mx + b
                            if ((slope * px) + intercept) < py1:
                                belowORabove = True
                                compareList.append(px)
                                break
                        else:  # trending down
                            py1 = df_prices[3][px]  # set y to the lowest of current candlestick

                            # y = mx + b
                            if ((slope * px) + intercept) > py1:
                                belowORabove = True
                                compareList.append(px)
                                break

                    if belowORabove:
                        break

                for i in Line2xyList:
                    x = [int(j) + fromIndex for j in i[0]]
                    y = i[1]
                    slope, intercept, r_value, p_value, std_err = linregress(x, y)

                    for px in range(toIndex, df_length):
                        py1 = 0
                        if check_trend == "UP":  # trending up
                            py1 = df_prices[2][px]  # set y to the highest of current candlestick

                            # y = mx + b
                            if ((slope * px) + intercept) < py1:
                                belowORabove = True
                                compareList.append(px)
                                break
                        else:  # trending down
                            py1 = df_prices[3][px]  # set y to the lowest of current candlestick

                            # y = mx + b
                            if ((slope * px) + intercept) > py1:
                                belowORabove = True
                                compareList.append(px)
                                break

                    if belowORabove:
                        break

                if belowORabove:
                    if len(compareList) <= 0:
                        toIndex = df_length
                    else:
                        toIndex = np.min(compareList)
                else:
                    continue

                extraInfoFrom = "from: " + str(fromIndex) + "_"
                extraInfoTo = "to: " + str(toIndex) + "_"
                drawLines(tempDF, graph, temp2, fromIndex, toIndex, "L2_")
                drawLines(tempDF, graph, temp3, fromIndex, toIndex, "L3_")
                drawLines(tempDF, graph, setLines4[0], fromIndex, toIndex, "L4_")
                # drawLines(tempDF, graph, setLines4[1], fromIndex, toIndex, "L3_xdist_")
                # drawLines(tempDF, graph, setLines4[2], fromIndex, toIndex, "L3_x2dist_")
                drawLines(tempDF, graph, setLines4[3], fromIndex, toIndex, extraInfoFrom + "L1_new_")
                drawLines_dash(tempDF, graph, temp1, fromIndex, toIndex, extraInfoTo + "L1_")

            # graph.show()
            if tempWindowIndex < 10:
                name = "fig000" + str(tempWindowIndex)
            elif tempWindowIndex < 100:
                name = "fig00" + str(tempWindowIndex)
            elif tempWindowIndex < 1000:
                name = "fig0" + str(tempWindowIndex)
            else:
                name = "fig" + str(tempWindowIndex)

            imgPostfix = ".png"
            # graph.write_image("images/" + name + imgPostfix)
            # TODO: [!] windows might have different directory path unlike mac
            graph.write_image(dirName + "/" + name + imgPostfix)


    generatePPT(dirName,dirName)




# if __name__ == "__main__":
#     socks5_proxy = "54.249.188.136:1080"
#     socks5_user = None
#     socks5_pass = None
#     socks5_ssl_verification = True
#
#     client = Client(exchange="binance.com",
#                     socks5_proxy_server=socks5_proxy,
#                     socks5_proxy_user=socks5_user,
#                     socks5_proxy_pass=socks5_pass,
#                     socks5_proxy_ssl_verification=socks5_ssl_verification)
#
#     # TEST ONLY, when client is not responding due to some issues
#
#     # run_algorithm(client=None, symbol="DOGEUSDT", start_stamp="2023-05-06 10:00:00",
#     #               end_stamp="2023-05-06 20:00:00")
#
#     # TEST END
#
#     run_algorithm(client=client, symbol="DOGEUSDT", start_stamp="2023-05-06 10:00:00",
#                   end_stamp="2023-05-06 20:00:00")
