import numpy as np
import matplotlib.pyplot as plt
import queue
import logging
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
        self.data_queue = queue.Queue(self.scalar)

    # data smooth by convolution
    def _smooth_filter_by_conv(self):
        data = np.convolve(self.heart_data, np.ones(self.smooth_level)/self.smooth_level, mode='same')
        return data

    # optimization edge processing of filter which is using convolution
    def average_move_filter(self):
        temp = []
        # there is need for len(self.heart_data) times multiplication operations
        # if data is list func doesn't work
        for i in range(len(self.heart_data)):
            if i+1 < self.smooth_level:
                temp.append(sum(self.heart_data[0:i+1])/(i+1))
            elif i > len(self.heart_data)-self.smooth_level:
                temp.append(sum(self.heart_data[i:])/(len(self.heart_data)-i))
            else:
                temp.append(sum(self.heart_data[i:i+self.smooth_level])/self.smooth_level)
        return np.array(temp)

    # calculating heart rate by body impedance
    def heart_rate_cal_v1(self):
        if len(self.heart_data) < 40:
            test_logger.warning("No Heart beat signal")
            return 0, 0
        if self.smooth:
            # maybe you should cut down the level of filter
            self.heart_data = self.average_move_filter()
        #  also you can compare a number of front sample with constant
        if self.heart_data[-20:].mean() > int(9.2e6) or self.heart_data[-20:].mean() < int(4.5e6):
            test_logger.warning("No Heart beat signal")
            return 0, 0
        else:
            test_logger.info("Impedance signal detected")
            temp = [0 if d <= 0 else d for d in self.heart_data[self.scalar:]-self.heart_data[0:-self.scalar]]

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
            heart_rate = self.cal_heart_rate_unit()
            return heart_rate, temp

    def heart_rate_cal_v2(self):
        # set bottom as d
        if self.smooth:
            self.heart_data = self.average_move_filter()
        temp = [0 if d <= 0 else d for d in self.heart_data[self.scalar:] - self.heart_data[0:-self.scalar]]
        index, _ = signal.find_peaks(temp, height=0, distance=20, prominence=500, width=5)
        self._mark.extend(index)
        self._end = index[-1]
        self._begin = index[0]
        self._count = len(index)
        heart_rate = self.cal_heart_rate_unit()
        return heart_rate, temp

    def heart_rate_cal_v3(self):
        if self.smooth:
            self.heart_data = self.average_move_filter()
        temp = [0 if d <= 0 else d for d in self.heart_data[self.scalar:] - self.heart_data[0:-self.scalar]]
        index = sp.find_peaks(temp, width=5, threshold=800)
        self._mark.extend(index)
        self._end = index[-1]
        self._begin = index[0]
        self._count = len(index)
        heart_rate = self.cal_heart_rate_unit()
        return heart_rate, temp
        pass

    def cal_heart_rate_unit(self):
        total_sample = self._end-self._begin
        #total_sample = 768
        if total_sample > 0:
            # 计算心率的时候需要减掉一个心跳点
            heart_rate = (self._count-1)/(total_sample/self.fs)*60
            return heart_rate
        return 0


def heart_rate_main_debug(data, fs, threshold, scalar, smooth: bool, smooth_level):
    process = HeartRate(data, fs, threshold, scalar, smooth, smooth_level)
    plt.subplot(311)
    plt.title('impedance data')
    plt.plot(data, label='origin')
    plt.subplot(312)
    plt.plot(process.average_move_filter(), label='smooth')
    plt.subplot(313)
    heart_rate, temp = process.heart_rate_cal_v3()
    plt.plot(temp, label='D-Value', marker='x', markevery=process._mark[1:], mec='r')
    plt.text(230, -27000, '$count=%d $ \n $rate=%d $' % (process._count, heart_rate))
    plt.show()
    return heart_rate


def heart_rate_main(data, fs, threshold, scalar, smooth: bool, smooth_level):
    process = HeartRate(data, fs, threshold, scalar, smooth, smooth_level)
    heart_rate, temp = process.heart_rate_cal_v1()
    return heart_rate



