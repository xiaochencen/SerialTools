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
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap
import threading, sys
from UIUnit.SetupUi import MainWindow, QIcon


# todo： 改变继承MainWindow 不然线程会卡在查找Port的While循环里
class Unit(MainWindow):
    detected_port = pyqtSignal()

    def __init__(self):
        super(Unit, self).__init__()
        self.UI = MainWindow()
        self.is_detect_serial_port = True
        self.com = QSerialPort()
        self.set_connect()
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

        # NoFlowControl          没有流程控制
        # HardwareControl        硬件流程控制(RTS/CTS)

        # SoftwareControl        软件流程控制(XON/XOFF)
        # UnknownFlowControl     未知控制
        self.com.setFlowControl(QSerialPort.NoFlowControl)
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
        if self.com.isOpen():
            self.com.close()
        super(Unit, self).closeEvent(event)

    def __read_ready(self):
        if self.com.bytesAvailable():
            # 当数据可读取时
            # 这里只是简答测试少量数据,如果数据量太多了此处readAll其实并没有读完
            # 需要自行设置粘包协议
            data = self.com.readAll()
            if self.receive_hex_checkbox.isChecked():
                # 如果勾选了hex显示
                data = data.toHex()
            data = data.data()
            # 解码显示（中文啥的）
            try:
                self.receive_area.append(data.decode('GB2312'))
            except:
                # 解码失败
                self.receive_area.append('Error Decode' + repr(data))

    def clear_show(self):
        self.receive_area.clear()
        pass

    













