'''
funciton: process receive data
'''


def filter_data(data, mark, data_len, total_len):
    data = data.split(mark)[1:]
    f_data = []
    for i in data:
        if len(i) == total_len-len(mark):
            f_data.append(i[0:data_len])
    return f_data


def transform_data(data, mark, data_len, total_len):
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
    return t_data
