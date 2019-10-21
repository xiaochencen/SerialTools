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
file_handle = logging.FileHandler('heart_rate.log', encoding='utf-8')
file_handle.setLevel(logging.CRITICAL)
file_handle.setFormatter(LOG_FORMAT)
signal_logging.addHandler(file_handle)


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
    # if len(data) != 3:
    #     print("---------------------------------------------------"+str(data))
    #     return False
    if data[1] == 0:
        if data[0] > 0 and data[2] == 0:
            return 2
        elif data[0] == 0 and data[2] > 0:
            return 1
        else:
            return 3


def average_move_filter(filter_data, smooth_level):
    temp = []
    # there is need for len(filter_data) times multiplication operations
    # if data is list func doesn't work
    for i in range(len(filter_data)):
        if i+1 < smooth_level:
            temp.append(sum(filter_data[0:i+1])/(i+1))
        elif i > len(filter_data)-smooth_level:
            temp.append(sum(filter_data[i:])/(len(filter_data)-i))
        else:
            temp.append(sum(filter_data[i:i+smooth_level])/smooth_level)
    return temp


# 可以用类来写，并将find_peaks设置为静态方法
# 这样可以将一些代码独立出来作为类方法
def find_peaks(data, distance: int = 15, width=None, threshold=0):
    index = []
    flag1 = 0  # 是否进入峰值段阶段
    flag3 = 0  # 找到峰值标志，可以寻找终点标志
    begin = 0  # 起点标志
    peak_index = 0  # 上一峰值索引
    peak_mean = 0  # 初始化峰值均值
    temp_peak_index = None  # 临时峰值索引
    dis = 0  # 两峰之间的采样点数
    len_data = len(data)
    # 主循环 会少两个点
    for i in range(1, len_data-1):
        # 起点终点确认
        if data[i] == 0:
            mark = _is_cross(data[i-1:i + 2])
            # 检测到起点，记录index
            if mark == 1 and flag1 == 0:
                # signal_logging.debug('检测到起点%d' % i)
                begin = i
                flag1 = 1
            # 检测到终点，并执行最后的宽度检测
            elif mark == 2 and flag1 == 1:
                # signal_logging.debug('检测到终点%d' % i)
                flag1 = 0
                if i - begin > width and flag3 == 1:
                    # 找到第一个峰值
                    if peak_index == 0:
                        if data[temp_peak_index] < 1000:  # 防止过小值屏蔽
                            signal_logging.info("屏蔽起点:%d" % temp_peak_index)
                            temp_peak_index = None
                            flag3 = 0
                            continue
                        peak_index = temp_peak_index
                        signal_logging.info("检测到第一峰:{index}--值为：{value:.2f}".
                                            format(index=peak_index, value=data[peak_index]))
                        temp_peak_index = None
                        index.append(peak_index)
                        flag3 = 0
                    # 找到第二个峰值 如果percent 达不到要求
                    # 那么删除前一个值并将当前值作为第一个值重新搜索确认dis
                    elif dis == 0:
                        percent = data[peak_index]/data[temp_peak_index]
                        cur_dis = temp_peak_index - peak_index
                        # cur_dis 范围设定在心跳40-192/min 确定初始量程
                        if 0.5 < percent and 96 > cur_dis > 20:
                            signal_logging.info("检测到第二峰:{index}--值为：{value:.2f}--距离：{cur}--比例：{per:.2f}".
                                                format(index=temp_peak_index, value=data[temp_peak_index],
                                                cur=cur_dis, per=percent))
                            dis = temp_peak_index-peak_index
                            peak_mean = (data[temp_peak_index]+data[peak_index])/2
                            peak_index = temp_peak_index
                            temp_peak_index = None
                            index.append(peak_index)
                            flag3 = 0
                        else:
                            signal_logging.info("检测不合格第二峰:{index}--值为：{value:.2f}--距离：{cur}--比例：{per:.2f}".
                                                format(index=temp_peak_index, value=data[temp_peak_index],
                                                       cur=cur_dis, per=percent))
                            index.pop()
                            # 判断第二个峰值是否达到阈值，如果达到则将该值作为新的第一峰
                            # 否者重新搜索第一峰
                            if data[temp_peak_index] > 1000:
                                peak_index = temp_peak_index
                                index.append(peak_index)
                            else:
                                peak_index = 0
                            temp_peak_index = None
                            flag3 = 0
                    # 找到第一第二峰 根据初始化的参数执行后续搜索
                    else:
                        percent = peak_mean / data[temp_peak_index]
                        cur_dis = temp_peak_index - peak_index
                        signal_logging.info("检测到合格峰值:{index}--值为：{value:.2f}--距离：{cur}--比例：{per:.2f}".
                                            format(index=temp_peak_index, value=data[temp_peak_index],
                                                   cur=cur_dis, per=percent))
                        # 每次心跳点变化 以及 前后两个峰值 不能超过一定的阈值
                        # 前后阈值设置为不同的值
                        if 0.65 * dis < cur_dis < 1.5 * dis and 0.2 < percent < 2.5:
                            # todo 确认该点确实是心跳点  可调整加权数据 加速收敛
                            dis = 0.75 * dis + 0.25 * cur_dis
                            signal_logging.debug('-----------%d' % dis)
                            # 只有在确定是心跳点的时候更新peak的均值
                            peak_mean = (peak_mean + data[temp_peak_index])/2
                            peak_index = temp_peak_index
                            temp_peak_index = None
                            index.append(peak_index)
                            flag3 = 0
                            pass
                        # 心跳链接一旦断掉后面接不起来，只能重新开始计算
                        elif cur_dis > 1.5*dis:
                            signal_logging.warning(index)
                            # 如果已经利用到了50%的数据,
                            if index[-1]-index[0] > len(data)*0.5 or len(index) > 10:
                                return index
                            index.clear()
                            flag1 = 0  # 是否进入峰值段阶段
                            flag3 = 0  # 找到峰值标志，可以寻找终点标志
                            begin = 0  # 起点标志
                            peak_index = 0  # 上一峰值索引
                            temp_peak_index = None  # 临时峰值索引
                            peak_mean = 0
                            dis = 0  # 两峰之间的采样点数
                            signal_logging.warning("-------------数据清零")
                            pass
                        else:
                            # todo 不认为该点是心跳点
                            temp_peak_index = None
                            flag3 = 0
                            pass
            else:
                continue
        # 峰值确认
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


def __find_peaks(data, distance: int = 15, width=None, threshold=0):
    # 可能需要对差值2点的卷积处理，将
    index = []
    flag1 = 0  # 是否进入峰值段阶段
    flag3 = 0  # 找到峰值标志，可以寻找终点标志
    begin = 0  # 起点标志
    peak_index = 0  # 上一峰值索引
    temp_peak_index = None  # 临时峰值索引
    dis = 0  # 两峰之间的采样点数
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
                    # 找到第一个峰值
                    if peak_index == 0:
                        peak_index = temp_peak_index
                        temp_peak_index = None
                        index.append(peak_index)
                        flag3 = 0
                    # 找到第二个峰值 如果percent 达不到要求
                    # 那么删除前一个值并将当前值作为第一个值重新搜索确认dis
                    elif dis == 0:
                        percent = data[peak_index]/data[temp_peak_index] if \
                            data[peak_index] < data[temp_peak_index] else\
                            data[temp_peak_index]/data[peak_index]
                        cur_dis = temp_peak_index - peak_index
                        if percent > 0.5 and 96 > cur_dis > 30:
                            dis = temp_peak_index-peak_index
                            peak_index = temp_peak_index
                            temp_peak_index = None
                            index.append(peak_index)
                            flag3 = 0
                        else:
                            index.pop()
                            peak_index = temp_peak_index
                            index.append(peak_index)
                            temp_peak_index = None
                            flag3 = 0
                    else:
                        div_data = [data[peak_index], data[temp_peak_index]]
                        cur_dis = temp_peak_index - peak_index
                        percent = min(div_data) / max(div_data)  # 计算峰值差距
                        if percent > 0.4 and 0.5 * dis < cur_dis < 1.5 * dis:
                            # todo 确认该点确实是心跳点  可调整加权数据
                            dis = 0.8 * dis + 0.2 * cur_dis
                            signal_logging.debug('----%d' % dis)
                            peak_index = temp_peak_index
                            temp_peak_index = None
                            index.append(peak_index)
                            flag3 = 0
                            pass
                        else:
                            # todo 不认为该点是心跳点
                            temp_peak_index = None
                            flag3 = 0
                            pass
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











