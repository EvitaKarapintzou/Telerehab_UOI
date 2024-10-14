import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import multiprocessing
import time
import numpy as np
from datetime import datetime as dt

import data_export as data_export
from connect_to_mat import request_new_map, connect_to_device
from detect_available_mats import get_mats_information
import configuration

# Configuration
config = configuration.config
rows = config['ROWS']
cols = config['COLS']

connected_mats = get_mats_information()

# Initialize the multiprocessing queue
data_queue = multiprocessing.Queue()

# Function to request and receive a new pressure map
def request_pressure_map(ser):
    if ser.in_waiting > 0:
        try:
            xbyte = ser.read().decode('utf-8')
        except Exception:
            print("Exception")
        if xbyte == 'N':
            active_points_receive_map(ser)
        else:
            ser.flush()

# Function to handle the incoming data points
def active_points_receive_map(ser):
    global values
    matrix = np.zeros((rows, cols), dtype=int)

    HighByte = ser.read()
    LowByte = ser.read()
    high = int.from_bytes(HighByte, 'big')
    low = int.from_bytes(LowByte, 'big')
    nPoints = ((high << 8) | low)

    ser.read()  # Skip 2 bytes
    ser.read()
    
    for _ in range(nPoints):
        x = int.from_bytes(ser.read(), 'big')
        y = int.from_bytes(ser.read(), 'big')
        HighByte = ser.read()
        LowByte = ser.read()
        high = int.from_bytes(HighByte, 'big')
        low = int.from_bytes(LowByte, 'big')
        val = ((high << 8) | low)
        matrix[y][x] = val if val >= 33 else 0
    
    values = np.fliplr(matrix)
    return values

# Function to create a new device map
def create_new_device_map(mat, ser):
    device_port = mat['port']
    serial_number = mat['serial']
    timepoint = dt.now().isoformat()
    
    request_pressure_map(ser)

    collected_data = values.tolist()
    
    new_map = {"dateTime": timepoint,
               "device_port": device_port,
               "serial_number": serial_number,
               "sensors": collected_data}
    
    return new_map

# Function to get a single mat's pressure sum and put the data in the queue
def get_sinlge_mat_pressure_sum(mat, queue):
    ser = connect_to_device(mat)
    request_new_map(ser)
    time.sleep(0.03)
    device_map = create_new_device_map(mat, ser)
    sensors_values = device_map['sensors']

    # Push the 48x48 matrix into the queue
    queue.put(sensors_values)

    row_sum = [sum(row) for row in sensors_values]
    map_sum = sum(row_sum)

    return map_sum

# Function to handle multiple mats and continuously collect data
def get_mat_pressures(queue):
    stopwatch = time.time() + 1

    while time.time() < stopwatch:
        for mat in connected_mats:
            get_sinlge_mat_pressure_sum(mat, queue)
        time.sleep(0.5)  # Adjust sleep time to control data collection rate

    print(f"RECORDS COLLECTED: {len(current_map)}")

    data_export.export_to_json(current_map)  # Export collected data to JSON

from PyQt5 import QtWidgets
import pyqtgraph as pg

class RandomDataApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Random 48x48 Data Visualization')

        # Create the main widget
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        
        # Create a layout
        layout = QtWidgets.QVBoxLayout(self.main_widget)

        # Create the image view widget for displaying the heatmap
        self.image_view = pg.ImageView()
        layout.addWidget(self.image_view)

        # Set up a timer to refresh the display
        self.timer = pg.QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_heatmap)
        self.timer.start(100)  # Update every 100 milliseconds (0.1 seconds)

        self.show()

    def update_heatmap(self):
        # Generate random 48x48 data
        z_data = np.random.rand(48, 48)

        # Update the image view with the new data
        self.image_view.setImage(z_data.T, autoLevels=True)

if __name__ == '__main__':
    # Start the data collection process
    data_process = multiprocessing.Process(target=get_mat_pressures, args=(data_queue,))
    data_process.start()

    # Create the PyQt application
    app = QtWidgets.QApplication(sys.argv)
    ex = PressureMapApp(data_queue)
    sys.exit(app.exec_())
    
    # Wait for the data collection process to finish (if needed)
    data_process.join()
