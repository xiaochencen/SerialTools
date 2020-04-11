import re

import matplotlib.pyplot as plt
import numpy as np


def transform_hex_int(hex_data: list = [], len_data: int = 0):
    ans = []
    for i in hex_data:
        if len(i) is len_data:
            dec_data = int(i[-6:], 16)
            ans.append(dec_data)
    return ans


def func_data_process(scalar: int = 8, smooth_level: int = 6, data_scalar: list = []):
    temp = sp.average_move_filter(filter_data=data_scalar, smooth_level=smooth_level)
    temp = [0 if d <= 0 else d for d in np.array(temp[scalar:])
            - np.array(temp[0:-scalar])]
    return temp





data = np.loadtxt(r"C:\Users\Minder\Desktop\新建文本文档 (3).txt", dtype=str)
data = ''.join(data)
import model.signal_process as sp
data1=sp.transform_data(data,6,16)
data = re.findall(r'.{16}', data)
dec_data = transform_hex_int(data, 16)

diff_data = func_data_process(data_scalar=dec_data)
temp = sp.average_move_filter(filter_data=dec_data, smooth_level=6)
plt.subplot(311)
plt.plot(dec_data)
plt.subplot(312)
plt.plot(temp)
plt.subplot(313)
plt.plot(diff_data)
plt.show()

pass
