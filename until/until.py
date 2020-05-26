#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年9月4日
@author: chen wang
@email: 844379300@qq.com
@file: SerialPort until
@description:
"""
import logging
import threading
import time
from until import decorators
from importlib import reload

from PyQt5.QtCore import pyqtSignal, QIODevice, QTimer, Qt
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QFileDialog
from numpy import save

from UIUnit.SetupUi import MainWindow
from model import signal_process
from model import test

until_logging = logging.getLogger(__name__)
LOG_FORMAT = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
handleStream = logging.StreamHandler()
handleFile = logging.FileHandler('Heart_rate_He.log')
handleStream.setFormatter(LOG_FORMAT)
handleStream.setLevel(logging.ERROR)
handleFile.setLevel(logging.CRITICAL)
handleFile.setFormatter(LOG_FORMAT)
until_logging.addHandler(handleStream)
until_logging.addHandler(handleFile)


class Unit(MainWindow):
    detected_port = pyqtSignal()
    update_heart = pyqtSignal(float)
    update_impedance_int = pyqtSignal([list], [int])
    update_impedance_hex = pyqtSignal([list], [str])

    def __init__(self):
        super(Unit, self).__init__()
        self.temp_hex_data = []
        self.temp_int_data = []
        self.port_list = []
        self.receive_count = 0
        self.send_count = 0
        self.times = 100
        self.detect_Timer = QTimer()
        self.detect_Timer.start(1000)
        self.com = QSerialPort()
        self.heart_rate_timer = QTimer()
        self.send_data_timer = QTimer()
        self.plot_update_timer = QTimer()
        self.set_connect()

    def detect_serial_process(self):
        # running until find serial port
        temp_port = QSerialPortInfo.availablePorts()
        temp_name = [i.portName() + ' ' + i.description() for i in temp_port]
        if temp_name != self.port_list:
            self.port_list = temp_name
            self.detected_port.emit()

    def set_connect(self):
        # connect function to signal
        self.detected_port.connect(self.update_auto)
        self.open_serial_button.clicked.connect(self.on_button_open_close_clicked)
        self.com.readyRead.connect(self.read_ready, Qt.QueuedConnection)
        self.clear_button.clicked.connect(self.clear_show)
        self.transform_data_checkbox.clicked.connect(self._check_parameter)
        self.heart_rate_timer.timeout.connect(self.heart_rate_cal_process)
        self.detect_Timer.timeout.connect(self.detect_serial_process)
        self.heart_rate_release.clicked.connect(self.heart_rate_cal)
        self.heart_rate_debug_button.clicked.connect(self.heart_rate_debug)
        self.save_data_button.clicked.connect(self.save_data)
        self.load_action.triggered.connect(self.load_data)
        self.reload_action.triggered.connect(self.reload_model)
        self.update_impedance_int.connect(self.on_impedance_int_update)
        self.update_impedance_hex[str].connect(self.on_impedance_hex_update)
        self.update_impedance_hex[list].connect(self.on_impedance_hex_update)
        self.plot_update_timer.timeout.connect(self.update_plot)
        self.send_button.clicked.connect(self.uart_send)
        self.send_data_timer.timeout.connect(self._timer_send)

    def update_auto(self):
        # Auto update Serial port to combobox After Device inserted
        self.serial_port_combobox.clear()
        self.serial_port_combobox.addItems(self.port_list)

    def on_button_open_close_clicked(self):
        # 打开或关闭串口按钮
        if self.com.isOpen():
            self.plot_update_timer.stop()
            self.com.close()
            if self.heart_rate_release.isChecked():
                self.heart_rate_release.setChecked(False)
            self.status_bar_status.setText("<font color=%s>%s</font>"
                                           % ("#008200", self.config.get('Status Bar', 'Close')))
            self.open_serial_button.setStyleSheet("background-color:red")
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
            self.com.setDataTerminalReady(True)
            self.status_bar_status.setText("<font color=%s>%s</font>"
                                           % ("#008200", self.config.get('Status Bar', 'Open')))
            self.open_serial_button.setStyleSheet("background-color:green")
            self.plot_update_timer.start(16)
        except QSerialPort.OpenError:
            QMessageBox.critical(self, 'Serial Error', 'Open Serial Port Error!')
            return

    def closeEvent(self, event):
        # rewrite closeEvent
        if self.com.isOpen():
            self.com.close()
        self.save_parameter()
        super(Unit, self).closeEvent(event)

    def read_ready(self):
        th = threading.Thread(target=Unit.__read_ready, args=(self,))
        th.start()

    def __read_ready(self):
        if self.com.bytesAvailable():
            time.sleep(0.01)
            data = self.com.readAll()
            if self.receive_hex_checkbox.isChecked():
                data = data.toHex()
            data = data.data()
            try:
                decode_data = data.decode(self.decoding_combobox.currentText())
                self.receive_count += len(decode_data)
                if self.transform_data_checkbox.isChecked():  # 执行数据转换
                    show_data = signal_process.transform_data(decode_data,
                                                              int(self.bytes_of_start_point.text()),
                                                              int(self.bytes_of_total_edit.text()),
                                                              int(self.bytes_of_stop_point.text()))
                    self.receive_count += len(show_data)
                    self.temp_int_data.extend(show_data)
                    self.update_impedance_int.emit(show_data)
                else:
                    self.update_impedance_hex[str].emit(decode_data)
                    pass
            except UnicodeError:
                # 解码失败
                pass

    @decorators.clear_decorator
    def clear_show(self):
        self.receive_area.clear()
        self.temp_int_data = []
        self.temp_hex_data = []
        t = threading.Thread(target=self.clear_plot)
        t.start()
        pass

    def clear_plot(self):
        self.plot_1.clear()
        self.plot_2.clear()

    def clear_count(self):
        self.receive_count = 0
        self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))

    def _check_parameter(self):
        sender = self.sender()
        if self.bytes_of_total_edit.text() == '':
            QMessageBox.critical(self, 'Parameter Error', 'Please input total bytes parameter')
            self.transform_data_checkbox.setChecked(False)
            return
        if self.bytes_of_start_point.text() == '':
            QMessageBox.critical(self, 'Parameter Error', 'Please input data bytes parameter')
            self.transform_data_checkbox.setChecked(False)
            return
        if self.bytes_of_stop_point.text() == '':
            QMessageBox.critical(self, 'Parameter Error', 'Please input Begin Mark parameter')
            self.transform_data_checkbox.setChecked(False)
            return

    def heart_rate_cal_process(self):
        # heart_rate_main(data, fs, threshold, scalar, smooth: bool, smooth_level):
        fs = int(self.fs_parameter.text())
        threshold = int(self.threshold_parameter.text())
        scalar = int(self.scalar_parameter.text())
        smooth = self.smooth_switch.isChecked()
        smooth_level = int(self.smooth_level.text())
        if len(self.temp_int_data) <= 640:
            data = self.temp_int_data
        else:
            data = self.temp_int_data[-640:]
        rate, temp, index = test.heart_rate_main(data, fs, threshold, scalar, bool(smooth), smooth_level)
        self.update_plot_p2(temp, index)
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
        self.config['Data Format'] = {'Data Begin': self.bytes_of_start_point.text(),
                                      'Data Stop': self.bytes_of_stop_point.text(),
                                      'Total Len': self.bytes_of_total_edit.text()}
        self.config['Heart Rate'] = {'Fs': self.fs_parameter.text(),
                                     'Threshold': self.threshold_parameter.text(),
                                     'Scalar': self.scalar_parameter.text(),
                                     'Smooth Level': self.smooth_level.text()}
        self.config['Send Config'] = {'send times': self.times_edit.text(),
                                      'send interval': self.send_interval_edit.text(),
                                      'send data': self.send_area.toPlainText()}
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
        self.update_plot()
        self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))

    def reload_model(self):
        # todo： 通过选择或是读取输入载入指定的模块。
        try:
            reload(signal_process)
            reload(test)
        except TypeError:
            QMessageBox.critical(self, "Reload Error", 'Check Your Input!')
            pass

    def on_impedance_hex_update(self, show_data):
        self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))
        if type(show_data) is list:
            for i in show_data:
                self.receive_area.append(str(i))
        elif type(show_data) is str:
            self.receive_area.append(show_data)
        else:
            pass

    def on_impedance_int_update(self, show_data):
        self.status_bar_recieve_count.setText(r'Receive ' + r'Bytes:' + str(self.receive_count))
        for i in show_data:
            self.receive_area.append(str(i))
        pass

    @decorators.threading_decorator
    def update_plot_p1(self):
        # 更新polt1画图
        if len(self.temp_int_data):
            curve = self.plot_1.plot()
            curve.setData(self.temp_int_data, pen=(0, 255, 255))
            self.plot_1.setXRange(max(0, len(self.temp_int_data)-640), len(self.temp_int_data))
            self.plot_1.setYRange(min(self.temp_int_data[-640:]), max(self.temp_int_data[-640:]))

    def update_plot_p2(self, temp, index):
        # 更新plot2画图,使用原始数据中的640个点
        self.plot_2.clear()
        self.plot_2.plot(temp, pen=(0, 255, 255))
        y_data = [temp[s] for s in index]
        self.plot_2.plot(index, y_data, pen=(0, 0, 0), symbolBrush=(255, 0, 0),
                         symbolPen='w', symbol='t', symbolSize=10)

    def update_plot(self):
        self.update_plot_p1()

    def uart_send(self):
        if self.times_send_chebox.isChecked():
            try:
                interrupt_times = int(self.send_interval_edit.text())
            except ValueError:
                interrupt_times = 2000
            try:
                self.times = int(self.times_edit.text())
            except ValueError:
                pass
            self.send_data_timer.start(interrupt_times)
            self.send_button.setCheckable(False)
        else:
            self._timer_send()

    def _timer_send(self):
        if self.com.isOpen():
            data = self.send_area.toPlainText()
            if data != '':
                if self.send_code_combox.currentText() == 'HEX':
                    data = data.strip()
                    send_list = []
                    while data != '':
                        try:
                            num = int(data[0:2], 16)
                        except ValueError:
                            QMessageBox.critical(self, 'Error Data', 'Please Check you Send Data')
                            return
                        data = data[2:].strip()
                        send_list.append(num)
                    data = bytes(send_list)
                else:
                    data = (data+'\r\n').encode('utf-8')
                num = self.com.write(data)
                self.send_count += num
            else:
                pass
        if self.times_send_chebox.isChecked():
            self.times -= 1
            if self.times == 0:
                self.send_data_timer.stop()
                self.send_button.setCheckable(True)
                self.times_send_chebox.setChecked(False)





















