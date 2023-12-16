import serial
from PyQt5.QtWidgets import QMessageBox

ser = None

# Create a function to initialize the serial connection
def initialize_serial(port, baudrate):
    global ser

    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=5)
        return ser
    except Exception as e:
        # Create a QMessageBox
        messageBox = QMessageBox()
        messageBox.setWindowTitle('Error')
        messageBox.setText(f"Failed to connect to {port} at {baudrate} baud: {e}")
        messageBox.setIcon(QMessageBox.Critical)  # You can set different icons (Information, Warning, Critical, etc.)
        messageBox.setStandardButtons(QMessageBox.Ok)  # You can set different standard buttons (Ok, Cancel, Yes, No, etc.)

        # Execute the message box and wait for user response
        result = messageBox.exec_()

        if result == QMessageBox.Ok:
            print('OK button clicked')

        return None