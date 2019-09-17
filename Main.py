from until.until import Unit
from PyQt5.QtWidgets import QApplication
import sys


def main():
    app = QApplication(sys.argv)
    main_window = Unit()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()