from src.BaseClass import BaseClass
import decimal
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objects as pgPlot
from scipy.stats import linregress
import sys


class Strategy(BaseClass):
    """
    Class that houses the very strategy generating algorithm, designed to capture
    an otherwise visually-defined trend following strategy
    """

    def __init__(self, client):
        self.client = client

    def calculate_initial_wick_lines(self):
        df_prices = pd.read_pickle("df_prices")
        cols_to_convert = df_prices.columns[2:]
        df_prices.iloc[:, 0] = df_prices.iloc[:, 0].apply(lambda x: int(x))
        df_prices[cols_to_convert] = df_prices[cols_to_convert].astype(float)
        fromIndex, toIndex = 401, 499  # Down
        tempDF = df_prices.iloc[fromIndex:toIndex]
        tempDF.reset_index(drop=True, inplace=True)
        print(f"DF: {tempDF.head()}")
        setLines = self.BF_findSetOfLines(tempDF, 2, True)
        graph = self.visualization(df_prices)
        self.drawLines(tempDF, graph, setLines, fromIndex, toIndex)
        graph.show()

    def visualization(self, df: pd.DataFrame) -> pgPlot.Figure:
        openList = df[1].tolist()
        openList = [float(i) for i in openList]
        priceList = df[4].tolist()
        priceList = [float(i) for i in priceList]
        highList = df[2].tolist()
        highList = [float(i) for i in highList]
        lowList = df[3].tolist()
        lowList = [float(i) for i in lowList]

        fig = pgPlot.Figure(data=[pgPlot.Candlestick(x=df.index,
                                                     open=openList, high=highList,
                                                     low=lowList, close=priceList)])

        return fig

    def drawLines(self, df: pd.DataFrame, figure1: pgPlot.Figure, l1: list, fromIndex: int, toIndex: int):
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

        l2 = readLine1(df, l1)
        strName1 = "slope " + "1"
        count = 1
        for i in l2:
            # timestamplist = [int(j) for j in i[2]]
            # dateTimelist = [convertTimeStamp2DateTime(i) for i in timestamplist]
            x = [int(j) + fromIndex for j in i[0]]
            y = i[1]
            # https://stackoverflow.com/questions/9538525/calculating-slopes-in-numpy-or-scipy
            slope, intercept, r_value, p_value, std_err = linregress(x, y)

            # y = mx + b
            new_x_list = [fromIndex, toIndex - 1]
            # new_y_list = [slope * 0 + intercept, slope * (toIndex-fromIndex) + intercept]
            new_y_list = [slope * fromIndex + intercept, slope * (toIndex - 1) + intercept]

            figure1.add_trace(
                # pgPlot.Scatter(x=x, y=y, mode='lines', name=strName1))
                pgPlot.Scatter(x=new_x_list, y=new_y_list, mode='lines', name=strName1))
            # pgPlot.Scatter(x=dateTimelist, y=new_y_list, mode='lines', name=strName1))

            count = count + 1
            strName1 = "slope " + str(count)

    # format: "2023-02-15 02:23:00"
    def convertDateStr2TimeStamp(self, dateString):
        return int(datetime.strptime(dateString, "%Y-%m-%d %H:%M:%S").timestamp()) * 1000

    def convertTimeStamp2DateTime(self, integer):
        return datetime.fromtimestamp(integer * 1.0 / 1000)

    def findCandleInterception(self, df: pd.DataFrame) -> list:
        interceptionList_high = []
        interceptionList_low = []
        length = df.shape[0]
        # initial_index = df.index[0]
        # for i in range(initial_index, initial_index+length):
        for i in range(0, length):
            # for i in range(initial_index, initial_index+length):
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
            for j in range(0, length):
                # for j in range(initial_index, initial_index+length):
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

    def create_df(self, list_klines):
        array_np = np.array([lst[:5] for lst in list_klines])
        return pd.DataFrame(array_np)

    # part 1
    def BF_findSetOfLines(self, df: pd.DataFrame, specificXWickPoints: int = 2, atLeast=False):
        print(df)
        check_trend = self.findTrend(df)
        _test_setOfAllLines = []
        setOfLines = []
        df_length = df.shape[0]

        # https://stackoverflow.com/questions/6189956/easy-way-of-finding-decimal-places
        def find_decimals(value):
            return (int(abs(decimal.Decimal(str(value)).as_tuple().exponent)))

        rounded_decimal = find_decimals(df[1][0])

        for i in range(0, df_length):
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
            for px2 in range(i, df_length):
                # if i == j:
                #     continue
                if px1 == px2:
                    continue

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
                loop1val_py1 = py1
                while (loop1val_py1 <= limit1):
                    loop2val_py2 = py2
                    while (loop2val_py2 <= limit2):
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

                            if self.segment_intersect([[loop3val_i, df[1][loop3val_i]], [loop3val_i,
                                                                                         df[4][loop3val_i]]],
                                                      self.scale([[px1, loop1val_py1], [px2, loop2val_py2]], 100)):
                                failed_conditions = True  # like failed intersection condition
                                break

                        # check whether a line intersect the body candle [(x, open), (x, close)]->vertical line
                        if failed_conditions:
                            # if this line intersect body, then it is not the line we wanted

                            _test_setOfAllLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                            loop2val_py2 = loop2val_py2 + 0.1
                            continue
                        else:
                            # store the line
                            setOfLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                            _test_setOfAllLines.append([[px1, loop1val_py1], [px2, loop2val_py2]])
                            loop2val_py2 = loop2val_py2 + 0.1

                    loop1val_py1 = loop1val_py1 + 0.1

        print("setOfLines: (passed intersection with candle body)")
        print(setOfLines)
        print(len(setOfLines))
        print()

        toBeReturnedSet = []

        # TODO: [!]
        # add final condition depending on trend up or trend down
        for setOfLines_index in range(0, len(setOfLines)):
            x = [self._x(setOfLines[setOfLines_index][0]), self._x(setOfLines[setOfLines_index][1])]
            y = [self._y(setOfLines[setOfLines_index][0]), self._y(setOfLines[setOfLines_index][1])]
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
                    py1 = df[3][px]  # set y to the lowest of current candlestick

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

            xList = [self._x(toBeReturnedSet[setOfLines_index][0]), self._x(toBeReturnedSet[setOfLines_index][1])]
            yList = [self._y(toBeReturnedSet[setOfLines_index][0]), self._y(toBeReturnedSet[setOfLines_index][1])]
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

                    # if px == 65:
                    #     print("start & end:")
                    #     print(start)
                    #     print(end)
                    #     print("start & end.")
                    #     print("new_y:")
                    #     print(new_y)
                    #     print(round(new_y, rounded_decimal))
                    #     print("new_y end.")

                    if start >= round(new_y, rounded_decimal) >= end:
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
        newTBRSet = []
        for i in range(0, len(toBeReturnedSet)):
            # if specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
            if atLeast is True and \
                    specificXWickPoints == len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(toBeReturnedSet[i])
            elif specificXWickPoints <= len(toBeReturnedSet_intersectionWithOtherWickPoint[i]):
                newTBRSet.append(toBeReturnedSet[i])

        newTBRSet2 = []
        # TODO [!]: if trend UP and slope < 0, remove, and, if trend DOWN and slope > 0, remove
        for i in range(0, len(newTBRSet)):
            xList = [self._x(toBeReturnedSet[i][0]), self._x(toBeReturnedSet[i][1])]
            yList = [self._y(toBeReturnedSet[i][0]), self._y(toBeReturnedSet[i][1])]
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
        return newTBRSet

    def findTrend(self, df: pd.DataFrame) -> str:
        # df[4] is close, df[1] is open
        # list of close vals - list of open vals
        sum = np.sum(df[4] - df[1])

        trend = "None"
        if sum > 0:
            trend = "UP"
        elif sum < 0:
            trend = "DOWN"
        return trend

    # Return true if line segments AB and CD intersect
    def segment_intersect(self, line1, line2):  # A,B -> line1, C,D-> line2
        # return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
        return self.ccw(line1[0], line2[0], line2[1]) != self.ccw(line1[1], line2[0], line2[1]) \
               and self.ccw(line1[0], line1[1], line2[0]) != self.ccw(line1[0], line1[1], line2[1])

    # https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
    def ccw(self, A, B, C):
        # return (C.y-A.y) * (B.x-A.x) > (B.y-A.y) * (C.x-A.x)
        return (self._y(C) - self._y(A)) * (self._x(B) - self._x(A)) > (self._y(B) - self._y(A)) * (self._x(C) -
                                                                                                    self._x(A))

    # return x
    @staticmethod
    def _x(point):
        return point[0]

    # return y
    @staticmethod
    def _y(point):
        return point[1]

    def scale(self, line1, factor):
        x1, x2 = self.scale_dimension(self._x(line1[0]), self._x(line1[1]), factor)
        y1, y2 = self.scale_dimension(self._y(line1[0]), self._y(line1[1]), factor)
        return [[x1, y1], [x2, y2]]

    def scale_dimension(self, dim1, dim2, factor):
        base_length = dim2 - dim1
        ret1 = dim1 - (base_length * (factor - 1) / 2)
        ret2 = dim2 + (base_length * (factor - 1) / 2)
        return ret1, ret2
