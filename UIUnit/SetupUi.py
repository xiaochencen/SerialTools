from PyQt5.QtCore import (pyqtSlot, pyqtSignal, Qt,)
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QHBoxLayout,
                             QVBoxLayout, QComboBox, QPushButton, QCheckBox,
                             QSplitter, QAction, qApp, QTextEdit, QFormLayout,
                             QGroupBox, QGridLayout, QLabel, QLineEdit)
from PyQt5.QtGui import (QIcon, QPixmap, QIntValidator)
from configparser import ConfigParser


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.config = ConfigParser()
        self.setting_widget = QWidget()
        self.show_widget = QWidget()
        self.heart_function_widget = QWidget()
        self.main_widget = QSplitter()

        self.main_layout = QHBoxLayout()
        self.setting_layout = QVBoxLayout()
        self.show_layout = QVBoxLayout()

        self.open_serial_button = QPushButton()
        self.receive_hex_checkbox = QCheckBox('HEX')
        self.receive_asc_checkbox = QCheckBox('ASCII')
        self.init_ui()

    def init_ui(self):
        self.config.read('config.ini')
        self.setGeometry(self.config.getint('Size Setting', 'Geometry_ax'),
                         self.config.getint('Size Setting', 'Geometry_ay'),
                         self.config.getint('Size Setting', 'Geometry_xs'),
                         self.config.getint('Size Setting', 'Geometry_ys'))
        # todo: change the version number automatically
        self.setWindowTitle(self.config.get('Text Setting', 'MainWindow_Title')+'--V1.0')

        self.setWindowIcon(QIcon(self.config.get('Picture Setting', 'MainWind_icon')))
        self.main_widget.addWidget(self.setting_widget)
        self.main_widget.addWidget(self.show_widget)
        self.main_widget.addWidget(self.heart_function_widget)
        self.main_widget.setStretchFactor(0, 2)
        self.main_widget.setStretchFactor(1, 12)
        self.main_widget.setStretchFactor(2, 2)
        self.open_serial_button.setCheckable(True)
        self.open_serial_button.setText('Click')
        self.init_show_widget()
        self.init_statue_bar()
        self.init_menu_bar()
        self.init_setting_widget()
        self.init_heart_function_widget()
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
        # serial setting part set
        # port set part
        group_box = QGroupBox('SerialSetting')
        serial_setting_layout = QFormLayout()
        self.serial_port_combobox = QComboBox()
        self.serial_baudrate_combobox = QComboBox()
        self.serial_bytes_combobox = QComboBox()
        self.serial_parity_combobox = QComboBox()
        self.serial_stop_combobox = QComboBox()
        self.serial_flow_combobox = QComboBox()
        self.serial_baudrate_combobox.addItems(['1200', '2400', '4800', '9600', '19200',
                                                '38400', '57600', '115200'])
        self.serial_baudrate_combobox.setCurrentIndex(3)
        self.serial_baudrate_combobox.setEditable(True)
        self.serial_bytes_combobox.addItems(['5', '6', '7', '8'])
        self.serial_bytes_combobox.setCurrentIndex(3)
        self.serial_parity_combobox.addItems(['No', 'Odd', 'Space', 'Even', 'Mark'])
        self.serial_parity_combobox.setCurrentIndex(0)
        self.serial_stop_combobox.addItems(['One', 'OneAndHalf', 'Two'])
        self.serial_flow_combobox.addItems(['NoFlow', 'Hardware', 'Software', 'UnknownFlow'])
        self.serial_flow_combobox.setCurrentIndex(0)
        # learn QFromLayout
        serial_setting_layout.addRow(QLabel(r'端口'), self.serial_port_combobox)
        serial_setting_layout.addRow(QLabel(r'波特率'), self.serial_baudrate_combobox)
        serial_setting_layout.addRow(QLabel(r'分割符'), self.serial_parity_combobox)
        serial_setting_layout.addRow(QLabel(r'数据位数'), self.serial_bytes_combobox)
        serial_setting_layout.addRow(QLabel(r'流控制'), self.serial_flow_combobox)
        serial_setting_layout.addRow(QLabel(r'打开串口'), self.open_serial_button)
        group_box.setLayout(serial_setting_layout)

        # receive set part
        receive_group_box = QGroupBox('Receive Setting')
        data_process_group_box = QGroupBox('Data Process')
        hex_or_ascii_layout = QHBoxLayout()
        data_process_layout = QHBoxLayout()
        receive_layout = QGridLayout()
        self.receive_hex_checkbox.setChecked(True)
        self.receive_asc_checkbox.setChecked(False)
        self.receive_asc_checkbox.setAutoExclusive(True)
        self.receive_hex_checkbox.setAutoExclusive(True)
        hex_or_ascii_layout.addWidget(self.receive_hex_checkbox)
        hex_or_ascii_layout.addWidget(self.receive_asc_checkbox)
        receive_layout.addLayout(hex_or_ascii_layout, 0, 0)
        self.filter_data_checkbox = QCheckBox('数据过滤')
        self.filter_data_checkbox.setObjectName('filter_data_checkbox')
        self.transform_data_checkbox = QCheckBox('数据转换')
        self.transform_data_checkbox.setObjectName('transform_data_checkbox')
        data_process_layout.addWidget(self.filter_data_checkbox)
        data_process_layout.addWidget(self.transform_data_checkbox)
        data_process_group_box.setLayout(data_process_layout)
        receive_group_box.setLayout(receive_layout)

        self.setting_layout.addWidget(group_box)
        self.setting_layout.addWidget(receive_group_box)
        self.setting_layout.addWidget(data_process_group_box)
        self.setting_layout.addStretch()
        self.setting_widget.setLayout(self.setting_layout)
        pass

    def init_show_widget(self):
        show_button_layout = QGridLayout()
        show_info_layout = QHBoxLayout()
        self.decoding_combobox = QComboBox()
        self.decoding_combobox.addItems(['ASCII', 'GB2312'])
        self.decoding_combobox.setEditable(False)
        self.receive_area = QTextEdit()
        self.receive_area.setTabletTracking(True)
        self.clear_button = QPushButton(self.config.get('Button Setting', 'Clear'))
        # self.show_wave =
        show_button_layout.addWidget(self.clear_button, 0, 0)
        show_info_layout.addWidget(self.decoding_combobox)
        self.show_widget.setLayout(self.show_layout)
        self.show_layout.addWidget(self.receive_area)
        self.show_layout.addLayout(show_info_layout)
        self.show_layout.addLayout(show_button_layout)

        pass

    # detail information show and seq setting
    def init_heart_function_widget(self):
        function_layout = QVBoxLayout()
        data_format_group = QGroupBox('Data Format')
        data_format_layout = QFormLayout()
        self.begin_str_edit = QLineEdit()
        self.bytes_of_data_edit = QLineEdit()
        self.bytes_of_total_edit = QLineEdit()
        self.bytes_of_data_edit.setValidator(QIntValidator(1, 100))
        self.bytes_of_data_edit.setPlaceholderText("0~100")
        self.bytes_of_total_edit.setValidator(QIntValidator(1, 100))
        self.bytes_of_total_edit.setPlaceholderText("0~100")
        data_format_layout.addRow(QLabel('Begin Mark:'), self.begin_str_edit)
        data_format_layout.addRow(QLabel('Total Bytes:'), self.bytes_of_total_edit)
        data_format_layout.addRow(QLabel('Data Bytes:'), self.bytes_of_data_edit)
        data_format_group.setLayout(data_format_layout)
        function_layout.addWidget(data_format_group)
        self.heart_function_widget.setLayout(function_layout)
        function_layout.addStretch()
        pass

    def init_statue_bar(self):
        # todo: 可以增加状态闪烁的功能 使用QTime
        self.status_bar_status = QLabel()
        self.status_bar_status.setMinimumWidth(80)
        self.status_bar_status.setText("<font color=%s>%s</font>" % ("#008200", self.config.get('Status Bar', 'OK')))
        self.status_bar_recieve_count = QLabel(r'Receive '+r'Bytes:'+'0')
        self.statusBar().addWidget(self.status_bar_status)
        self.statusBar().addWidget(self.status_bar_recieve_count, 2)
        pass


