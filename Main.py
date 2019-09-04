from UIUnit.SetupUi import MainWindow
from PyQt5.QtWidgets import QApplication
import sys, os


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()