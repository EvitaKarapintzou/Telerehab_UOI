import time
import serial
import configuration

conf = configuration.config

baud = conf["BAUDRATE"]
time_out = conf["TIMEOUT"]

request = conf['REQUEST_NEW_MAP']
start = conf['START_STREAM']
stop = conf['STOP_STREAM']

def connect_to_device(device):
  ser = serial.Serial(
  port=device['port'],
  baudrate=baud,
  timeout=time_out
  )

  return ser

def request_new_map(ser):
  data = request
  ser.write(data.encode())

def start_stream(ser):
  data = start
  ser.write(data.encode())

def stop_stream(ser):
  data = stop
  ser.write(data.encode())

if __name__ == '__main__':
  connect_to_device()
  request_new_map()
  start_stream()
  stop_stream()