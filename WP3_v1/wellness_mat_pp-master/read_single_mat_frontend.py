import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import multiprocessing
import time
import numpy as np
from datetime import datetime as dt
import sys
import data_export as data_export
from connect_to_mat import request_new_map, connect_to_device
from detect_available_mats import get_mats_information
import configuration
from pyqtgraph import ColorMap


# Configuration
config = configuration.config
rows = config['ROWS']
cols = config['COLS']

connected_mats = get_mats_information()
values = np.zeros((rows, cols), dtype=int)


z_data_last = np.zeros((rows, cols));

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

  xbyte = ser.read().decode('utf-8')

  HighByte = ser.read()
  LowByte = ser.read()
  high = int.from_bytes(HighByte, 'big')
  low = int.from_bytes(LowByte, 'big')
  nPoints = ((high << 8) | low)

  xbyte = ser.read().decode('utf-8')
  xbyte = ser.read().decode('utf-8')
  x = 0
  y = 0
  n = 0
  while(n < nPoints):
    x = ser.read()
    y = ser.read()
    x = int.from_bytes(x, 'big')
    y = int.from_bytes(y, 'big')
    HighByte = ser.read()
    LowByte = ser.read()
    high = int.from_bytes(HighByte, 'big')
    low = int.from_bytes(LowByte, 'big')
    val = ((high << 8) | low)
    matrix[y][x] = val if val >= 33 else 0
    n += 1
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
    time.sleep(0.1)
    device_map = create_new_device_map(mat, ser)
    sensors_values = device_map['sensors']
    print(sensors_values)

    # Push the 48x48 matrix into the queue
    queue.put(sensors_values)

    row_sum = [sum(row) for row in sensors_values]
    map_sum = sum(row_sum)

    return map_sum

# Function to handle multiple mats and continuously collect data
def get_mat_pressures(queue):
    stopwatch = time.time() + 1

    while True:
        for mat in connected_mats:
            get_sinlge_mat_pressure_sum(mat, queue)
        time.sleep(0.2)  # Adjust sleep time to control data collection rate


from PyQt5 import QtWidgets
import pyqtgraph as pg

class PressureMapApp(QtWidgets.QMainWindow):
    z_data_last = np.zeros((rows, cols));

    def __init__(self, data_queue):
        super().__init__()
        self.initUI()
        

    def initUI(self):
        self.setWindowTitle('48x48 Data Visualization')
        # Create the main widget
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        
        # Create a layout
        layout = QtWidgets.QVBoxLayout(self.main_widget)

        # Create the image view widget for displaying the heatmap
        self.image_view = pg.ImageView()
        layout.addWidget(self.image_view)

        # Create a colorful colormap
        colors = [
            (0, 0, 255),  # Blue
            (0, 255, 255),  # Cyan
            (0, 255, 0),  # Green
            (255, 255, 0),  # Yellow
            (255, 0, 0),  # Red
        ]
        cmap = ColorMap(pos=np.linspace(0.0, 1.0, len(colors)), color=colors)
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        # Set the colormap to the ImageView
        self.image_view.setColorMap(cmap)

        # Set up a timer to refresh the display
        self.timer = pg.QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_heatmap)
        self.timer.start(100)  # Update every 100 milliseconds (0.1 seconds)

        self.show()

    def update_heatmap(self):
        # Generate random 48x48 data
        #z_data = np.random.rand(48, 48)
        try:
            z_data = data_queue.get_nowait()  # Non-blocking get
            z_data_last = z_data;
        except:
            z_data = z_data_last


        # Update the image view with the new data
        z_data = np.array(z_data)

        self.image_view.setImage(z_data, autoLevels=True)

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
