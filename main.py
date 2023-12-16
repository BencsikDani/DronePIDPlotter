import sys
from PyQt5 import QtWidgets
from real_time_plot_app import RealTimePlotApp

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWin = RealTimePlotApp()
    mainWin.show()
    sys.exit(app.exec_())
