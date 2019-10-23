import numpy as np
import matplotlib.pyplot as plt
import logging
import time
from collections import deque
from matplotlib import use
from model import signal_process as sp
from scipy import signal

use('TkAgg')
LOG_FORMAT = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
test_logger = logging.getLogger(__name__)
handler1 = logging.StreamHandler()
handler2 = logging.FileHandler(filename='test.log', mode='a', encoding='utf-8')
handler1.setFormatter(LOG_FORMAT)
handler2.setFormatter(LOG_FORMAT)
test_logger.setLevel(logging.DEBUG)
test_logger.addHandler(handler1)
test_logger.addHandler(handler2)


class HeartRate(object):
    def __init__(self, data, fs, threshold, scalar, smooth: bool, smooth_level):
        self._count = 0
        self._max_D_value = 0
        self._begin = 0
        self._end = 0
        self._mark = [0]
        self.fs = fs
        self.threshold = threshold
        self.scalar = scalar
        self.heart_data = np.array(data)
        self.smooth = smooth
        self.smooth_level = smooth_level

    # calculating heart rate by body impedance
    def heart_rate_cal_v1(self):
        if len(self.heart_data) < 40:
            test_logger.warning("No Heart beat signal")
            return 0, 0
        if self.smooth:
            # maybe you should cut down the level of filter
            self.heart_data = sp.average_move_filter(self.heart_data, self.smooth_level)
        #  also you can compare a number of front sample with constant
        if self.heart_data[-20:].mean() > int(9.2e6) or self.heart_data[-20:].mean() < int(4.5e6):
            test_logger.warning("No Heart beat signal")
            return 0, 0
        else:
            test_logger.info("Impedance signal detected")
            temp = [0 if d <= 0 else d for d in np.array(self.heart_data[self.scalar:]) -
                    np.array(self.heart_data[0:-self.scalar])]

            # begin to scan the data
            for index, value in enumerate(temp):
                d_index = index - self._mark[-1]
                if d_index < 18:
                    continue
                elif value > self.threshold:
                    self._mark.append(index)
                    self._count += 1
                    if self._begin == 0:
                        self._begin = index
                else:
                    continue
            self._end = self._mark[-1]
            heart_rate = sp.cal_heart_rate_unit(self._end, self._begin, self._count, self.fs)
            return heart_rate, temp, index

    def heart_rate_cal_v2(self):
        # set bottom as d
        # using find_peaks func from scipy-signal
        if self.smooth:
            self.heart_data = sp.average_move_filter(self.heart_data, self.smooth_level)
        temp = [0 if d <= 0 else d for d in np.array(self.heart_data[self.scalar:])
                - np.array(self.heart_data[0:-self.scalar])]
        index, _ = signal.find_peaks(temp, height=0, distance=20, prominence=500, width=5)
        self._mark.extend(index)
        self._end = index[-1]
        self._begin = index[0]
        self._count = len(index)
        heart_rate = sp.cal_heart_rate_unit(self._end, self._begin, self._count, self.fs)
        return heart_rate, temp, index

    def heart_rate_cal_v3(self):
        # use find_peaks function write by myself
        if self.smooth:
            self.heart_data = sp.average_move_filter(self.heart_data, self.smooth_level)
        temp = [0 if d <= 0 else d for d in np.array(self.heart_data[self.scalar:])
                - np.array(self.heart_data[0:-self.scalar])]
        index = sp.find_peaks(temp, width=6, threshold=600)
        try:
            self._mark.extend(index)
            self._end = index[-1]
            self._begin = index[0]
            self._count = len(index)
        except IndexError:
            test_logger.error("Index索引越界")
        finally:
            heart_rate = sp.cal_heart_rate_unit(self._end, self._begin, self._count, self.fs)
        return heart_rate, temp, index
        pass


def heart_rate_main_debug(data, fs, threshold, scalar, smooth: bool, smooth_level):
    process = HeartRate(data, fs, threshold, scalar, smooth, smooth_level)
    plt.subplot(311)
    plt.title('impedance data')
    plt.plot(data, label='origin')
    plt.subplot(312)
    plt.plot(process.average_move_filter(), label='smooth')
    plt.subplot(313)
    heart_rate, temp, index = process.heart_rate_cal_v3()
    plt.plot(temp, label='D-Value', marker='x', markevery=process._mark[1:], mec='r')
    plt.text(230, -27000, '$count=%d $ \n $rate=%d $' % (process._count, heart_rate))
    plt.show()
    return heart_rate


def heart_rate_main(data, fs, threshold, scalar, smooth: bool, smooth_level):
    process = HeartRate(data, fs, threshold, scalar, smooth, smooth_level)
    heart_rate, temp, index = process.heart_rate_cal_v3()
    return heart_rate, temp, index


class HeartRateRealTime(object):
    def __init__(self, scalar, smooth_level, threshold, width, fs, diff_len):
        self.smooth_level = smooth_level
        self.diff_len = diff_len
        self.origin_data = deque(maxlen=smooth_level)
        self.average_data = deque(maxlen=scalar)
        self.diff_data = deque(maxlen=diff_len)
        self.threshold = threshold
        self.width = width
        self.fs = fs

    def receive_data(self, data):
        if self.origin_data.maxlen == self.origin_data.__len__():
            if self.average_data.maxlen == self.average_data.__len__():
                if self.diff_data.maxlen == self.diff_data.__len__():
                    index = sp.find_peaks(list(self.diff_data), width=self.width, threshold=self.threshold)
                    end = index[-1]
                    begin = index[0]
                    count = len(index)
                    rate = sp.cal_heart_rate_unit(end, begin, count, self.fs)
                    # 删掉前面一秒的数据
                    self.diff_data = deque(list(self.diff_data)[self.fs:], maxlen=self.diff_len)
                    return rate
                else:
                    div = self.average_data[-1] - self.average_data[0]
                    self.diff_data.append(0 if div < 0 else div)
            self.average_data.append(sum(list(self.origin_data)) / self.smooth_level)
        self.origin_data.append(data)
        return 0


if __name__ == '__main__':
    origin = np.load(r'D:\SerialTools\80-852019-10-12-TIME10-55-28.npy')
    h_ob = HeartRateRealTime(8, 6, 700, 6, 64, 640)
    for index, value in enumerate(origin):
        rate = h_ob.receive_data(value)
        print("Index:%d------Rate:%f" % (index, rate))







