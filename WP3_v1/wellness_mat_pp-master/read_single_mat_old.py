import time

import data_export as data_export
from connect_to_mat import request_new_map, connect_to_device
from detect_available_mats import get_mats_information
import configuration
import numpy as np
from datetime import datetime as dt

current_map = []

config = configuration.config

rows = config['ROWS']
cols = config['COLS']

connected_mats = get_mats_information()
  
values = np.zeros((rows, cols), dtype=int)

def request_pressure_map(ser):
  xbyte = ''
  if ser.in_waiting > 0:
    try:
      xbyte = ser.read().decode('utf-8')
    except Exception:
      print("Exception")
    if(xbyte == 'N'):
      active_points_receive_map(ser)
    else:
      ser.flush()

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
  
def create_new_device_map(mat, ser):
  device_port = mat['port']
  serial_number = mat['serial']
  timepoint = dt.now().isoformat()
  
  request_pressure_map(ser)

  collected_data = values.tolist()
  # empty_list = [] # Empty list is passed in new_map['sensors'] when I just want to check time difference between data collection

  new_map = {"dateTime": timepoint,
                 "device_port": device_port,
                 "serial_number": serial_number,
                 "sensors": collected_data
                #  "sensors": empty_list
                }
  
  return new_map

def get_sinlge_mat_pressure_sum(mat):
  ser = connect_to_device(mat)
  request_new_map(ser)
  time.sleep(0.03)
  device_map = create_new_device_map(mat, ser)
  current_map.append(device_map)
  # ser.flush()
  # ser.close()
  sensors_values = device_map['sensors']
  row_sum = [sum(row) for row in sensors_values]
  map_sum = sum(row_sum)

  # data_export.print_data_frame(current_map) # un-comment to print data frame and export to xlsx file
  
  return map_sum

def get_mat_pressures():
  # for i in range(2):
  #   if i == 0:
  #     continue

  stopwatch = time.time() + 1

  while time.time() < stopwatch:
    for mat in connected_mats:
      # time.sleep(0.5)
      mat_sum = get_sinlge_mat_pressure_sum(mat)
      print(mat_sum)
    print(f"{time.time()}")
    print("\n")

  print(f"RECORDS COLLECTED: {len(current_map)}")

  # data_export.export_to_json(current_map) # un-comment to create json file with the appended maps (excercise)

if __name__ == "__main__":
  get_mat_pressures()