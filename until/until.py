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
import threading, sys
from UIUnit.SetupUi import MainWindow, QIcon


class Unit(MainWindow):
    detected_port = pyqtSignal()

    def __init__(self):
        super(Unit, self).__init__()
        self.is_detect_serial_port = True
        self.com = QSerialPort()
        self.set_connect()
        self.detect_serial_port()

    def detect_serial_port(self):
        if self.is_detect_serial_port:
            self.is_detect_serial_port = False
            t = threading.Thread(target=self.detect_serial_process())
            t.setDaemon(True)  # could not understand thread
            t.start()

    def detect_serial_process(self):
        # running until find serial port
        while True:
            self.port_list = self.find_serial_port()
            if len(self.port_list):
                self.detected_port.emit()
                break

    def find_serial_port(self):
        port_list = QSerialPortInfo.availablePorts()
        return port_list

    def set_connect(self):
        self.detected_port.connect(self.update_auto)
        self.open_serial_button.clicked.connect(self.on_button_open_close_clicked())

    def update_auto(self):
        if len(self.port_list) > 0:
            current_text = self.serial_port_combobox.currentText()
            self.serial_port_combobox.clear()
            com_text = []
            for i in self.port_list:
                com_text.append(i.portName() + ' ' + i.description())

                pass
            self.serial_port_combobox.addItems(com_text)
            if current_text in com_text:
                self.serial_port_combobox.setCurrentText(current_text)
            else:
                self.serial_port_combobox.setCurrentIndex(0)
                self.serial_baudrate_combobox.clear()
                self.serial_baudrate_combobox.addItems(map(str, self.port_list[0].standardBaudRates()))

    def on_button_open_close_clicked(self):
        # 打开或关闭串口按钮
        if self.com.isOpen():
            # 如果串口是打开状态则关闭
            self.com.close()
            self.com.clear()
            self.status_bar_status.setText("<font color=%s>%s</font>"
                                           % ("#008200", self.config.get('Status Bar', 'Close')))
            self.open_serial_button.setIcon(self.config.get('Picture Setting', 'Close Button'))
            self.labelStatus.style().polish(self.labelStatus)  # 刷新样式
            return

        # 根据配置连接串口
        try:
            self.com.setPort(self.serial_port_combobox.currentText().split(' ')[0])
        except QSerialPort.DeviceNotFoundError:
            QMessageBox.Critical(self, 'Error', 'Serial port setting error!\nPlease check you port')
            return
        # 设置波特率
        self.com.setBaudRate(  # 动态获取, 类似QSerialPort::Baud9600这样的吧
            getattr(QSerialPort, 'Baud' + self.serial_baudrate_combobox.currentText()))
        # 设置校验位
        self.com.setParity(  # QSerialPort::NoParity
            getattr(QSerialPort, self.serial_parity_combobox.currentText() + 'Parity'))
        # 设置数据位
        self._serial.setDataBits(  # QSerialPort::Data8
            getattr(QSerialPort, 'Data' + self.serial_bytes_combobox.currentText()))
        # 设置停止位
        self._serial.setStopBits(  # QSerialPort::OneStop
            getattr(QSerialPort, self.comboBoxStop.currentText()) + 'Stop')

        # NoFlowControl          没有流程控制
        # HardwareControl        硬件流程控制(RTS/CTS)

        # SoftwareControl        软件流程控制(XON/XOFF)
        # UnknownFlowControl     未知控制
        self._serial.setFlowControl(QSerialPort.NoFlowControl)
        # 读写方式打开串口
        ok = self._serial.open(QIODevice.ReadWrite)
        if ok:
            self.textBrowser.append('打开串口成功')
            self.buttonConnect.setText('关闭串口')
            self.labelStatus.setProperty('isOn', True)
            self.labelStatus.style().polish(self.labelStatus)  # 刷新样式
        else:
            self.textBrowser.append('打开串口失败')
            self.buttonConnect.setText('打开串口')
            self.labelStatus.setProperty('isOn', False)
            self.labelStatus.style().polish(self.labelStatus)  # 刷新样式













