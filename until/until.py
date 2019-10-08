#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年9月4日
@author: chen wang
@email: 844379300@qq.com
@file: SerialPort until
@description:
"""
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtCore import pyqtSignal, QIODevice, QTimer
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QFileDialog
import threading, time
from functools import wraps
from UIUnit.SetupUi import MainWindow
from model import signal_process
from model import test
from numpy import save
from importlib import reload

import logging

until_logging = logging.getLogger(__name__)
LOG_FORMAT = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
handleStream = logging.StreamHandler()
handleStream.setFormatter(LOG_FORMAT)
handleStream.setLevel(logging.ERROR)
until_logging.addHandler(handleStream)


def clear_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        args[0].receive_count = 0
        args[0].status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(args[0].receive_count))
        self.heart_std_led_show.display(0)
        return func(self)
    return wrapper


class Unit(MainWindow):
    detected_port = pyqtSignal()

    def __init__(self):
        super(Unit, self).__init__()
        self.UI = MainWindow()
        self.is_detect_serial_port = True
        self.temp_hex_data = []
        self.temp_int_data = []
        self.com = QSerialPort()
        self.heart_rate_timer = QTimer()
        self.set_connect()
        self.receive_count = 0
        self.detect_serial_port()

    def detect_serial_port(self):
        if self.is_detect_serial_port:
            self.is_detect_serial_port = False
            # @warning 多线程的函数只写函数名，不能加上(),否者会死在子线程里
            t = threading.Thread(target=self.detect_serial_process)
            t.setDaemon(True)  # could not understand thread
            t.start()

    def detect_serial_process(self):
        # running until find serial port
        while True:
            self.port_list = QSerialPortInfo.availablePorts()
            if len(self.port_list):
                break
        self.detected_port.emit()

    def set_connect(self):
        # connect function to signal
        self.detected_port.connect(self.update_auto)
        self.open_serial_button.clicked.connect(self.on_button_open_close_clicked)
        self.com.readyRead.connect(self.__read_ready)
        self.clear_button.clicked.connect(self.clear_show)
        self.filter_data_checkbox.clicked.connect(self._check_parameter)
        self.transform_data_checkbox.clicked.connect(self._check_parameter)
        self.heart_rate_timer.timeout.connect(self.heart_rate_cal_process)
        self.heart_rate_release.clicked.connect(self.heart_rate_cal)
        self.heart_rate_debug_button.clicked.connect(self.heart_rate_debug)
        self.save_data_button.clicked.connect(self.save_data)
        self.load_action.triggered.connect(self.load_data)
        self.reload_action.triggered.connect(self.reload_model)

    def update_auto(self):
        # Auto update Serial port to combobox After Device inserted
        if len(self.port_list) > 0:
            self.serial_port_combobox.clear()
            com_text = []
            for i in self.port_list:
                com_text.append(i.portName() + ' ' + i.description())
                pass
            self.serial_port_combobox.addItems(com_text)

    def on_button_open_close_clicked(self):
        # 打开或关闭串口按钮
        if self.com.isOpen():
            self.com.close()
            if self.heart_rate_release.isChecked():
                self.heart_rate_release.setChecked(False)
            self.status_bar_status.setText("<font color=%s>%s</font>"
                                           % ("#008200", self.config.get('Status Bar', 'Close')))
            self.open_serial_button.setChecked(False)
            self.open_serial_button.setText('Serial Closed')
            return
        # 配置串口
        if self.serial_port_combobox.currentText().split(' ')[0]:
            self.com.setPortName(self.serial_port_combobox.currentText().split(' ')[0])
        else:
            QMessageBox.warning(self, 'Serial Warning', 'Have no Serial have been Choice')
            return
        # 设置波特率
        self.com.setBaudRate(  # 动态获取, 类似QSerialPort::Baud9600这样的吧
            getattr(QSerialPort, 'Baud' + self.serial_baudrate_combobox.currentText()))
        # 设置校验位
        self.com.setParity(  # QSerialPort::NoParity
            getattr(QSerialPort, self.serial_parity_combobox.currentText() + 'Parity'))
        # 设置数据位
        self.com.setDataBits(  # QSerialPort::Data8
            getattr(QSerialPort, 'Data' + self.serial_bytes_combobox.currentText()))
        # 设置停止位
        self.com.setStopBits(  # QSerialPort::OneStop
            getattr(QSerialPort, self.serial_stop_combobox.currentText() + 'Stop'))
        self.com.setFlowControl(  # QSerialPort::FlowControl
            getattr(QSerialPort, self.serial_flow_combobox.currentText() + 'Control'))
        # 读写方式打开串口
        try:
            self.com.open(QIODevice.ReadWrite)
            self.status_bar_status.setText("<font color=%s>%s</font>"
                                           % ("#008200", self.config.get('Status Bar', 'Open')))
            self.open_serial_button.setChecked(True)
            self.open_serial_button.setText("Serial Opened")

        except QSerialPort.OpenError:
            QMessageBox.critical(self, 'Serial Error', 'Open Serial Port Error!')
            return

    def closeEvent(self, event):
        # rewrite closeEvent
        if self.com.isOpen():
            self.com.close()
        self.save_parameter()
        super(Unit, self).closeEvent(event)

    def __read_ready(self):
        if self.com.bytesAvailable():
            data = self.com.readAll()
            if self.receive_hex_checkbox.isChecked():
                data = data.toHex()
            data = data.data()
            try:
                decode_data = data.decode(self.decoding_combobox.currentText())
                if self.filter_data_checkbox.isChecked():
                    show_data, rate = signal_process.filter_data(decode_data, self.begin_str_edit.text(),
                                                                 int(self.bytes_of_data_edit.text()),
                                                                 int(self.bytes_of_total_edit.text()),
                                                                 self.heart_rate_begin_edit.text(),
                                                                 self.filter_heart_rate.isChecked())
                    self.receive_count += len(show_data)
                    if rate != 0:
                        self.heart_std_led_show.display(rate)
                    self.temp_hex_data.extend(show_data)
                    for i in show_data:
                        self.receive_area.append(str(i))

                elif self.transform_data_checkbox.isChecked():
                    show_data, rate = signal_process.transform_data(decode_data, self.begin_str_edit.text(),
                                                                    int(self.bytes_of_data_edit.text()),
                                                                    int(self.bytes_of_total_edit.text()),
                                                                    self.heart_rate_begin_edit.text(),
                                                                    self.filter_heart_rate.isChecked())
                    self.receive_count += len(show_data)
                    self.temp_int_data.extend(show_data)
                    for i in show_data:
                        self.receive_area.append(str(i))
                    if rate != 0:
                        self.heart_std_led_show.display(rate)
                else:
                    self.receive_area.append(decode_data)
            except UnicodeError:
                # 解码失败
                self.receive_area.append('Error Decode' + repr(data))

            self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))

    @clear_decorator
    def clear_show(self):
        self.receive_area.clear()
        self.temp_int_data = []
        self.temp_hex_data = []
        pass

    def clear_count(self):
        self.receive_count = 0
        self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))

    def _check_parameter(self):
        sender = self.sender()
        if self.bytes_of_total_edit.text() == '':
            QMessageBox.critical(self, 'Parameter Error', 'Please input total bytes parameter')
            self.filter_data_checkbox.setChecked(False)
            self.transform_data_checkbox.setChecked(False)
            return
        if self.bytes_of_data_edit.text() == '':
            QMessageBox.critical(self, 'Parameter Error', 'Please input data bytes parameter')
            self.filter_data_checkbox.setChecked(False)
            self.transform_data_checkbox.setChecked(False)
            return
        if self.begin_str_edit.text() == '':
            QMessageBox.critical(self, 'Parameter Error', 'Please input Begin Mark parameter')
            self.filter_data_checkbox.setChecked(False)
            self.transform_data_checkbox.setChecked(False)
            return
        if sender == self.transform_data_checkbox:
            self.filter_data_checkbox.setChecked(False)

    def heart_rate_cal_process(self):
        # heart_rate_main(data, fs, threshold, scalar, smooth: bool, smooth_level):
        fs = int(self.fs_parameter.text())
        threshold = int(self.threshold_parameter.text())
        scalar = int(self.scalar_parameter.text())
        smooth = self.smooth_switch.isChecked()
        smooth_level = int(self.smooth_level.text())
        if len(self.temp_int_data) <= 768:
            data = self.temp_int_data
        else:
            data = self.temp_int_data[-768:]
        rate = test.heart_rate_main(data, fs, threshold, scalar, bool(smooth), smooth_level)
        self.heart_led_show.display(rate)

    def heart_rate_cal(self):
        if self.transform_data_checkbox.isChecked() and self.heart_rate_release.isChecked():
            self.heart_rate_timer.start(2000)
        else:
            self.heart_rate_timer.stop()

    def heart_rate_debug(self):
        fs = int(self.fs_parameter.text())
        threshold = int(self.threshold_parameter.text())
        scalar = int(self.scalar_parameter.text())
        smooth = self.smooth_switch.isChecked()
        smooth_level = int(self.smooth_level.text())
        try:
            begin = int(self.begin_cal_index_edit.text())
            end = int(self.end_cal_index_edit.text())
        except ValueError:
            begin = 0
            end = len(self.temp_int_data)-1
            until_logging.warning("Default Begin and End are used!")
        if len(self.temp_int_data)-1 < end:
            until_logging.error("Index over，Cut Down End Value !")
        data = self.temp_int_data[begin:end]
        rate = test.heart_rate_main_debug(data, fs, threshold, scalar, bool(smooth), smooth_level)
        self.heart_led_show.display(rate)

    def save_parameter(self):
        self.config['Data Format'] = {'Heart Begin': self.heart_rate_begin_edit.text(),
                                      'Begin Mark': self.begin_str_edit.text(),
                                      'Total Len': self.bytes_of_total_edit.text(),
                                      'Data Len': self.bytes_of_data_edit.text()}
        self.config['Heart Rate'] = {'Fs': self.fs_parameter.text(),
                                     'Threshold': self.threshold_parameter.text(),
                                     'Scalar': self.scalar_parameter.text(),
                                     'Smooth Level': self.smooth_level.text()}
        with open('config.ini', 'w') as config:
            self.config.write(config)

    def save_data(self):
        time_str = time.strftime('%Y-%m-%d-TIME%H-%M-%S', time.localtime())
        name, button = QInputDialog.getText(None, 'Input Name', 'Please input file Name')
        if button:
            file_name = name + time_str
            th = threading.Thread(target=save, args=(file_name, self.temp_int_data))
            th.start()
            th.join(100)
            #save(file_name, self.temp_int_data)
        else:
            pass

    def load_data(self):
        from numpy import load
        file, _ = QFileDialog.getOpenFileUrl(self, r'Choose File')
        try:
            self.temp_int_data = load(file.toLocalFile())
        except (TypeError, FileNotFoundError):
            until_logging.error("File Open Filed")
            return
        self.receive_count = len(self.temp_int_data)
        self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))

    def reload_model(self):
        # todo： 通过选择或是读取输入载入指定的模块。
        try:
            reload(signal_process)
            reload(test)
        except TypeError:
            QMessageBox.critical(self, "Reload Error", 'Check Your Input!')
            pass




















