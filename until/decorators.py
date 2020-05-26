import threading
from functools import wraps


def threading_decorator(func):
    # 多线程装饰器
    @wraps(func)
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=func, args=args, kwargs=kwargs)
        thr.start()
        thr.setName("func-{}".format(func.__name__))
    return wrapper


def clear_decorator(func):
    # 装饰器清空显示数据
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        args[0].receive_count = 0
        args[0].status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(args[0].receive_count))
        return func(self)
    return wrapper
