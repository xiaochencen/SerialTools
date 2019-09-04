from PyQt5.QtSerialPort import QSerialPort


class QSerial():
    def __init__(self, port: QSerialPort):
        self.port = port


