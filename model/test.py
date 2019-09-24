import numpy as np
import matplotlib.pyplot as plt
from matplotlib import use
import queue
use('TkAgg')


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
        for i in range(len(self.heart_data)):
            if i+1 < self.smooth_level:
                temp.append(sum(self.heart_data[0:i+1])/(i+1))
            elif i > len(self.heart_data)-self.smooth_level:
                temp.append(sum(self.heart_data[i:])/(len(self.heart_data)-i))
            else:
                temp.append(sum(self.heart_data[i:i+self.smooth_level]/self.smooth_level))
        return np.array(temp)

    # calculating heart rate by body impedance
    def heart_rate_cal_v1(self):
        if len(self.heart_data) < 100:
            return 0, 0
        if self.smooth:
            # maybe you should cut down the level of filter
            self.heart_data = self.average_move_filter()
        if self.heart_data[-20:].mean() > int(9.2e6) or self.heart_data[-20:].mean() < int(4.5e6):  # also you can compare a number of front sample with constant
            print("No heartbeat detected")
            return 0, 0
        else:
            print("Detected impedance signal, calculate progress running")  # need replace print() by logging
            temp = self.heart_data[self.scalar:]-self.heart_data[0:-self.scalar]
            # begin to scan the data
            #
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
        for date, index in enumerate(self.heart_data):
            # todo: 加入离秤检测
            if self.data_queue.full() is False:
                self.data_queue.put(date)
            else:
                temp = self.data_queue.queue[-1]-self.data_queue.get()
                if temp > self.threshold:
                    if index-self._mark[-1] < 18:
                        continue
                    else:
                        self._mark.append(index)


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
    heart_rate, temp = process.heart_rate_cal_v1()
    plt.plot(temp, label='D-Value', marker='x', markevery=process._mark[1:], mec='r')
    plt.text(230, -27000, '$count=%d $ \n $rate=%d $' % (process._count, heart_rate))
    plt.show()
    return heart_rate


def heart_rate_main(data, fs, threshold, scalar, smooth: bool, smooth_level):
    process = HeartRate(data, fs, threshold, scalar, smooth, smooth_level)
    heart_rate, temp = process.heart_rate_cal_v1()
    return heart_rate



