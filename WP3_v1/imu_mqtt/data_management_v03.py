import time
import json
import numpy as np
import re
from shared_variables import enableInterpolation, isFoundFirstTimestamp, firstTimestamp, imus, firstPacket, timeToCallMetrics, sensorDataToUpload, imu1Queue, imu2Queue, imu3Queue, imu4Queue, mqttState, enableMetrics, imu1FinalQueue, imu2FinalQueue, imu3FinalQueue, imu4FinalQueue, csv_file_path, imus, counter, startReceiving, lastDataTime, enableConnectionToAPI, feedbackData
#from get_online_metrics_ex_1_pr_1 import get_metrics
from SittingMetrics.MaintainingFocus_HeadUpandDown import get_metrics as get_metrics_MaintainingFocus_HeadUpandDown
#from SittingMetrics.HeelRaises import get_metrics
from SittingMetrics.MaintainingFocus_Headrotation import get_metrics as get_metrics_MaintainingFocus_Headrotation
# from SittingMetrics.MaintainingFocus_Headrotation import getMetricsSittingOld01
# from SittingMetrics.Trunk_rotation import get_metrics
# from SittingMetrics.Trunk_rotation import getMetricsSittingNew01
# from SittingMetrics.Assisted_toe_raises import get_metrics
# from SittingMetrics.Assisted_toe_raises import getMetricsSittingNew02
# from SittingMetrics.SeatedMarchingSpot import get_metrics
# from SittingMetrics.SeatedMarchingSpot import getMetricsSittingNew04
#from SittingMetrics.MaintainingFocus_HeadUpandDown import getMetricsSittingOld02
#from getMetricsSittingOld02 import get_metrics
#from getMetricsSittingOld02 import getMetricsSitting01
#from GaitMetrics.WalkingHorizontalHeadTurns import getMetricsGaitNew02
#from GaitMetrics.WalkingHorizontalHeadTurns import get_metrics
from csv_management import write_in_files
from api_management import upload_sensor_data, postExerciseScore
from sensor_data import SensorData
import multiprocessing as mp
from scipy.interpolate import interp1d
import csv




def reformat_sensor_data(sensor_data_list):
    if not sensor_data_list:
        return []

    # Get the reference timestamp
    reference_timestamp = sensor_data_list[0].timestamp

    reformatted_data = []

    # Iterate through the sensor data list
    for data in sensor_data_list:
        timestamp = data.timestamp
        elapsed_time = timestamp - reference_timestamp
        reformatted_entry = [timestamp, elapsed_time, data.w, data.x, data.y, data.z]
        reformatted_data.append(reformatted_entry)

    return reformatted_data


import os
import matplotlib.pyplot as plt
from datetime import datetime

def get_data_tranch(q1, q2, q3, q4, counter, exercise):
    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []

    # Empty the queues into respective lists
    while not q1.empty():
        imu1List.append(q1.get())
    while not q2.empty():
        imu2List.append(q2.get())
    while not q3.empty():
        imu3List.append(q3.get())
    while not q4.empty():
        imu4List.append(q4.get())

    # Create directory for plots, common folder for the exercise and timestamp
    current_time = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{exercise}_{current_time}"
    os.makedirs(folder_name, exist_ok=True)

    # Save the data lists to CSV files
    save_list_to_csv(imu1List, 'HEAD', counter, folder_name)
    save_list_to_csv(imu2List, 'PELVIS', counter, folder_name)
    save_list_to_csv(imu3List, 'LEFTFOOT', counter, folder_name)
    save_list_to_csv(imu4List, 'RIGHTFOOT', counter, folder_name)

    # Plot and save the data for each IMU
    plot_imu_data(imu1List, "HEAD", counter, folder_name)
    plot_imu_data(imu2List, "PELVIS", counter, folder_name)
    plot_imu_data(imu3List, "LEFTFOOT", counter, folder_name)
    plot_imu_data(imu4List, "RIGHTFOOT", counter, folder_name)

    # Handle metrics if enabled
    if enableMetrics:
        if exercise == 'exer_01':
            returnedJson = get_metrics_MaintainingFocus_Headrotation(imu1List, imu2List, imu3List, imu4List, counter)
        elif exercise == 'exer_02':
            returnedJson = get_metrics_MaintainingFocus_HeadUpandDown(imu1List, imu2List, imu3List, imu4List, counter)

    # Final actions when counter reaches 4
    if counter == 4:
        postExerciseScore(returnedJson, "1")    
    print(returnedJson)

def plot_imu_data(imu_list, body_part, counter, folder_name):
    if not imu_list:
        return  # Skip if the list is empty

    # Extract w, x, y, z and timestamps
    timestamps = [item.timestamp for item in imu_list]
    w_values = [item.w for item in imu_list]
    x_values = [item.x for item in imu_list]
    y_values = [item.y for item in imu_list]
    z_values = [item.z for item in imu_list]

    # Create 4 subplots for w, x, y, z
    fig, axs = plt.subplots(4, 1, figsize=(10, 10))
    fig.suptitle(f'{body_part} - Counter {counter}', fontsize=16)

    # Plot each component
    axs[0].plot(timestamps, w_values, label='w')
    axs[0].set_title(f'{body_part} - w')
    axs[0].set_xlabel('Timestamp')
    axs[0].set_ylabel('w')

    axs[1].plot(timestamps, x_values, label='x')
    axs[1].set_title(f'{body_part} - x')
    axs[1].set_xlabel('Timestamp')
    axs[1].set_ylabel('x')

    axs[2].plot(timestamps, y_values, label='y')
    axs[2].set_title(f'{body_part} - y')
    axs[2].set_xlabel('Timestamp')
    axs[2].set_ylabel('y')

    axs[3].plot(timestamps, z_values, label='z')
    axs[3].set_title(f'{body_part} - z')
    axs[3].set_xlabel('Timestamp')
    axs[3].set_ylabel('z')

    # Save the figure in the common folder with the counter in the file name
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f'{folder_name}/{body_part}_counter_{counter}.png')
    plt.close(fig)



def scheduler(scheduleQueue):
    print("Waiting for 'STARTCOUNTING' message...")

    # Wait until "STARTCOUNTING" message is received in the scheduleQueue
    while True:
        if (not scheduleQueue.empty()):
            message = scheduleQueue.get()  # Block until a message is received
            if message == "startcounting":
                print("Received 'startcounting'. Starting the scheduler...")
                break  # Exit the loop and proceed to start the scheduling

    # Now start the main loop
    while True:
        time.sleep(timeToCallMetrics)
        scheduleQueue.put("GO")


def parse_config_message(config_message):
    config_dict = {}
    parts = config_message.split(",")

    for part in parts:
        if "=" in part:
            body_part, rest = part.split("=")
            mac_address, mode = rest.split("-")
            if mode != "OFF":  # Only add to config_dict if the mode is not OFF
                config_dict[body_part] = (mac_address, mode)
        else:
            exercise_code = part  # Extract the exercise code (last part)

    return config_dict, exercise_code


def initialize_imu_data_structures(config_dict, manager):
    imu_data = {}

    for role in config_dict.keys():
        # For each IMU device (role), initialize a list and two queues
        imu_list = []
        imu_queue = manager.Queue()
        imu_final_queue = manager.Queue()
        
        # Store the lists and queues in the dictionary for that role (e.g., HEAD, PELVIS)
        imu_data[role] = (imu_list, imu_queue, imu_final_queue)
    
    return imu_data

def safe_get_imu_queue(imu_data, body_part, default_queue):
    """Safely retrieve the IMU queue, or return a default if the body part is not in the configuration."""
    return imu_data.get(body_part, [None, default_queue])[1]  # Access the queue from imu_data or return the default queue


def receive_imu_data(q, scheduleQueue, config_message, exercise):

    # Initialize multiprocessing manager
    manager = mp.Manager()
    imu_config, exercise_code = parse_config_message(config_message)
    print('exercise_code =', exercise_code )

    # Create the data structures with manager-based queues
    imu_data = initialize_imu_data_structures(imu_config, manager)
    print('imu_data = ', imu_data)

    global isFoundFirstTimestamp, enableInterpolation
    # Sample configuration message
    jjj = 0;
    INTERVALS = 0;
    # Set of body parts that have received at least one sample
    received_body_parts = set()

    # The set of body parts expected based on the configuration
    expected_body_parts = {key for key, value in imu_data.items() if value[1] != "OFF"}
    print('expected_body_parts = ', expected_body_parts)


    if exercise_code == 'exer_01':
        while INTERVALS < 4 or not q.empty():
            #if (q.empty()):
            #    print('empty q')
            data = q.get()  # Read data from the dataQueue
            #print(data)

            if ":" in data:  # Check for valid sensor data format
                # Convert JSON data to SensorData object
                sensor_data = SensorData.from_json(data)

                # Use deviceMacAddress as the body part identifier
                body_part = sensor_data.device_mac_address
                #print(body_part)

                if body_part in expected_body_parts:
                    received_body_parts.add(body_part);
                
                if (received_body_parts == expected_body_parts):
                    scheduleQueue.put('startcounting')
                    # Fetch the relevant lists and queues from imu_data
                    if body_part in imu_data:
                        imu_list, imu_queue, imu_finalqueue = imu_data[body_part]

                        # Add the sensor data to the appropriate structures
                        imu_list.append(sensor_data)
                        imu_queue.put(sensor_data)
                        imu_finalqueue.put(sensor_data)
                    else:
                        print(f"Unrecognized body part: {body_part}")

                    # Check if there is something in the schedule queue
                    if not scheduleQueue.empty():
                        message = scheduleQueue.get()  # Block until a message is received
                        if message == "GO":
                            # Call the data processing function based on the queues
                            print('I am calling get_data_tranch')
                            # interpolate
                            process_and_interpolate_imus(imu_data, target_rate_hz=100)  # 100 Hz target rate

                            get_data_tranch(
                                safe_get_imu_queue(imu_data, 'HEAD', manager.Queue()),  # imu1Queue
                                safe_get_imu_queue(imu_data, 'PELVIS', manager.Queue()),  # imu2Queue
                                safe_get_imu_queue(imu_data, 'LEFTFOOT', manager.Queue()),  # imu3Queue
                                safe_get_imu_queue(imu_data, 'RIGHTFOOT', manager.Queue()),  # imu4Queue
                                INTERVALS,  # Pass the counter variable
                                exercise_code  # Pass the exercise code
                            )

                            scheduleQueue.get()  # Consume the scheduled task
                            INTERVALS += 1
                            print(f"Intervals = {INTERVALS}")

                            if INTERVALS == 4:
                                print("Processing the entire data stream...")
                                get_data_tranch(
                                    imu_data.get('HEAD', [None, None, manager.Queue()])[2],  # imu1FinalQueue
                                    imu_data.get('PELVIS', [None, None, manager.Queue()])[2],  # imu2FinalQueue
                                    imu_data.get('LEFTFOOT', [None, None, manager.Queue()])[2],  # imu3FinalQueue
                                    imu_data.get('RIGHTFOOT', [None, None, manager.Queue()])[2],  # imu4FinalQueue
                                    INTERVALS,
                                    exercise_code
                                )
                                break;



    return 0;
            

def save_list_to_csv(imu_list, body_part, counter, folder_name):
    if not imu_list:
        return  # Skip if the list is empty

    # Create the CSV file path
    csv_file_path = os.path.join(folder_name, f"{body_part}_data_counter_{counter}.csv")
    
    # Write data to CSV
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'w', 'x', 'y', 'z'])  # CSV headers
        for data in imu_list:
            writer.writerow([data.timestamp, data.w, data.x, data.y, data.z])


def find_common_time_period(imu_data):
    """
    Finds the common time period for all available IMU data lists.
    Returns the maximum start time and the minimum end time across all non-empty lists.
    """
    max_start_time = float('-inf')
    min_end_time = float('inf')

    for body_part, (imu_list, _, _) in imu_data.items():
        if imu_list:  # Check if the list is not empty
            # Access the timestamp from the first and last SensorData object in the list
            start_time = imu_list[0].timestamp
            end_time = imu_list[-1].timestamp

            # Update the common time range
            max_start_time = max(max_start_time, start_time)
            min_end_time = min(min_end_time, end_time)

    return max_start_time, min_end_time

# Function to crop the IMU data
def crop_imu_data(imu_data, max_start_time, min_end_time):
    cropped_data = {}
    
    for body_part, (imu_list, imu_queue, imu_finalqueue) in imu_data.items():
        # Filter data between max_start_time and min_end_time
        cropped_list = [d for d in imu_list if max_start_time <= d['timestamp'] <= min_end_time]
        cropped_data[body_part] = (cropped_list, imu_queue, imu_finalqueue)
    
    return cropped_data


# Function to interpolate IMU data to 100Hz
def interpolate_imu_data(imu_list, target_rate_hz, max_start_time, min_end_time):
    """
    Interpolate the IMU data to match the target sampling rate and common time period.
    """
    if not imu_list:
        return []

    # Extract timestamps and other data (e.g., w, x, y, z)
    timestamps = np.array([data.timestamp for data in imu_list])
    w_values = np.array([data.w for data in imu_list])
    x_values = np.array([data.x for data in imu_list])
    y_values = np.array([data.y for data in imu_list])
    z_values = np.array([data.z for data in imu_list])

    # Limit timestamps to the common time period
    mask = (timestamps >= max_start_time) & (timestamps <= min_end_time)
    timestamps = timestamps[mask]
    w_values = w_values[mask]
    x_values = x_values[mask]
    y_values = y_values[mask]
    z_values = z_values[mask]

    if len(timestamps) == 0:
        return []  # Return an empty list if no valid data points

    # Calculate the new timestamps with the target rate
    new_timestamps = np.arange(max_start_time, min_end_time, 1000.0 / target_rate_hz)  # target rate in ms

    # Interpolate values to the new timestamps
    interp_w = np.interp(new_timestamps, timestamps, w_values)
    interp_x = np.interp(new_timestamps, timestamps, x_values)
    interp_y = np.interp(new_timestamps, timestamps, y_values)
    interp_z = np.interp(new_timestamps, timestamps, z_values)

    # Return the interpolated data as a list of SensorData objects
    interpolated_data = []
    for i in range(len(new_timestamps)):
        interpolated_data.append(SensorData(
            device_mac_address=imu_list[0].device_mac_address,  # Use same device address
            timestamp=new_timestamps[i],
            w=interp_w[i],
            x=interp_x[i],
            y=interp_y[i],
            z=interp_z[i]
        ))
    return interpolated_data



def process_and_interpolate_imus(imu_data, target_rate_hz):
    """
    Process and interpolate each IMU data list based on the target sampling rate.
    """
    # Find the common time period for all IMU data
    max_start_time, min_end_time = find_common_time_period(imu_data)

    for body_part, (imu_list, imu_queue, imu_finalqueue) in imu_data.items():
        if imu_list:
            # Interpolate the list and replace the original data with interpolated data
            interpolated_list = interpolate_imu_data(imu_list, target_rate_hz, max_start_time, min_end_time)
            imu_data[body_part] = (interpolated_list, imu_queue, imu_finalqueue)
            print(f"{body_part} data interpolated.")
        else:
            print(f"No data available for {body_part}, skipping interpolation.")

