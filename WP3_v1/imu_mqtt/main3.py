import logging
import sys
import os
import numpy as np
# Set up logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(message)s')

# Create file handler to log to a file
file_handler = logging.FileHandler('app.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create console handler to log to the command line
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Suppress debug logging for matplotlib
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Redirect stdout and stderr to logger
class StreamToLogger:
    def __init__(self, log_level):
        self.log_level = log_level
        self.line_buffer = ''

    def write(self, message):
        if message.strip():
            self.log_level(message.strip())

    def flush(self):
        pass

# Redirect stdout and stderr to the logger
sys.stdout = StreamToLogger(logger.info)  # Redirect stdout to logger.info
sys.stderr = StreamToLogger(logger.error)  # Redirect stderr to logger.error

import multiprocessing as mp
import paho.mqtt.client as mqtt
import time, re
import logging
from data_management_v04  import scheduler, receive_imu_data
from api_management import login, get_device_api_key
from configure_file_management import read_configure_file
from shared_variables import queueData, scheduleQueue, imus, enableConnectionToAPI, MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL
from shared_variables import counter, startReceiving, lastDataTime, mqttState
import multiprocessing as mp
from websocketServer import run_websocket_server
import csv
import psutil
from UDPSERVER import start_multicast_server
from sensor_data import SensorData

import requests
import configparser
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R




logging.info('This is a test log entry.')


def quaternion_to_euler(w, x, y, z):
    # Roll (x-axis rotation)
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(t0, t1)

    # Pitch (y-axis rotation)
    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch = np.arcsin(t2)

    # Yaw (z-axis rotation)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t3, t4)

    return roll, pitch, yaw

# Function to get daily schedule
def get_daily_schedule():
    # Load API key from config file
    config = configparser.ConfigParser()
    config.read('/home/uoi/Documents/GitHub/Telerehab_UOI/WP3_v1/imu_mqtt/config.ini')
    api_key_edge = config['API'].get('key_edge', '')

    # Define the API endpoint
    daily_schedule_url = 'https://telerehab-develop.biomed.ntua.gr/api/PatientSchedule/daily'

    headers = {
        'accept': '*/*',
        'Authorization': api_key_edge
    }
    response = requests.get(daily_schedule_url, headers=headers)
    print(response)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def save_to_csv(data):
    with open('sensor_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data.device_mac_address, data.timestamp, data.w, data.x, data.y, data.z])

# Define appStatus as a shared string (character array)
appStatus = mp.Array('c', b'down')
startExercise = mp.Array('c', b'false')
finishExercise = mp.Array('c', b'false')

import threading


read_configure_file()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("IMUsettings")
    client.subscribe("DeviceStatus")
    client.subscribe("StopRecording")

def on_message(client, userdata, msg):
    global mqttState 
    startReceiving.value = True   
    lastDataTime.value = time.time()
    
    logging.info(f"Message Received -> {msg.payload.decode()}")

    if 'start' in msg.payload.decode():
        new_value = "R"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise started!\033[0m")
        startExercise.value = b'e01';
        print('I got START');
    
    elif 'done' in msg.payload.decode():
        print("\033[1m\033[93mI got done from mobile app\033[0m")
        with finishExercise.get_lock(): 
            finishExercise.value = b'true'
        
    elif 'stop' in msg.payload.decode():
        new_value = "S"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise finished!\033[0m") 
    elif 'StopRecording' in msg.payload.decode():
        new_value = "S"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise finished!\033[0m") 
    elif 'up' in msg.payload.decode():
        with appStatus.get_lock():  # Synchronize access
            appStatus.value = b'up'
        with finishExercise.get_lock(): 
            finishExercise.value = b'false'
        print('I got UP');
    elif 'myIMUsettings' in msg.payload.decode():
        print();

    elif 'exit' in msg.payload.decode():
        print('EXIT');

    elif 'Quaternion' in msg.payload.decode():
        print(msg.payload.decode())
    elif 'Linear' in msg.payload.decode():
        print(msg.payload.decode());
    elif '=' in msg.payload.decode():
        print('config message sent')
    else:
        print(msg.payload.decode())

# Function to read data from the queue and update live plot
# Function to read data from the queue and update live plot
def live_plot_from_queue(q):
    fig, axs = plt.subplots(8, 4, figsize=(12, 16))  # 4x4 grid for quaternions + 4x4 grid for Euler angles
    lines = {}

    body_parts = ['HEAD', 'PELVIS', 'LEFTFOOT', 'RIGHTFOOT']
    components = ['w', 'x', 'y', 'z']
    euler_angles = ['roll', 'pitch', 'yaw']

    # Initialize plot lines for quaternions and Euler angles
    for i, body_part in enumerate(body_parts):
        for j, comp in enumerate(components):
            axs[i, j].set_title(f"{body_part} - {comp} Component")
            axs[i, j].set_xlim(0, 10000)
            axs[i, j].set_ylim(-1, 1)
            axs[i, j].grid(True)
            lines[(body_part, comp)], = axs[i, j].plot([], [], lw=2)

        for j, angle in enumerate(euler_angles):
            axs[i+4, j].set_title(f"{body_part} - {angle} (Euler Angle)")
            axs[i+4, j].set_xlim(0, 10000)
            axs[i+4, j].set_ylim(-180, 180)  # Euler angles in degrees
            axs[i+4, j].grid(True)
            lines[(body_part, angle)], = axs[i+4, j].plot([], [], lw=2)

    imu_data = {bp: {comp: [] for comp in components + euler_angles} for bp in body_parts}

    # Update plot function for FuncAnimation
    def update_plot(frame):
        while not q.empty():
            data = q.get()  # Read data from the queue

            if ":" in data:  # Check for valid sensor data format
                sensor_data = SensorData.from_json(data)
                body_part = sensor_data.device_mac_address

                if body_part in imu_data:
                    # Append quaternion components
                    imu_data[body_part]['w'].append(sensor_data.w)
                    imu_data[body_part]['x'].append(sensor_data.x)
                    imu_data[body_part]['y'].append(sensor_data.y)
                    imu_data[body_part]['z'].append(sensor_data.z)

                    # Convert quaternions to Euler angles
                    quaternions = np.array([sensor_data.w, sensor_data.x, sensor_data.y, sensor_data.z]).reshape(1, -1)
                    rotations = R.from_quat(quaternions)
                    euler = rotations.as_euler('xyz', degrees=True)
                    
                    # Append Euler angles
                    imu_data[body_part]['roll'].append(euler[0][0])
                    imu_data[body_part]['pitch'].append(euler[0][1])
                    imu_data[body_part]['yaw'].append(euler[0][2])

                    # Keep only the last 10,000 data points
                    for comp in components + euler_angles:
                        imu_data[body_part][comp] = imu_data[body_part][comp][-10000:]

        # Update plot lines with new data for each body part and component
        for i, body_part in enumerate(body_parts):
            for j, comp in enumerate(components):
                if len(imu_data[body_part][comp]) > 0:
                    lines[(body_part, comp)].set_data(np.arange(len(imu_data[body_part][comp])), imu_data[body_part][comp])
                    axs[i, j].set_xlim(max(0, len(imu_data[body_part][comp]) - 10000), len(imu_data[body_part][comp]))

            # Update Euler angle plots
            for j, angle in enumerate(euler_angles):
                if len(imu_data[body_part][angle]) > 0:
                    lines[(body_part, angle)].set_data(np.arange(len(imu_data[body_part][angle])), imu_data[body_part][angle])
                    axs[i+4, j].set_xlim(max(0, len(imu_data[body_part][angle]) - 10000), len(imu_data[body_part][angle]))

        return lines.values()

    # Initialize animation
    ani = FuncAnimation(fig, update_plot, interval=100)  # Update every 100ms
    plt.tight_layout()
    plt.show()

def waitandkill(client):
    time.sleep(120)
    print('i am sending stoprecording')
    client.publish('StopRecording', 'StopRecording')



def runScenario(queueData):
    try:
        print('running scenario')
        exercises = get_daily_schedule()
        if not exercises:
            print("No exercises found. Exiting loop.")
            return -1;
        for exercise in exercises:

            mbB1 = mp.Process(target=scheduler,args=(scheduleQueue,));
            mbB1.start();
            print(exercise)
            print(f"Exercise Name: {exercise['exerciseName']}, Progression: {exercise['progression']}")

            current_exercise = exercises[0];
            if (exercise['exerciseName'] == 'ex1'):
                config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=EF:0F:A9:3D:48:AA-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_01"
            elif (exercise['exerciseName'] == 'ex2'):
                config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-OFF,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_06"

            topic = "IMUsettings"
            with appStatus.get_lock():
                GETappStatus = bytes(appStatus.value).decode()  
            with startExercise.get_lock():
                GETstartExercise = bytes(startExercise.value).decode()
            
            '''
            while (GETappStatus != 'up'):
                print('waiting for the VC app...')
                time.sleep(1);
                with appStatus.get_lock():
                    GETappStatus = bytes(appStatus.value).decode()  
            '''
            #mobile app is up and running
            print('---I got UP. mobile app is up and running---')

            #start exercise
            print('---I am initiating ' + exercise['exerciseName'] + '---');

            print("config_message_01 =", config_message)
            print("exercise =", exercise)

            message = config_message;
            client.publish(topic, message);
            time.sleep(5);
            waitkill = mp.Process(target=waitandkill, args=(client,))
            waitkill.start()
            client.publish('StartRecording', 'start');

            #mbB = mp.Process(target=receive_imu_data,args=(queueData, scheduleQueue, config_message, exercise, ));
            #mbB.start();
            #mbB.join();

            # Start the live plotting function
            live_plot_from_queue(queueData)

            # Wait for the producer process to finish


            time.sleep(60); #wait

            #input();
            client.publish('StopRecording', 'StopRecording')

            #client.publish(topic, 'stop');

            # communication with the VC

            
            #start exercise sitting 02

            #client.publish(topic, 'exit');

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}");

    



if(enableConnectionToAPI):
    login()
    get_device_api_key()

server_process = mp.Process(target=start_multicast_server, args=(queueData,))
server_process.start()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)

def publish_loop():
    topic = "IMUsettings"
    message1 = "myIMUsettings"

    while True:
        with appStatus.get_lock():
            current_status = bytes(appStatus.value).decode()  # Properly decode to string
        with startExercise.get_lock():
            startExer = bytes(startExercise.value).decode()  # Properly decode to string

        if current_status == 'down':
            #client.publish(topic, message1)
            print('waiting...')
            time.sleep(1)
        elif current_status == 'up':
            if (startExer == 'e01'):
                message = config_message;
                client.publish(topic, message);
            with startExercise.get_lock():
                startExercise.value = b'false'                
        else:
            time.sleep(1)  # Sleep to avoid busy-waiting


# Start the publishing loop in another thread
thread = threading.Thread(target=publish_loop)
#thread.start()

#threadscenario = threading.Thread(target=runScenario, args=(queueData, ))
#threadscenario.start()
runScenario(queueData)
client.loop_forever()

#thread.join()
#threadscenario.join()
