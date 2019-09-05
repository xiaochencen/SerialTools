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
            t_data.append(int(i[0:data_len], 16))
    return t_data
