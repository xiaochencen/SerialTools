from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QHBoxLayout,
                             QVBoxLayout, QComboBox, QPushButton, QCheckBox,
                             QSplitter, QAction, qApp, QTextEdit, QFormLayout,
                             QGroupBox, QGridLayout, QLabel)
from PyQt5.QtGui import QIcon
from PyQt5.QtSerialPort import QSerialPort
from configparser import ConfigParser


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigParser()
        self.com = QSerialPort()

        self.setting_widget = QWidget()
        self.show_widget = QWidget()
        self.info_widget = QWidget()
        self.main_widget = QSplitter()

        self.main_layout = QHBoxLayout()
        self.setting_layout = QVBoxLayout()
        self.show_layout = QVBoxLayout()

        self.open_serial_button = QPushButton()
        self.receive_hex = QCheckBox()
        self.receive_asc = QCheckBox()
        self.init_ui()
        self.init_connect()

    def init_ui(self):
        self.config.read('config.ini')
        self.open_serial_button.setText(self.config.get('Button Setting', 'Start'))
        self.setGeometry(self.config.getint('Size Setting', 'Geometry_ax'),
                         self.config.getint('Size Setting', 'Geometry_ay'),
                         self.config.getint('Size Setting', 'Geometry_xs'),
                         self.config.getint('Size Setting', 'Geometry_ys'))
        self.setWindowTitle(self.config.get('Text Setting', 'MainWindow_Title'))
        self.setWindowIcon(QIcon(self.config.get('Picture Setting', 'MainWind_icon')))
        self.main_widget.addWidget(self.setting_widget)
        self.main_widget.addWidget(self.show_widget)
        self.main_widget.addWidget(self.info_widget)
        self.main_widget.setStretchFactor(0, 2)
        self.main_widget.setStretchFactor(1, 12)
        self.main_widget.setStretchFactor(2, 2)

        self.init_show_widget()
        self.init_statue_bar()
        self.init_menu_bar()
        self.init_setting_widget()
        self.setCentralWidget(self.main_widget)

    def init_menu_bar(self):
        scan_action = QAction('Scan(&S)', self)
        port_setting_action = QAction('Port(&P)', self)
        scan_action.setShortcut('Ctrl+S')
        # scan_action.triggered.connect(self.)
        port_menu = self.menuBar().addMenu('Port(&P)')
        port_menu.addAction(scan_action)
        view_menu = self.menuBar().addMenu('View(&V)')
        view_menu.addAction(port_setting_action)

    def init_setting_widget(self):
        group_box = QGroupBox('SerialSetting')
        serial_setting_layout = QFormLayout()
        self.serial_port_combobox = QComboBox()
        self.serial_baudrate_combobox = QComboBox()
        self.serial_bytes_combobox = QComboBox()
        self.serial_parity_combobox = QComboBox()
        self.serial_baudrate_combobox.addItems(['9600', '16200', '38400'])
        self.serial_baudrate_combobox.setCurrentIndex(1)
        self.serial_baudrate_combobox.setEditable(True)
        self.serial_bytes_combobox.addItems(['5', '6', '7', '8'])
        self.serial_bytes_combobox.setCurrentIndex(3)
        self.serial_parity_combobox.addItems(['None', 'Odd', 'Space'])
        self.serial_parity_combobox.setCurrentIndex(0)
        # learn QFromLayout
        serial_setting_layout.addRow(QLabel(r'端口'), self.serial_port_combobox)
        serial_setting_layout.addRow(QLabel(r'波特率'), self.serial_baudrate_combobox)
        serial_setting_layout.addRow(QLabel(r'分割符'), self.serial_parity_combobox)
        serial_setting_layout.addRow(QLabel(r'数据位数'), self.serial_bytes_combobox)
        serial_setting_layout.addRow(QLabel(r'打开串口'), self.open_serial_button)
        group_box.setLayout(serial_setting_layout)
        self.setting_layout.addWidget(group_box)

        receive_group_box = QGroupBox('Receive Setting')
        serial_receive_layout = QGridLayout()
        hex_label = QLabel('Hex')
        asc_label = QLabel('ASC')
        self.receive_hex.setChecked(True)
        self.receive_asc.setChecked(False)
        self.check_box_rts = QCheckBox('Rts')
        self.check_box_dtr = QCheckBox('Dtr')
        # learn QGridLayout
        serial_receive_layout.addWidget(hex_label, 0, 0)
        serial_receive_layout.addWidget(self.receive_hex, 0, 1)
        serial_receive_layout.addWidget(asc_label, 0, 2)
        serial_receive_layout.addWidget(self.receive_asc, 0, 3)
        serial_receive_layout.addWidget(self.check_box_dtr, 1, 0)
        serial_receive_layout.addWidget(self.check_box_rts, 1, 1)
        receive_group_box.setLayout(serial_receive_layout)
        self.setting_layout.addWidget(receive_group_box)
        self.setting_layout.addStretch()
        self.setting_widget.setLayout(self.setting_layout)
        pass

    def init_show_widget(self):
        button_layout = QGridLayout()
        info_layout = QGroupBox()
        self.receive_area = QTextEdit()
        self.clear_button = QPushButton(self.config.get('Button Setting', 'Clear'))
        # self.show_wave =
        self.show_widget.setLayout(self.show_layout)
        self.show_layout.addWidget(self.receive_area)
        self.show_layout.addWidget(self.clear_button)
        pass

    # detail information show and seq setting
    def init_info_widget(self):
        pass

    def init_statue_bar(self):
        pass

    def init_connect(self):
        pass



