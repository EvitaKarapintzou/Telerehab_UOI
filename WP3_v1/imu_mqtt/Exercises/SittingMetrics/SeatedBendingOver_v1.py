import pandas as pd
import numpy as np
import os
from datetime import datetime
import statistics 
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.signal import argrelextrema
from scipy.spatial.transform import Rotation as R
from scipy.signal import butter, filtfilt
import json
import scipy


def plotIMUDATA(Limu, x, filename):
    time = [row[0] for row in Limu]
    w = [row[x] for row in Limu]

    plt.figure(figsize=(10, 6))  
    plt.plot(time, w, marker='o', linestyle='-', color='b')  
    plt.title('Time vs W Component')
    plt.xlabel('Time (sec)')
    plt.ylabel('W component of quaternion')
    plt.grid(True)  


def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs  
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)

    default_padlen = 2 * max(len(b), len(a)) - 1
    if len(data) <= default_padlen:
        padlen = len(data) - 1
    else:
        padlen = default_padlen

    y = filtfilt(b, a, data, padlen=padlen)
    return y


def striplist(L):
    A = []
    for item in L:
        t = item[1:-1]
        if ',' in t:
            t = t.split(',')
        else:
            t = t.split(' ')
        if "(number" not in t:
            A.append([t[-7],t[-5],t[-4],t[-3],t[-2],t[-1]])
    return A

def get_metrics(imu1,imu2,imu3,imu4, counter):
    Limu1 = striplist(imu1[2:])
    Limu2 = striplist(imu2[2:])
    Limu3 = striplist(imu3[2:])
    Limu4 = striplist(imu4[2:])
    

    dt1 = 0 
    dt2 = 0
    dt3 = 0
    dt4 = 0
    
    if(len(Limu1) > 0 ):
        dt1 = float(Limu1[-1][1]) - float(Limu1[0][1]);
    if(len(Limu2) > 0 ):
        dt2 = float(Limu2[-1][1]) - float(Limu2[0][1]);
    # if(len(Limu3) > 0 ):
    #     dt3 = float(Limu3[-1][1]) - float(Limu3[0][1]);
    # if(len(Limu4) > 0 ):
    #     dt4 = float(Limu4[-1][1]) - float(Limu4[0][1]);


    mean = statistics.mean([dt1, dt2, dt3, dt4])
    std = statistics.stdev([dt1, dt2, dt3, dt4])

    Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    # Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    # Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    if len(Limu1) > 0 and len(Limu2) > 0:
        returnedJson = getMetricsSeatingOld03(Limu1, Limu2, False) 
        return returnedJson

def getMetricsSeatingOld03(Limu1, Limu2, plotdiagrams):
   
    columns = ['Timestamp', 'elapsed(time)',  'W(number)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu1 = pd.DataFrame(Limu1, columns=columns)
    df_Limu1['elapsed(time)'] = pd.to_datetime(df_Limu1['elapsed(time)'], unit='ms')
    df_Limu1 = df_Limu1.sort_values(by='elapsed(time)')
    df_Limu1.set_index('elapsed(time)', inplace=True)
    
    columns = ['Timestamp', 'elapsed(time)',  'W(number)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu2 = pd.DataFrame(Limu2, columns=columns)
    df_Limu2['elapsed(time)'] = pd.to_datetime(df_Limu2['elapsed(time)'], unit='ms')
    df_Limu2 = df_Limu2.sort_values(by='elapsed(time)')
    df_Limu2.set_index('elapsed(time)', inplace=True)
 

    quaternions1 = df_Limu1[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    rotations1 = R.from_quat(quaternions1)
    euler_angles1 = rotations1.as_euler('xyz', degrees=False)
    euler_df1 = pd.DataFrame(euler_angles1, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    euler_angles_degrees1 = rotations1.as_euler('xyz', degrees=True)
    euler_df_degrees1 = pd.DataFrame(euler_angles_degrees1, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])
   
    quaternions2 = df_Limu2[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    rotations2 = R.from_quat(quaternions2)
    euler_angles2 = rotations2.as_euler('xyz', degrees=False)
    euler_df2 = pd.DataFrame(euler_angles2, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    euler_angles_degrees2 = rotations2.as_euler('xyz', degrees=True)
    euler_df_degrees2 = pd.DataFrame(euler_angles_degrees2, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])

    start_time = df_Limu2.index.min()
    end_time = df_Limu2.index.max()
    interval_length = pd.Timedelta(seconds=5)
    
    quaternions_df1 = df_Limu1;

    fs = 50
    cutoff = 0.5

    # Apply the filter to the Yaw data
    W_filtered1 = butter_lowpass_filter(quaternions_df1['W(number)'], cutoff, fs, order=5)
    Y_filtered1 = butter_lowpass_filter(quaternions_df1['Y (number)'], cutoff, fs, order=5)

    movement_magnitude1 = np.sqrt(np.square(W_filtered1) + np.square(Y_filtered1))

    yaw_filtered2 = butter_lowpass_filter(euler_df_degrees2['Yaw (degrees)'], cutoff, fs, order=5)

    peaks1, _ = find_peaks(movement_magnitude1)
    valleys1, _ = find_peaks(-movement_magnitude1)

    if(len(peaks1) == 0):
        return 0
    if(len(valleys1) == 0):
        return 0

    if valleys1[0] > peaks1[0]:
        peaks1 = peaks1[1:]  
    if peaks1[-1] < valleys1[-1]:
        valleys1 = valleys1[:-1]  
        
    movement_pairs1 = [(valleys1[i], peaks1[i]) for i in range(min(len(peaks1), len(valleys1)))]

    movement_ranges_yaw1 = []
    movement_ranges_roll1 = []

    for valley1, peak1 in movement_pairs1:
            yaw_range1 = abs(W_filtered1[peak1] - W_filtered1[valley1])
            movement_ranges_yaw1.append(yaw_range1)
            
            roll_range1 = abs(Y_filtered1[peak1] - Y_filtered1[valley1])
            movement_ranges_roll1.append(roll_range1)

    combined_movement_ranges1 = [np.sqrt(yaw1**2 + roll1**2) for yaw1, roll1 in zip(movement_ranges_yaw1, movement_ranges_roll1)]

    for i, (yaw_range, roll_range) in enumerate(zip(movement_ranges_yaw1, movement_ranges_roll1)):
        combined_range1 = np.sqrt(yaw_range1**2 + roll_range1**2)
        print(f"Movement {i+1}: Yaw Range = {yaw_range1:.2f} degrees, Roll Range = {roll_range1:.2f} degrees, Combined Range = {combined_range1:.2f} degrees")

    significant_movements1 = [(pair1, yaw1, roll1, np.sqrt(yaw1**2 + roll1**2)) for pair1, yaw1, roll1 in zip(movement_pairs1, movement_ranges_yaw1, movement_ranges_roll1) if np.sqrt(yaw1**2 + roll1**2) >= 40]

    filtered_pairs1 = [item[0] for item in significant_movements1]
    filtered_combined_ranges1 = [item[3] for item in significant_movements1]

    for i, (_, _, _, combined_range1) in enumerate(significant_movements1):
        print(f"Significant Movement {i+1}: Combined Range = {combined_range1:.2f} degrees")

    movement_durations1 = []
    for start, end in filtered_pairs1:
        start_time1 = df_Limu1.iloc[start].name  # Assuming the DataFrame index is datetime or similar
        end_time1 = df_Limu1.iloc[end].name
        duration1 = (end_time1 - start_time1).total_seconds()
        movement_durations1.append(duration1)


    total_duration_seconds1 = (df_Limu1.index[-1] - df_Limu1.index[0]).total_seconds()
    pace1 = len(filtered_pairs1) / total_duration_seconds1  # Movements per second

    mean_combined_range1 = np.mean(filtered_combined_ranges1)
    std_combined_range1 = np.std(filtered_combined_ranges1, ddof=1)  # ddof=1 for sample standard deviation

    mean_duration1 = np.mean(movement_durations1)
    std_duration1 = np.std(movement_durations1, ddof=1)  # ddof=1 for sample standard deviation    

    # Calculate chin to chest distance
    def calculate_chin_to_chest_distance(roll_range1, roll_range):
        relative_pitch_angle = roll_range1 - roll_range
        relative_pitch_angle_rad = np.radians(relative_pitch_angle)
        # vertical_distance = np.cos(relative_pitch_angle_rad)
        return relative_pitch_angle

    chin_to_chest_distances = [
        calculate_chin_to_chest_distance(pitch_head, pitch_back)
        for pitch_head, pitch_back in zip(euler_df_degrees1['Pitch (degrees)'], euler_df_degrees2['Pitch (degrees)'])
    ]

    #IMU2 BACK
    peaks2, _ = find_peaks(yaw_filtered2)
    valleys2, _ = find_peaks(-yaw_filtered2)

    if(len(peaks2) == 0):
        return 0
    if(len(valleys2) == 0):
        return 0

    if valleys2[0] > peaks2[0]:
        peaks2 = peaks2[1:]  
    if peaks2[-1] < valleys2[-1]:
        valleys2 = valleys2[:-1]  
        
    movement_pairs2 = [(valleys2[i], peaks2[i]) for i in range(min(len(peaks2), len(valleys2)))]

    movement_ranges2 = [yaw_filtered2[peak2] - yaw_filtered2[valley2] for valley2, peak2 in movement_pairs2]

    significant_movements2 = [(pair2, mrange2) for pair2, mrange2 in zip(movement_pairs2, movement_ranges2) if mrange2>= 0.1]

    filtered_pairs2 = [pair2 for pair2, mrange2 in significant_movements2]
    filtered_ranges2 = [mrange2 for pair2, mrange2 in significant_movements2]


    movement_details2 = []
    for i, (pair2, mrange2) in enumerate(significant_movements2):
        movement_detail2 = f"Significant Movement for Back {i+1}: Pair Back = {pair2}, Range = {mrange2:.2f} degrees"
        print(movement_detail2)
        movement_details2.append(movement_detail2)  # Append to list

    movement_durations2 = []
    for start, end in filtered_pairs2:
        start_time2 = df_Limu2.iloc[start].name
        end_time2 = df_Limu2.iloc[end].name
        duration2 = (end_time - start_time).total_seconds()
        movement_durations2.append(duration2)

    total_duration_seconds2 = (df_Limu2.index[-1] - df_Limu2.index[0]).total_seconds()
    pace2 = len(filtered_pairs2) / total_duration_seconds2  # Movements per second
    mean_range2 = np.mean(filtered_ranges2)
    std_range2 = np.std(filtered_ranges2, ddof=1)

    mean_duration2 = np.mean(movement_durations2) if movement_durations2 else -1
    std_duration2 = np.std(movement_durations2, ddof=1) if movement_durations2 else -1        

    metrics_data = {
        "total_metrics": {
            "***************LIMU1*************":{
               "number_of_movements1": int(len(filtered_pairs1)),
               "pace_movements_per_second1": float(pace1),
               "mean_range_degrees1": float(mean_combined_range1),
               "std_range_degrees1": float(std_combined_range1),
               "mean_duration_seconds1": float(mean_duration1),
               "std_duration_seconds1": float(std_duration1),
            },
            "***************LIMU2*************":{
               "number_of_movements2": int(len(filtered_pairs2)),
               "pace_movements_per_second2": float(pace2),
               "mean_range_degrees2": float(mean_range2),
               "std_range_degrees2": float(std_range2),
               "mean_duration_seconds2": float(mean_duration2),
               "std_duration_seconds2": float(std_duration2),
               "Exercise duration": total_duration_seconds2,
               "Chin_to_Chest_Distance": min(chin_to_chest_distances)  # Minimum distance during exercise
            }
        }
    }
        
    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{datetime_string}_SeatedBendingOver_metrics.txt"

    # Save the metrics to a file
    save_metrics_to_txt(metrics_data, filename)

    return json.dumps(metrics_data, indent=4)

    
def save_metrics_to_txt(metrics, file_path):
    main_directory = "Sitting Metrics Data"
    sub_directory = "SeatedBendingOver Metrics Data"

    directory = os.path.join(main_directory, sub_directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    full_path = os.path.join(directory, file_path)

    with open(full_path, 'w') as file:
        for key, value in metrics.items():
            if isinstance(value, dict):  
                file.write(f"{key}:\n")
                for sub_key, sub_value in value.items():
                    file.write(f"  {sub_key}: {sub_value}\n")
            else:
                file.write(f"{key}: {value}\n")
            file.write("\n")
