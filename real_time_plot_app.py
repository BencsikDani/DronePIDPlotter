from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QFont
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from real_time_plot_worker import RealTimePlotWorker, data, stored_gains
import serial_connection
from collections import deque


matplotlib.use('Qt5Agg')

# Constants
com_port = 'COM10'
baud_rate = 115200
pid2_fft = False

# Create deques to store received data for real-time plotting
buflen = 500
half_buflen = 1+250

pid1_ref_data = deque(maxlen=buflen)
pid1_meas_data = deque(maxlen=buflen)
pid1_out_data = deque(maxlen=buflen)
pid2_ref_data = deque(maxlen=buflen)
pid2_meas_data = deque(maxlen=buflen)
pid2_out_data = deque(maxlen=buflen)
pid3_ref_data = deque(maxlen=buflen)
pid3_meas_data = deque(maxlen=buflen)
pid3_out_data = deque(maxlen=buflen)
pid4_ref_data = deque(maxlen=buflen)
pid4_meas_data = deque(maxlen=buflen)
pid4_out_data = deque(maxlen=buflen)
pid5_ref_data = deque(maxlen=buflen)
pid5_meas_data = deque(maxlen=buflen)
pid5_out_data = deque(maxlen=buflen)
pid6_ref_data = deque(maxlen=buflen)
pid6_meas_data = deque(maxlen=buflen)
pid6_out_data = deque(maxlen=buflen)

pid2_meas_FFT_data = deque(maxlen=half_buflen)

buffers = [pid1_ref_data, pid1_meas_data, pid1_out_data,
           pid2_ref_data, pid2_meas_data, pid2_out_data,
           pid3_ref_data, pid3_meas_data, pid3_out_data,
           pid4_ref_data, pid4_meas_data, pid4_out_data,
           pid5_ref_data, pid5_meas_data, pid5_out_data,
           pid6_ref_data, pid6_meas_data, pid6_out_data,
           pid2_meas_FFT_data]

for b in buffers:
    for i in range(buflen):
        b.append(None)

class RealTimePlotApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.set_textboxes = None
        self.set_buttons = None
        self.plot_thread = None
        self.initUI()

    def initUI(self):
        bigfont = QFont('Time New Roman', 15)

        # Window parameters
        self.setWindowTitle('PID GUI')
        #self.setGeometry(50, 50, 950, 950)
        self.resize(1200, 900)

        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


        # Outer layout
        outer_layout = QtWidgets.QHBoxLayout()
        self.setLayout(outer_layout)

        # Left side of the main outer layout
        left_layout = QtWidgets.QVBoxLayout()
        outer_layout.addLayout(left_layout)

        # Right side of the main outer layout
        right_layout = QtWidgets.QVBoxLayout()
        outer_layout.addLayout(right_layout)

        # region Left
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        panel_layout = QtWidgets.QVBoxLayout()
        left_layout.addLayout(panel_layout)

        button_layout = QtWidgets.QHBoxLayout()
        panel_layout.addLayout(button_layout)

        # region Button
        # --------------------------------------------------------------------------------------------------------------
        self.startButton = QtWidgets.QPushButton('Start Plot')
        self.startButton.clicked.connect(self.start_plotting)
        button_layout.addWidget(self.startButton)

        self.stopButton = QtWidgets.QPushButton('Stop Plot')
        self.stopButton.setEnabled(False)
        self.stopButton.clicked.connect(self.stop_plotting)
        button_layout.addWidget(self.stopButton)
        # --------------------------------------------------------------------------------------------------------------
        # endregion Button

        self.throttle_label = QtWidgets.QLabel("Throttle:  0\n0  0  0  0")
        self.throttle_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.throttle_label.setContentsMargins(0, 10, 0, 0)
        self.throttle_label.setFont(bigfont)
        panel_layout.addWidget(self.throttle_label)

        self.pid_all_label = QtWidgets.QLabel('PID_Ro:  0.0  0.0  0.0\nPID_Ri:  0.0  0.0  0.0\nPID_Po:  0.0  0.0  0.0\nPID_Pi:  0.0  0.0  0.0\nPID_Y:  0.0  0.0  0.0\nPID_T:  0.0  0.0  0.0')
        self.pid_all_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.pid_all_label.setFont(bigfont)
        panel_layout.addWidget(self.pid_all_label)

        self.refreshButton = QtWidgets.QPushButton('Refresh Gains')
        self.refreshButton.setFixedHeight(40)
        self.refreshButton.setEnabled(False)
        self.refreshButton.clicked.connect(self.refresh_gains)
        panel_layout.addWidget(self.refreshButton)

        plot_radio_layout = QtWidgets.QHBoxLayout()
        plot_radio_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        panel_layout.addLayout(plot_radio_layout)

        # region Radio
        # --------------------------------------------------------------------------------------------------------------
        self.rollRadioButton = QtWidgets.QRadioButton('Roll')
        self.rollRadioButton.text = 'Roll'
        self.rollRadioButton.setChecked(True)
        plot_radio_layout.addWidget(self.rollRadioButton)

        self.pitchRadioButton = QtWidgets.QRadioButton('Pitch')
        self.pitchRadioButton.text = 'Pitch'
        plot_radio_layout.addWidget(self.pitchRadioButton)

        self.yawRadioButton = QtWidgets.QRadioButton('Yaw')
        self.yawRadioButton.text = 'Yaw'
        plot_radio_layout.addWidget(self.yawRadioButton)

        self.throttleRadioButton = QtWidgets.QRadioButton('Throttle')
        self.throttleRadioButton.text = 'Throttle'
        plot_radio_layout.addWidget(self.throttleRadioButton)

        self.radio_buttons = [self.rollRadioButton, self.pitchRadioButton, self.yawRadioButton, self.throttleRadioButton]
        # --------------------------------------------------------------------------------------------------------------
        # endregion Radio

        # region Scroll
        # --------------------------------------------------------------------------------------------------------------
        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedWidth(300)
        scroll.setFixedHeight(600)
        scroll.setWidgetResizable(True)
        panel_layout.addWidget(scroll)

        scrollWidget = QtWidgets.QWidget()
        scroll.setWidget(scrollWidget)

        scrollContent = QtWidgets.QVBoxLayout()
        scrollWidget.setLayout(scrollContent)
        # --------------------------------------------------------------------------------------------------------------
        # endregion Radio


        pid1_label = QtWidgets.QLabel('Roll outer PID')
        pid1_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        pid1_label.setContentsMargins(0, 10, 0, 0)
        scrollContent.addWidget(pid1_label)

        pid1_grid = QtWidgets.QGridLayout()
        scrollContent.addLayout(pid1_grid)

        # region PID1 Grid
        # --------------------------------------------------------------------------------------------------------------
        pid1_kp_label = QtWidgets.QLabel('Kp')
        pid1_kp_label.setFixedWidth(20)
        pid1_kp_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid1_grid.addWidget(pid1_kp_label, 1, 1)

        pid1_ki_label = QtWidgets.QLabel('Ki')
        pid1_ki_label.setFixedWidth(20)
        pid1_ki_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid1_grid.addWidget(pid1_ki_label, 2, 1)

        pid1_kd_label = QtWidgets.QLabel('Kd')
        pid1_kd_label.setFixedWidth(20)
        pid1_kd_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid1_grid.addWidget(pid1_kd_label, 3, 1)

        self.pid1_kp_tb = QtWidgets.QLineEdit()
        self.pid1_kp_tb.setFixedWidth(120)
        pid1_grid.addWidget(self.pid1_kp_tb, 1, 2)

        self.pid1_ki_tb = QtWidgets.QLineEdit()
        self.pid1_ki_tb.setFixedWidth(120)
        pid1_grid.addWidget(self.pid1_ki_tb, 2, 2)

        self.pid1_kd_tb = QtWidgets.QLineEdit()
        self.pid1_kd_tb.setFixedWidth(120)
        pid1_grid.addWidget(self.pid1_kd_tb, 3, 2)

        self.pid1_kp_btn = QtWidgets.QPushButton('Set')
        self.pid1_kp_btn.setFixedWidth(80)
        self.pid1_kp_btn.setEnabled(False)
        self.pid1_kp_btn.clicked.connect(self.send_pid1_kp)
        pid1_grid.addWidget(self.pid1_kp_btn, 1, 3)

        self.pid1_ki_btn = QtWidgets.QPushButton('Set')
        self.pid1_ki_btn.setFixedWidth(80)
        self.pid1_ki_btn.setEnabled(False)
        self.pid1_ki_btn.clicked.connect(self.send_pid1_ki)
        pid1_grid.addWidget(self.pid1_ki_btn, 2, 3)

        self.pid1_kd_btn = QtWidgets.QPushButton('Set')
        self.pid1_kd_btn.setFixedWidth(80)
        self.pid1_kd_btn.setEnabled(False)
        self.pid1_kd_btn.clicked.connect(self.send_pid1_kd)
        pid1_grid.addWidget(self.pid1_kd_btn, 3, 3)
        # --------------------------------------------------------------------------------------------------------------
        # endregion PID1 Grid

        pid2_label = QtWidgets.QLabel('Roll inner PID')
        pid2_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        pid2_label.setContentsMargins(0, 10, 0, 0)
        scrollContent.addWidget(pid2_label)

        pid2_grid = QtWidgets.QGridLayout()
        scrollContent.addLayout(pid2_grid)

        # region PID2 Grid
        # --------------------------------------------------------------------------------------------------------------
        pid2_kp_label = QtWidgets.QLabel('Kp')
        pid2_kp_label.setFixedWidth(20)
        pid2_kp_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid2_grid.addWidget(pid2_kp_label, 1, 1)

        pid2_ki_label = QtWidgets.QLabel('Ki')
        pid2_ki_label.setFixedWidth(20)
        pid2_ki_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        #pid2_grid.addWidget(pid2_ki_label, 2, 1)

        pid2_kd_label = QtWidgets.QLabel('Kd')
        pid2_kd_label.setFixedWidth(20)
        pid2_kd_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid2_grid.addWidget(pid2_kd_label, 3, 1)

        self.pid2_kp_tb = QtWidgets.QLineEdit()
        self.pid2_kp_tb.setFixedWidth(120)
        pid2_grid.addWidget(self.pid2_kp_tb, 1, 2)

        self.pid2_ki_tb = QtWidgets.QLineEdit()
        self.pid2_ki_tb.setFixedWidth(120)
        #pid2_grid.addWidget(self.pid2_ki_tb, 2, 2)

        self.pid2_kd_tb = QtWidgets.QLineEdit()
        self.pid2_kd_tb.setFixedWidth(120)
        pid2_grid.addWidget(self.pid2_kd_tb, 3, 2)

        self.pid2_kp_btn = QtWidgets.QPushButton('Set')
        self.pid2_kp_btn.setFixedWidth(80)
        self.pid2_kp_btn.setEnabled(False)
        self.pid2_kp_btn.clicked.connect(self.send_pid2_kp)
        pid2_grid.addWidget(self.pid2_kp_btn, 1, 3)

        self.pid2_ki_btn = QtWidgets.QPushButton('Set')
        self.pid2_ki_btn.setFixedWidth(80)
        self.pid2_ki_btn.setEnabled(False)
        self.pid2_ki_btn.clicked.connect(self.send_pid2_ki)
        #pid2_grid.addWidget(self.pid2_ki_btn, 2, 3)

        self.pid2_kd_btn = QtWidgets.QPushButton('Set')
        self.pid2_kd_btn.setFixedWidth(80)
        self.pid2_kd_btn.setEnabled(False)
        self.pid2_kd_btn.clicked.connect(self.send_pid2_kd)
        pid2_grid.addWidget(self.pid2_kd_btn, 3, 3)
        # --------------------------------------------------------------------------------------------------------------
        # endregion PID2 Grid

        pid3_label = QtWidgets.QLabel('Pitch outer PID')
        pid3_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        pid3_label.setContentsMargins(0, 10, 0, 0)
        scrollContent.addWidget(pid3_label)

        pid3_grid = QtWidgets.QGridLayout()
        scrollContent.addLayout(pid3_grid)

        # region PID3 Grid
        # --------------------------------------------------------------------------------------------------------------
        pid3_kp_label = QtWidgets.QLabel('Kp')
        pid3_kp_label.setFixedWidth(20)
        pid3_kp_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid3_grid.addWidget(pid3_kp_label, 1, 1)

        pid3_ki_label = QtWidgets.QLabel('Ki')
        pid3_ki_label.setFixedWidth(20)
        pid3_ki_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid3_grid.addWidget(pid3_ki_label, 2, 1)

        pid3_kd_label = QtWidgets.QLabel('Kd')
        pid3_kd_label.setFixedWidth(20)
        pid3_kd_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid3_grid.addWidget(pid3_kd_label, 3, 1)

        self.pid3_kp_tb = QtWidgets.QLineEdit()
        self.pid3_kp_tb.setFixedWidth(120)
        pid3_grid.addWidget(self.pid3_kp_tb, 1, 2)

        self.pid3_ki_tb = QtWidgets.QLineEdit()
        self.pid3_ki_tb.setFixedWidth(120)
        pid3_grid.addWidget(self.pid3_ki_tb, 2, 2)

        self.pid3_kd_tb = QtWidgets.QLineEdit()
        self.pid3_kd_tb.setFixedWidth(120)
        pid3_grid.addWidget(self.pid3_kd_tb, 3, 2)

        self.pid3_kp_btn = QtWidgets.QPushButton('Set')
        self.pid3_kp_btn.setFixedWidth(80)
        self.pid3_kp_btn.setEnabled(False)
        self.pid3_kp_btn.clicked.connect(self.send_pid3_kp)
        pid3_grid.addWidget(self.pid3_kp_btn, 1, 3)

        self.pid3_ki_btn = QtWidgets.QPushButton('Set')
        self.pid3_ki_btn.setFixedWidth(80)
        self.pid3_ki_btn.setEnabled(False)
        self.pid3_ki_btn.clicked.connect(self.send_pid3_ki)
        pid3_grid.addWidget(self.pid3_ki_btn, 2, 3)

        self.pid3_kd_btn = QtWidgets.QPushButton('Set')
        self.pid3_kd_btn.setFixedWidth(80)
        self.pid3_kd_btn.setEnabled(False)
        self.pid3_kd_btn.clicked.connect(self.send_pid3_kd)
        pid3_grid.addWidget(self.pid3_kd_btn, 3, 3)
        # --------------------------------------------------------------------------------------------------------------
        # endregion PID3 Grid

        pid4_label = QtWidgets.QLabel('Pitch inner PID')
        pid4_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        pid4_label.setContentsMargins(0, 10, 0, 0)
        scrollContent.addWidget(pid4_label)

        pid4_grid = QtWidgets.QGridLayout()
        scrollContent.addLayout(pid4_grid)

        # region PID4 Grid
        # --------------------------------------------------------------------------------------------------------------
        pid4_kp_label = QtWidgets.QLabel('Kp')
        pid4_kp_label.setFixedWidth(20)
        pid4_kp_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid4_grid.addWidget(pid4_kp_label, 1, 1)

        pid4_ki_label = QtWidgets.QLabel('Ki')
        pid4_ki_label.setFixedWidth(20)
        pid4_ki_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        #pid4_grid.addWidget(pid4_ki_label, 2, 1)

        pid4_kd_label = QtWidgets.QLabel('Kd')
        pid4_kd_label.setFixedWidth(20)
        pid4_kd_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid4_grid.addWidget(pid4_kd_label, 3, 1)

        self.pid4_kp_tb = QtWidgets.QLineEdit()
        self.pid4_kp_tb.setFixedWidth(120)
        pid4_grid.addWidget(self.pid4_kp_tb, 1, 2)

        self.pid4_ki_tb = QtWidgets.QLineEdit()
        self.pid4_ki_tb.setFixedWidth(120)
        #pid4_grid.addWidget(self.pid4_ki_tb, 2, 2)

        self.pid4_kd_tb = QtWidgets.QLineEdit()
        self.pid4_kd_tb.setFixedWidth(120)
        pid4_grid.addWidget(self.pid4_kd_tb, 3, 2)

        self.pid4_kp_btn = QtWidgets.QPushButton('Set')
        self.pid4_kp_btn.setFixedWidth(80)
        self.pid4_kp_btn.setEnabled(False)
        self.pid4_kp_btn.clicked.connect(self.send_pid4_kp)
        pid4_grid.addWidget(self.pid4_kp_btn, 1, 3)

        self.pid4_ki_btn = QtWidgets.QPushButton('Set')
        self.pid4_ki_btn.setFixedWidth(80)
        self.pid4_ki_btn.setEnabled(False)
        self.pid4_ki_btn.clicked.connect(self.send_pid4_ki)
        #pid4_grid.addWidget(self.pid4_ki_btn, 2, 3)

        self.pid4_kd_btn = QtWidgets.QPushButton('Set')
        self.pid4_kd_btn.setFixedWidth(80)
        self.pid4_kd_btn.setEnabled(False)
        self.pid4_kd_btn.clicked.connect(self.send_pid4_kd)
        pid4_grid.addWidget(self.pid4_kd_btn, 3, 3)
        # --------------------------------------------------------------------------------------------------------------
        # endregion PID4 Grid

        pid5_label = QtWidgets.QLabel('Yaw PID')
        pid5_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        pid5_label.setContentsMargins(0, 10, 0, 0)
        scrollContent.addWidget(pid5_label)

        pid5_grid = QtWidgets.QGridLayout()
        scrollContent.addLayout(pid5_grid)

        # region PID5 Grid
        # --------------------------------------------------------------------------------------------------------------
        pid5_kp_label = QtWidgets.QLabel('Kp')
        pid5_kp_label.setFixedWidth(20)
        pid5_kp_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid5_grid.addWidget(pid5_kp_label, 1, 1)

        pid5_ki_label = QtWidgets.QLabel('Ki')
        pid5_ki_label.setFixedWidth(20)
        pid5_ki_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid5_grid.addWidget(pid5_ki_label, 2, 1)

        pid5_kd_label = QtWidgets.QLabel('Kd')
        pid5_kd_label.setFixedWidth(20)
        pid5_kd_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid5_grid.addWidget(pid5_kd_label, 3, 1)

        self.pid5_kp_tb = QtWidgets.QLineEdit()
        self.pid5_kp_tb.setFixedWidth(120)
        pid5_grid.addWidget(self.pid5_kp_tb, 1, 2)

        self.pid5_ki_tb = QtWidgets.QLineEdit()
        self.pid5_ki_tb.setFixedWidth(120)
        pid5_grid.addWidget(self.pid5_ki_tb, 2, 2)

        self.pid5_kd_tb = QtWidgets.QLineEdit()
        self.pid5_kd_tb.setFixedWidth(120)
        pid5_grid.addWidget(self.pid5_kd_tb, 3, 2)

        self.pid5_kp_btn = QtWidgets.QPushButton('Set')
        self.pid5_kp_btn.setFixedWidth(80)
        self.pid5_kp_btn.setEnabled(False)
        self.pid5_kp_btn.clicked.connect(self.send_pid5_kp)
        pid5_grid.addWidget(self.pid5_kp_btn, 1, 3)

        self.pid5_ki_btn = QtWidgets.QPushButton('Set')
        self.pid5_ki_btn.setFixedWidth(80)
        self.pid5_ki_btn.setEnabled(False)
        self.pid5_ki_btn.clicked.connect(self.send_pid5_ki)
        pid5_grid.addWidget(self.pid5_ki_btn, 2, 3)

        self.pid5_kd_btn = QtWidgets.QPushButton('Set')
        self.pid5_kd_btn.setFixedWidth(80)
        self.pid5_kd_btn.setEnabled(False)
        self.pid5_kd_btn.clicked.connect(self.send_pid5_kd)
        pid5_grid.addWidget(self.pid5_kd_btn, 3, 3)
        # --------------------------------------------------------------------------------------------------------------
        # endregion PID5 Grid

        pid6_label = QtWidgets.QLabel('Throttle PID')
        pid6_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        pid6_label.setContentsMargins(0, 10, 0, 0)
        scrollContent.addWidget(pid6_label)

        pid6_grid = QtWidgets.QGridLayout()
        scrollContent.addLayout(pid6_grid)

        # region PID6 Grid
        # --------------------------------------------------------------------------------------------------------------
        pid6_kp_label = QtWidgets.QLabel('Kp')
        pid6_kp_label.setFixedWidth(20)
        pid6_kp_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid6_grid.addWidget(pid6_kp_label, 1, 1)

        pid6_ki_label = QtWidgets.QLabel('Ki')
        pid6_ki_label.setFixedWidth(20)
        pid6_ki_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid6_grid.addWidget(pid6_ki_label, 2, 1)

        pid6_kd_label = QtWidgets.QLabel('Kd')
        pid6_kd_label.setFixedWidth(20)
        pid6_kd_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pid6_grid.addWidget(pid6_kd_label, 3, 1)

        self.pid6_kp_tb = QtWidgets.QLineEdit()
        self.pid6_kp_tb.setFixedWidth(120)
        pid6_grid.addWidget(self.pid6_kp_tb, 1, 2)

        self.pid6_ki_tb = QtWidgets.QLineEdit()
        self.pid6_ki_tb.setFixedWidth(120)
        pid6_grid.addWidget(self.pid6_ki_tb, 2, 2)

        self.pid6_kd_tb = QtWidgets.QLineEdit()
        self.pid6_kd_tb.setFixedWidth(120)
        pid6_grid.addWidget(self.pid6_kd_tb, 3, 2)

        self.pid6_kp_btn = QtWidgets.QPushButton('Set')
        self.pid6_kp_btn.setFixedWidth(80)
        self.pid6_kp_btn.setEnabled(False)
        self.pid6_kp_btn.clicked.connect(self.send_pid6_kp)
        pid6_grid.addWidget(self.pid6_kp_btn, 1, 3)

        self.pid6_ki_btn = QtWidgets.QPushButton('Set')
        self.pid6_ki_btn.setFixedWidth(80)
        self.pid6_ki_btn.setEnabled(False)
        self.pid6_ki_btn.clicked.connect(self.send_pid6_ki)
        pid6_grid.addWidget(self.pid6_ki_btn, 2, 3)

        self.pid6_kd_btn = QtWidgets.QPushButton('Set')
        self.pid6_kd_btn.setFixedWidth(80)
        self.pid6_kd_btn.setEnabled(False)
        self.pid6_kd_btn.clicked.connect(self.send_pid6_kd)
        pid6_grid.addWidget(self.pid6_kd_btn, 3, 3)
        # --------------------------------------------------------------------------------------------------------------
        # endregion PID6 Grid

        self.set_buttons = [self.pid1_kp_btn, self.pid1_ki_btn, self.pid1_kd_btn,
                            self.pid2_kp_btn, self.pid2_ki_btn, self.pid2_kd_btn,
                            self.pid3_kp_btn, self.pid3_ki_btn, self.pid3_kd_btn,
                            self.pid4_kp_btn, self.pid4_ki_btn, self.pid4_kd_btn,
                            self.pid5_kp_btn, self.pid5_ki_btn, self.pid5_kd_btn,
                            self.pid6_kp_btn, self.pid6_ki_btn, self.pid6_kd_btn]

        self.set_textboxes = [self.pid1_kp_tb, self.pid1_ki_tb, self.pid1_kd_tb,
                              self.pid2_kp_tb, self.pid2_ki_tb, self.pid2_kd_tb,
                              self.pid3_kp_tb, self.pid3_ki_tb, self.pid3_kd_tb,
                              self.pid4_kp_tb, self.pid4_ki_tb, self.pid4_kd_tb,
                              self.pid5_kp_tb, self.pid5_ki_tb, self.pid5_kd_tb,
                              self.pid6_kp_tb, self.pid6_ki_tb, self.pid6_kd_tb]

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # endregion Left

        # region Right
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        # Create Figure 1 for PID1 / PID3
        self.fig1 = Figure()
        self.canvas1 = FigureCanvas(self.fig1)

        if not pid2_fft:
            self.ax1 = self.fig1.add_subplot(2, 1, 1)
            self.ax2 = self.fig1.add_subplot(2, 1, 2)
        else:
            self.ax1 = self.fig1.add_subplot(5, 5, 13)
            self.ax2 = self.fig1.add_subplot(1, 1, 1)

        right_layout.addWidget(self.canvas1)

        # Create Figure 2 for PID2 / PID4 / PID5
        self.fig2 = Figure()
        self.canvas2 = FigureCanvas(self.fig2)

        self.ax3 = self.fig2.add_subplot(2, 1, 1)
        self.ax4 = self.fig2.add_subplot(2, 1, 2)

        right_layout.addWidget(self.canvas2)
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # endregion Right

    def start_plotting(self):
        serial_connection.ser = serial_connection.initialize_serial(com_port, baud_rate)
        if serial_connection.ser is not None:
            plt.ion()  # Turn on interactive mode for real-time plotting
            if self.plot_thread is None or not self.plot_thread.isRunning():
                self.plot_thread = QtCore.QThread()
                self.plotter = RealTimePlotWorker(buffers,
                                                  self.ax1, self.ax2, self.ax3, self.ax4,
                                                  self.fig1, self.fig2,
                                                  self.throttle_label, self.pid_all_label,
                                                  self.radio_buttons)

                self.plotter.moveToThread(self.plot_thread)
                self.plot_thread.started.connect(self.plotter.plot)
                self.rollRadioButton.toggled.connect(self.plotter.onPlotChange)
                self.pitchRadioButton.toggled.connect(self.plotter.onPlotChange)
                self.plotter.finished.connect(self.stop_plot_thread)
            self.plot_thread.start()

            self.startButton.setEnabled(False)
            self.stopButton.setEnabled(True)
            self.refreshButton.setEnabled(True)

            for btn in self.set_buttons:
                btn.setEnabled(True)
        else:
            print("Failed to initialize the serial connection.")

    def stop_plotting(self):
        if hasattr(self, 'plot_thread') and hasattr(self, 'plotter'):
            self.plotter.running = False

            self.stopButton.setEnabled(False)
            self.refreshButton.setEnabled(False)
            self.startButton.setEnabled(True)

            for btn in self.set_buttons:
                btn.setEnabled(False)

    def stop_plot_thread(self):
        if self.plot_thread and self.plot_thread.isRunning():
            self.plot_thread.terminate()

            # In order to redraw the whole line after restarting the plot
            #pid1_ref_data.clear()
            #pid1_meas_data.clear()
            #pid1_out_data.clear()
            #pid2_ref_data.clear()
            #pid2_meas_data.clear()
            #pid2_out_data.clear()

            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.ax4.clear()

            serial_connection.ser.close()

    def refresh_gains(self):
        if serial_connection.ser is not None:
            for tb, gain in zip(self.set_textboxes, stored_gains):
                tb.setText(str(gain))

    def wrong_number_format_popup(self):
        # Create a QMessageBox
        messageBox = QMessageBox()
        messageBox.setWindowTitle('Error')
        messageBox.setText(f"Wrong number format!")
        messageBox.setIcon(QMessageBox.Critical)  # You can set different icons (Information, Warning, Critical, etc.)
        messageBox.setStandardButtons(
            QMessageBox.Ok)  # You can set different standard buttons (Ok, Cancel, Yes, No, etc.)

        # Execute the message box and wait for user response
        result = messageBox.exec_()

        if result == QMessageBox.Ok:
            print('OK button clicked')

        return None

    def send_gain(self, string, gain_storage, tb):
        if serial_connection.ser is not None:
            try:
                gain_storage = float(tb.text().replace(',', '.'))
                string_to_send = string + ': ' + str(gain_storage) + '\r\n'
                serial_connection.ser.write(string_to_send.encode())
            except Exception as e:
                self.wrong_number_format_popup()

    def send_pid1_kp(self):
        self.send_gain('PID1_Kp', stored_gains[0], self.set_textboxes[0])

    def send_pid1_ki(self):
        self.send_gain('PID1_Ki', stored_gains[1], self.set_textboxes[1])

    def send_pid1_kd(self):
        self.send_gain('PID1_Kd', stored_gains[2], self.set_textboxes[2])

    def send_pid2_kp(self):
        self.send_gain('PID2_Kp', stored_gains[3], self.set_textboxes[3])

    def send_pid2_ki(self):
        self.send_gain('PID2_Ki', stored_gains[4], self.set_textboxes[4])

    def send_pid2_kd(self):
        self.send_gain('PID2_Kd', stored_gains[5], self.set_textboxes[5])

    def send_pid3_kp(self):
        self.send_gain('PID3_Kp', stored_gains[6], self.set_textboxes[6])

    def send_pid3_ki(self):
        self.send_gain('PID3_Ki', stored_gains[7], self.set_textboxes[7])

    def send_pid3_kd(self):
        self.send_gain('PID3_Kd', stored_gains[8], self.set_textboxes[8])

    def send_pid4_kp(self):
        self.send_gain('PID4_Kp', stored_gains[9], self.set_textboxes[9])

    def send_pid4_ki(self):
        self.send_gain('PID4_Ki', stored_gains[10], self.set_textboxes[10])

    def send_pid4_kd(self):
        self.send_gain('PID4_Kd', stored_gains[11], self.set_textboxes[11])

    def send_pid5_kp(self):
        self.send_gain('PID5_Kp', stored_gains[12], self.set_textboxes[12])

    def send_pid5_ki(self):
        self.send_gain('PID5_Ki', stored_gains[13], self.set_textboxes[13])

    def send_pid5_kd(self):
        self.send_gain('PID5_Kd', stored_gains[14], self.set_textboxes[14])

    def send_pid6_kp(self):
        self.send_gain('PID6_Kp', stored_gains[15], self.set_textboxes[15])

    def send_pid6_ki(self):
        self.send_gain('PID6_Ki', stored_gains[16], self.set_textboxes[16])

    def send_pid6_kd(self):
        self.send_gain('PID6_Kd', stored_gains[17], self.set_textboxes[17])

    def onTuneModeChange(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            if serial_connection.ser is not None:
                try:
                    string = 'Tune Mode: ' + str(radioButton.text) + '\r\n'
                    serial_connection.ser.write(string.encode())
                except Exception:
                    print('Tune Mode change error')
