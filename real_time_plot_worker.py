import time
import matplotlib
import numpy as np
import serial
from PyQt5 import QtWidgets, QtCore
import serial_connection
from PID_data import PID_data
import re
import real_time_plot_app
from collections import deque

matplotlib.use('Qt5Agg')

data = PID_data()
stored_gains = data.stored_gains
stored_plot_data = data.stored_plot_data

# Define a fixed update interval (in seconds)
update_interval = 0.005  # Set this to the desired interval
last_update_time = 0.0


# Store read gain value in the storage and set label
def store_gain(message, label, position):
    value = message.split(": ")[1]
    value = float(value)
    parts = re.split('\s+ |\n', label.text())
    parts[position] = str(value)
    text = ('  '.join(parts[0:4]) + '\n'
            + '  '.join(parts[4:8]) + '\n'
            + '  '.join(parts[8:12]) + '\n'
            + '  '.join(parts[12:16]) + '\n'
            + '  '.join(parts[16:20]) + '\n'
            + '  '.join(parts[20:24]))
    label.setText(text)

    return value


# Store read plot data value in the storage and set buffer
def store_plot_data(message, min, max, buffer):
    value = message.split(": ")[1]
    value = float(value)
    if min <= value <= max:
        buffer.append(value)

    return value


# Create a real-time plot for all attributes
def plot_realtime(worker,
                  buffers,
                  ax1, ax2, ax3, ax4,
                  figure1, figure2,
                  throttle_label, pid_all_label,
                  radio_buttons):
    global last_update_time
    global data

    if radio_buttons[0].isChecked():
        pid1_ref_line, = ax1.plot([], color='b', label='PID_Ro_ref')
        pid1_meas_line, = ax1.plot([], color='g', label='PID_Ro_meas')

        if not real_time_plot_app.pid2_fft:
            pid1_out_line, = ax2.plot([], color='r', label='PID_Ro_out')
        else:
            pid2_meas_FFT_line, = ax2.plot([], color='r', label='PID_Ri_meas_FFT')

        pid2_ref_line, = ax3.plot([], color='b', label='PID_Ri_ref')
        pid2_meas_line, = ax3.plot([], color='g', label='PID_Ri_meas')
        pid2_out_line, = ax4.plot([], color='r', label='PID_Ri_out')

        if not real_time_plot_app.pid2_fft:
            lines = [pid1_ref_line, pid1_meas_line, pid1_out_line, pid2_ref_line, pid2_meas_line, pid2_out_line]
        else:
            lines = [pid1_ref_line, pid1_meas_line, pid2_meas_FFT_line, pid2_ref_line, pid2_meas_line, pid2_out_line]
    elif radio_buttons[1].isChecked():
        pid3_ref_line, = ax1.plot([], color='b', label='PID_Po_ref')
        pid3_meas_line, = ax1.plot([], color='g', label='PID_Po_meas')
        pid3_out_line, = ax2.plot([], color='r', label='PID_Po_out')
        pid4_ref_line, = ax3.plot([], color='b', label='PID_Pi_ref')
        pid4_meas_line, = ax3.plot([], color='g', label='PID_Pi_meas')
        pid4_out_line, = ax4.plot([], color='r', label='PID_Pi_out')
        lines = [pid3_ref_line, pid3_meas_line, pid3_out_line, pid4_ref_line, pid4_meas_line, pid4_out_line]
    elif radio_buttons[2].isChecked():
        pid5_ref_line, = ax3.plot([], color='b', label='PID_Y_ref')
        pid5_meas_line, = ax3.plot([], color='g', label='PID_Y_meas')
        pid5_out_line, = ax4.plot([], color='r', label='PID_Y_out')
        lines = [None, None, None, pid5_ref_line, pid5_meas_line, pid5_out_line]
    elif radio_buttons[3].isChecked():
        pid6_ref_line, = ax3.plot([], color='b', label='PID_T_ref')
        pid6_meas_line, = ax3.plot([], color='g', label='PID_T_meas')
        pid6_out_line, = ax4.plot([], color='r', label='PID_T_out')
        lines = [None, None, None, pid6_ref_line, pid6_meas_line, pid6_out_line]

    ax1.set_ylim(-50 - 5, 50 + 5)

    if not real_time_plot_app.pid2_fft:
        ax2.set_ylim(-50 - 5, 50 + 5)
    else:
        ax2.set_ylim(-2500 - 100, 2500 + 100)

    ax3.set_ylim(-50 - 5, 50 + 5)
    ax4.set_ylim(-500 - 50, 500 + 50)

    ax1.legend(loc='lower left')
    ax2.legend(loc='lower left')
    ax3.legend(loc='lower left')
    ax4.legend(loc='lower left')

    x = np.arange(real_time_plot_app.buflen)
    freq = np.fft.rfftfreq(real_time_plot_app.buflen)
    freq_Hz = freq * (1 / update_interval)

    while worker.running:
        QtWidgets.QApplication.processEvents()  # Allow the GUI to update

        try:
            message = serial_connection.ser.readline().decode('utf-8')
            # if not message:
            #     worker.running = False

            # region Store messages
            if "Throttle" in message:
                values = message.split(" ")
                data.Throttle = (69, values[2], values[3], values[4], values[5])
                values[1] = (values[1])[1:-1]
                values[5] = (values[5])[0:-2]
                throttle_label.setText(f'Throttle:  {values[1]}\n{values[2]}  {values[3]}  {values[4]}  {values[5]}')

            elif "PID_Ro_Kp" in message:
                stored_gains[0] = store_gain(message, pid_all_label, 1)

            elif "PID_Ro_Ki" in message:
                stored_gains[1] = store_gain(message, pid_all_label, 2)

            elif "PID_Ro_Kd" in message:
                stored_gains[2] = store_gain(message, pid_all_label, 3)

            elif "PID_Ro_ref" in message:
                stored_plot_data[0] = store_plot_data(message, -500, 500, buffers[0])

            elif "PID_Ro_meas" in message:
                stored_plot_data[1] = store_plot_data(message, -500, 500, buffers[1])

            elif "PID_Ro_out" in message:
                stored_plot_data[2] = store_plot_data(message, -50, 50, buffers[2])

            elif "PID_Ri_Kp" in message:
                stored_gains[3] = store_gain(message, pid_all_label, 5)

            elif "PID_Ri_Ki" in message:
                stored_gains[4] = store_gain(message, pid_all_label, 6)

            elif "PID_Ri_Kd" in message:
                stored_gains[5] = store_gain(message, pid_all_label, 7)

            elif "PID_Ri_ref" in message:
                stored_plot_data[3] = store_plot_data(message, -50, 50, buffers[3])

            elif "PID_Ri_meas" in message:
                stored_plot_data[4] = store_plot_data(message, -50, 50, buffers[4])

                if -50 <= stored_plot_data[4] <= 50:
                    # Compute FFT
                    if real_time_plot_app.pid2_fft:
                        fft_data = np.fft.rfft(buffers[4]).real
                        buffers[15].extend(fft_data)

            elif "PID_Ri_out" in message:
                stored_plot_data[5] = store_plot_data(message, -500, 500, buffers[5])

            elif "PID_Po_Kp" in message:
                stored_gains[6] = store_gain(message, pid_all_label, 9)

            elif "PID_Po_Ki" in message:
                stored_gains[7] = store_gain(message, pid_all_label, 10)

            elif "PID_Po_Kd" in message:
                stored_gains[8] = store_gain(message, pid_all_label, 11)

            elif "PID_Po_ref" in message:
                stored_plot_data[6] = store_plot_data(message, -500, 500, buffers[6])

            elif "PID_Po_meas" in message:
                stored_plot_data[7] = store_plot_data(message, -500, 500, buffers[7])

            elif "PID_Po_out" in message:
                stored_plot_data[8] = store_plot_data(message, -50, 50, buffers[8])

            elif "PID_Pi_Kp" in message:
                stored_gains[9] = store_gain(message, pid_all_label, 13)

            elif "PID_Pi_Ki" in message:
                stored_gains[10] = store_gain(message, pid_all_label, 14)

            elif "PID_Pi_Kd" in message:
                stored_gains[11] = store_gain(message, pid_all_label, 15)

            elif "PID_Pi_ref" in message:
                stored_plot_data[9] = store_plot_data(message, -50, 50, buffers[9])

            elif "PID_Pi_meas" in message:
                stored_plot_data[10] = store_plot_data(message, -50, 50, buffers[10])

            elif "PID_Pi_out" in message:
                stored_plot_data[11] = store_plot_data(message, -500, 500, buffers[11])

            elif "PID_Y_Kp" in message:
                stored_gains[12] = store_gain(message, pid_all_label, 17)

            elif "PID_Y_Ki" in message:
                stored_gains[13] = store_gain(message, pid_all_label, 18)

            elif "PID_Y_Kd" in message:
                stored_gains[14] = store_gain(message, pid_all_label, 19)

            elif "PID_Y_ref" in message:
                stored_plot_data[12] = store_plot_data(message, -50, 50, buffers[12])

            elif "PID_Y_meas" in message:
                stored_plot_data[13] = store_plot_data(message, -50, 50, buffers[13])

            elif "PID_Y_out" in message:
                stored_plot_data[14] = store_plot_data(message, -500, 500, buffers[14])

            elif "PID_T_Kp" in message:
                stored_gains[15] = store_gain(message, pid_all_label, 21)

            elif "PID_T_Ki" in message:
                stored_gains[16] = store_gain(message, pid_all_label, 22)

            elif "PID_T_Kd" in message:
                stored_gains[17] = store_gain(message, pid_all_label, 23)

            elif "PID_T_ref" in message:
                stored_plot_data[15] = store_plot_data(message, 0, 1500, buffers[15])

            elif "PID_T_meas" in message:
                stored_plot_data[16] = store_plot_data(message, 0, 1500, buffers[16])

            elif "PID_T_out" in message:
                stored_plot_data[17] = store_plot_data(message, 0, 1000, buffers[17])

            # endregion Store messages

            # Only update the plot every update_interval seconds
            if time.time() - last_update_time >= update_interval:
                if worker.plotChanged:
                    for line in lines:
                        line.remove()

                    if radio_buttons[0].isChecked():
                        lines[0], = ax1.plot([], color='b', label='PID_Ro_ref')
                        lines[1], = ax1.plot([], color='g', label='PID_Ro_meas')

                        if not real_time_plot_app.pid2_fft:
                            lines[2], = ax2.plot([], color='r', label='PID_Ro_out')
                        else:
                            lines[2], = ax2.plot([], color='r', label='PID_Ri_meas_FFT')

                        lines[3], = ax3.plot([], color='b', label='PID_Ri_ref')
                        lines[4], = ax3.plot([], color='g', label='PID_Ri_meas')
                        lines[5], = ax4.plot([], color='r', label='PID_Ri_out')
                    elif radio_buttons[1].isChecked():
                        lines[0], = ax1.plot([], color='b', label='PID_Po_ref')
                        lines[1], = ax1.plot([], color='g', label='PID_Po_meas')
                        lines[2], = ax2.plot([], color='r', label='PID_Po_out')
                        lines[3], = ax3.plot([], color='b', label='PID_Pi_ref')
                        lines[4], = ax3.plot([], color='g', label='PID_Pi_meas')
                        lines[5], = ax4.plot([], color='r', label='PID_Pi_out')
                    elif radio_buttons[2].isChecked():
                        lines[0], = ax1.plot([], color='None', label='-')
                        lines[1], = ax1.plot([], color='None', label='-')
                        lines[2], = ax2.plot([], color='None', label='-')
                        lines[3], = ax3.plot([], color='b', label='PID_Y_ref')
                        lines[4], = ax3.plot([], color='g', label='PID_Y_meas')
                        lines[5], = ax4.plot([], color='r', label='PID_Y_out')
                    elif radio_buttons[3].isChecked():
                        lines[0], = ax1.plot([], color='None', label='-')
                        lines[1], = ax1.plot([], color='None', label='-')
                        lines[2], = ax2.plot([], color='None', label='-')
                        lines[3], = ax3.plot([], color='b', label='PID_T_ref')
                        lines[4], = ax3.plot([], color='g', label='PID_T_meas')
                        lines[5], = ax4.plot([], color='r', label='PID_T_out')

                    ax1.set_title('')
                    ax2.set_title('')
                    ax3.set_title('')
                    ax4.set_title('')

                    ax1.legend(loc='lower left')
                    ax2.legend(loc='lower left')
                    ax3.legend(loc='lower left')
                    ax4.legend(loc='lower left')

                    if not radio_buttons[3].isChecked():
                        ax3.set_ylim(-50 - 5, 50 + 5)
                        ax4.set_ylim(-500 - 50, 500 + 50)
                    else:
                        ax3.set_ylim(0, 1100)
                        ax4.set_ylim(0, 1100)

                    worker.plotChanged = False

                if radio_buttons[0].isChecked():
                    if not real_time_plot_app.pid2_fft:
                        for line, x, buffer in zip(lines,
                                                   [x, x, x, x, x, x],
                                                   buffers[0:6]):
                            line.set_data(x, buffer)
                        ax1.set_title('ref: ' + str(stored_plot_data[0]) + ' meas: ' + str(stored_plot_data[1]))
                        ax2.set_title(str(stored_plot_data[2]))
                        ax3.set_title('ref: ' + str(stored_plot_data[3]) + ' meas: ' + str(stored_plot_data[4]))
                        ax4.set_title(str(stored_plot_data[5]))

                    else:
                        for line, x, buffer in zip(lines,
                                                   [x, x, freq_Hz, x, x, x],
                                                   [*buffers[0:2], buffers[18], *buffers[3:6]]):
                            line.set_data(x, buffer)

                elif radio_buttons[1].isChecked():
                    for line, x, buffer in zip(lines,
                                               [x, x, x, x, x, x],
                                               buffers[6:12]):
                        line.set_data(x, buffer)
                    ax1.set_title('ref: ' + str(stored_plot_data[6]) + ' meas: ' + str(stored_plot_data[7]))
                    ax2.set_title(str(stored_plot_data[8]))
                    ax3.set_title('ref: ' + str(stored_plot_data[9]) + ' meas: ' + str(stored_plot_data[10]))
                    ax4.set_title(str(stored_plot_data[11]))

                elif radio_buttons[2].isChecked():
                    for line, x, buffer in zip(lines,
                                               [x, x, x, x, x, x],
                                               [None, None, None, *buffers[12:15]]):
                        line.set_data(x, buffer)
                    ax3.set_title('ref: ' + str(stored_plot_data[12]) + ' meas: ' + str(stored_plot_data[13]))
                    ax4.set_title(str(stored_plot_data[14]))

                elif radio_buttons[3].isChecked():
                    for line, x, buffer in zip(lines,
                                               [x, x, x, x, x, x],
                                               [None, None, None, *buffers[15:18]]):
                        line.set_data(x, buffer)
                    ax3.set_title('ref: ' + str(stored_plot_data[15]) + ' meas: ' + str(stored_plot_data[16]))
                    ax4.set_title(str(stored_plot_data[17]))

                if radio_buttons[0].isChecked() or radio_buttons[1].isChecked():
                    ax1.relim()
                    ax1.autoscale_view()
                    ax2.relim()
                    ax2.autoscale_view()
                ax3.relim()
                ax3.autoscale_view()
                ax4.relim()
                ax4.autoscale_view()

                figure1.canvas.draw()
                figure2.canvas.draw()

            last_update_time = time.time()  # Update the last update time

        except Exception as e:
            print(e)


class RealTimePlotWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self,
                 buffers,
                 ax1, ax2, ax3, ax4,
                 figure1, figure2,
                 throttle_label, pid_all_label,
                 radio_buttons):
        super().__init__()

        self.buffers = buffers

        self.ax1 = ax1
        self.ax2 = ax2
        self.ax3 = ax3
        self.ax4 = ax4

        self.figure1 = figure1
        self.figure2 = figure2

        self.throttle_label = throttle_label
        self.pid_all_label = pid_all_label

        self.radio_buttons = radio_buttons
        self.plotChanged = False

        self.running = True

    def plot(self):
        self.running = True
        plot_realtime(self,
                      self.buffers,
                      self.ax1, self.ax2, self.ax3, self.ax4,
                      self.figure1, self.figure2,
                      self.throttle_label, self.pid_all_label,
                      self.radio_buttons)

        # After the loop, emit the signal to indicate that the worker should stop
        self.finished.emit()

    def onPlotChange(self):
        self.plotChanged = True
