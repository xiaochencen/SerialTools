'''
funciton: process receive data
'''
import logging

signal_logging = logging.getLogger(__name__)
stream_handle = logging.StreamHandler()
signal_logging.setLevel(logging.DEBUG)
LOG_FORMAT = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
stream_handle.setFormatter(LOG_FORMAT)
stream_handle.setLevel(logging.DEBUG)
signal_logging.addHandler(stream_handle)

def filter_data(data, mark, data_len, total_len, heart_mark, heart_filter):
    rate = 0
    if heart_filter:
        index = data.find(heart_mark)
        if index != -1:
            rate = int(data[index:index + 2], 16)
    data = data.split(mark)[1:]
    f_data = []
    for i in data:
        if len(i) == total_len-len(mark):
            f_data.append(i[0:data_len])
    return f_data, rate


def transform_data(data, mark, data_len, total_len, heart_mark, heart_filter):
    rate = 0
    if heart_filter:
        index = data.find(heart_mark)
        if index != -1:
            index += len(heart_mark)
            rate = int(data[index:index+2], 16)
    data = data.split(mark)[1:]
    t_data = []
    for i in data:
        if len(i) == total_len-len(mark):
            # 进行转换最高位应该在最左边，重新进行排序
            # 还有使用re模块的方法
            data_p = i[0:data_len]
            data_p = [data_p[i:i+2] for i in range(0, len(data_p), 2)]
            data_p = ''.join(list((reversed(data_p))))
            t_data.append(int(data_p, 16))
    return t_data, rate


def _is_peak(data):
    if max(data) == data[1]:
        return True
    else:
        return False


def _is_cross(data):
    # 可以限制起点终点的距离
    if len(data) != 3:
        print("---------------------------------------------------"+str(data))
        return False
    if data[1] == 0:
        # 终点
        if data[0] > 0 and data[2] == 0:
            return 2
        # 起点
        elif data[0] == 0 and data[2] > 0:
            return 1
        # 同时
        else:
            return 3


def find_peaks(data, distance: int = 15, width=None, threshold=0):
    # 可能需要对差值2点的卷积处理，将
    index = []
    flag1 = 0  # 峰值前端标志
    flag3 = 0
    begin = 0  # 起点标志
    peak_index = 0  # 上一峰值索引
    temp_peak_index = None  # 临时峰值索引
    len_data = len(data)
    # 主循环 会少两个点
    for i in range(1, len_data-1):
        signal_logging.info("当前索引%d--%d" % (i, data[i]))
        if data[i] == 0:
            # 检测到起点，进入峰值检测
            mark = _is_cross(data[i-1:i + 2])
            if mark == 1 and flag1 == 0:
                signal_logging.debug('检测到起点%d' % i)
                begin = i
                flag1 = 1
            # 检测到终点，并执行最后的宽度检测
            elif mark == 2 and flag1 == 1:
                signal_logging.debug('检测到终点%d' % i)
                flag1 = 0
                if i - begin > width and flag3 == 1:
                    signal_logging.debug('峰值%d' % temp_peak_index)
                    peak_index = temp_peak_index
                    temp_peak_index = None
                    index.append(peak_index)
                    flag3 = 0
            # 掠过少数零点（单零点）
            else:
                continue
        elif data[i] > threshold:
            if _is_peak(data[i-1:i+2]) and flag1 == 1:
                # 检测到峰值点，确认峰值距离
                if i-peak_index > distance:
                    flag3 = 1
                    if temp_peak_index is None:
                        temp_peak_index = i
                    # 确认找到峰值，并判断是否为全局最优峰值
                    if temp_peak_index is not None and data[temp_peak_index] < data[i]:
                        temp_peak_index = i
    return index














