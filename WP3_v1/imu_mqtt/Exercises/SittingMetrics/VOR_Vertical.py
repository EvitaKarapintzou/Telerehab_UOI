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


# def interpolate_imu_data(imu_data, starttime, endtime, N):
    """
    Interpolate IMU data (w, x, y, z) between starttime and endtime into N samples.

    Parameters:
    imu_data (list of lists): The IMU data in format [time, w, x, y, z, _, _].
    starttime (float): The start time for interpolation.
    endtime (float): The end time for interpolation.
    N (int): Number of samples to interpolate.

    Returns:
    list of lists: Interpolated IMU data with N entries.
    """
    

def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs  
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)

    # Check if data length is greater than default padlen, adjust if necessary
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
    
    #print(')))))) ', Limu1[0].index(''))
    # if ['MAC'] in Limu1:
    #     Limu1 = Limu1[Limu1.index(['MAC']) + 1:]
    # if ['MAC'] in Limu2:
    #     Limu2 = Limu2[Limu2.index(['MAC']) + 1:]
    # if ['MAC'] in Limu3:
    #     Limu3 = Limu3[Limu3.index(['MAC']) + 1:]
    # if ['MAC'] in Limu4:
    #     Limu4 = Limu4[Limu4.index(['MAC']) + 1:]

    dt1 = 0 
    dt2 = 0
    dt3 = 0
    dt4 = 0
    
    if(len(Limu1) > 0 ):
        dt1 = float(Limu1[-1][0]) - float(Limu1[0][0]);
    if(len(Limu2) > 0 ):
        dt2 = float(Limu2[-1][0]) - float(Limu2[0][0]);
    # if(len(Limu3) > 0 ):
    #     dt3 = float(Limu3[-1][0]) - float(Limu3[0][0]);
    # if(len(Limu4) > 0 ):
    #     dt4 = float(Limu4[-1][0]) - float(Limu4[0][0]);

    mean = statistics.mean([dt1, dt2, dt3, dt4])
    std = statistics.stdev([dt1, dt2, dt3, dt4])


    Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    # Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    # Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    if(len(Limu1) > 0) and len(Limu2) > 0:
        returnedJson = getMetricsSittingOld02(Limu1, Limu2, False) 
        return returnedJson

def getMetricsSittingOld02(Limu1, Limu2, plotdiagrams):
   
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
    euler_angles = rotations1.as_euler('xyz', degrees=False)
    euler_df1 = pd.DataFrame(euler_angles, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    euler_angles_degrees = rotations1.as_euler('xyz', degrees=True)
    euler_df_degrees = pd.DataFrame(euler_angles_degrees, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])
   
    quaternions2 = df_Limu2[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    rotations2 = R.from_quat(quaternions2)
    euler_angles2 = rotations2.as_euler('xyz', degrees=False)
    euler_df2 = pd.DataFrame(euler_angles2, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    euler_angles_degrees2 = rotations2.as_euler('xyz', degrees=True)
    euler_df_degrees2 = pd.DataFrame(euler_angles_degrees2, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])

    start_time = df_Limu2.index.min()
    end_time = df_Limu2.index.max()
    interval_length = pd.Timedelta(seconds=5)
    
    if (plotdiagrams):
        plt.figure(figsize=(10, 6))
        plt.xlabel('Timestamp')
        plt.ylabel('Quaternion Components')
        plt.title('Quaternion Components (W, X, Y, Z) over Time')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        plt.savefig('quaternion_components_plot!!!!!!!.png')
        #plt.show()
    
    quaternions_df1 = df_Limu1;

    fs = 50
    cutoff = 0.5
    
    angular_velocity = euler_df_degrees.diff().abs() * fs
    acceleration = angular_velocity.diff().abs() * fs
    peak_acceleration = acceleration.max()

    # roll_right = euler_df_degrees['Roll (degrees)'].where(euler_df_degrees['Roll (degrees)'] > 0).mean()
    # roll_left = abs(euler_df_degrees['Roll (degrees)'].where(euler_df_degrees['Roll (degrees)'] < 0).mean())
    # movement_symmetry = (roll_right - roll_left) / (0.5 * (roll_right + roll_left))
  


    if (plotdiagrams):
        plt.figure(figsize=(12, 8))
        plt.plot(euler_df_degrees.index, euler_df_degrees['Roll (degrees)'], label='Roll', linewidth=1)
        plt.plot(euler_df_degrees.index, euler_df_degrees['Pitch (degrees)'], label='Pitch', linewidth=1)
        plt.plot(euler_df_degrees.index, euler_df_degrees['Yaw (degrees)'], label='Yaw', linewidth=1)

        plt.xlabel('Timestamp')
        plt.ylabel('Euler Angles (degrees)')
        plt.title('Euler Angles (Roll, Pitch, Yaw) over Time')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()  
        plt.show()



    # yaw_filtered = butter_lowpass_filter(euler_df_degrees['Yaw (degrees)'], cutoff, fs, order=5)
    pitch_filtered = butter_lowpass_filter(euler_df_degrees['Pitch (degrees)'], cutoff, fs, order=5)
    yaw_filtered2 = butter_lowpass_filter(euler_df_degrees2['Yaw (degrees)'], cutoff, fs, order=5)

    # if (plotdiagrams):
    #     plt.figure(figsize=(12, 6))
    #     plt.plot(euler_df_degrees.index, euler_df_degrees['Yaw (degrees)'], label='Original Yaw', linewidth=1, alpha=0.5)
    #     plt.plot(euler_df_degrees.index, yaw_filtered, label='Filtered Yaw', linewidth=2)
    #     plt.xlabel('Timestamp')
    #     plt.ylabel('Yaw (degrees)')
    #     plt.title('Yaw Signal Filtering')
    #     plt.legend()
    #     plt.show()

    peaks, _ = find_peaks(pitch_filtered)

    valleys, _ = find_peaks(-pitch_filtered)



    print("peaks ", peaks)
    print("valleys ", valleys)
    if(len(peaks) == 0):
        return 0
    if(len(valleys) == 0):
        return 0

    if valleys[0] > peaks[0]:
        peaks = peaks[1:]  
    if peaks[-1] < valleys[-1]:
        valleys = valleys[:-1]  
        
    movement_pairs = []

    for i in range(min(len(peaks), len(valleys))):
        movement_pairs.append((valleys[i], peaks[i]))

    print("Movement pairs (as index positions):", movement_pairs)

    
    # if (plotdiagrams):
    #     plt.figure(figsize=(12, 6))
    #     plt.plot(yaw_filtered, label='Filtered Yaw', linewidth=1)

    #     plt.plot(peaks, yaw_filtered[peaks], "x", label='Maxima')
    #     plt.plot(valleys, yaw_filtered[valleys], "o", label='Minima')

    #     plt.xlabel('Sample index')
    #     plt.ylabel('Yaw (degrees)')
    #     plt.title('Yaw Signal with Detected Movements')
    #     plt.legend()
    #     plt.show()

    movement_ranges = []

    for valley, peak in movement_pairs:
        movement_range = pitch_filtered[peak] - pitch_filtered[valley]
        movement_ranges.append(movement_range)

    for i, movement_range in enumerate(movement_ranges):
        print(f"Movement {i+1}: Range = {movement_range:.2f} degrees")
    significant_movements = [(pair, mrange) for pair, mrange in zip(movement_pairs, movement_ranges) if mrange >= 10]

    filtered_pairs = [pair for pair, range in significant_movements]
    filtered_ranges = [mrange for pair, mrange in significant_movements]
    
    movement_details = []
    for i, (pair, mrange) in enumerate(significant_movements):
        print(f"Significant Movement {i+1}: Pair = {pair}, Range = {mrange:.2f} degrees")

        movement_detail = f"Significant Movement {i+1}: Pair = {pair}, Range = {mrange:.2f} degrees"
        print(movement_detail)
        movement_details.append(movement_detail)  # Append to list

    movement_durations = []
    for start, end in filtered_pairs:
        start_time = df_Limu1.iloc[start].name
        end_time = df_Limu1.iloc[end].name
        duration = (end_time - start_time).total_seconds()
        print(duration)
        movement_durations.append(duration)
        print(movement_durations)



    total_duration_seconds = (df_Limu1.index[-1] - df_Limu1.index[0]).total_seconds()
    print(total_duration_seconds)
    if (total_duration_seconds > 0):
        pace = len(filtered_pairs) / total_duration_seconds  # Movements per second
    else:
        pace = -1

    if (len(filtered_ranges) > 0):
        mean_range = np.mean(filtered_ranges)
        std_range = np.std(filtered_ranges, ddof=1) 
    else:
        mean_range = -1
        std_range = -1

    if (len(movement_durations) > 0):
        mean_duration = np.mean(movement_durations)
        std_duration = np.std(movement_durations, ddof=1)
    else:
        mean_duration = -1
        std_duration = -1        

   
#    IMU2 BACK
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

    significant_movements2 = [(pair2, mrange2) for pair2, mrange2 in zip(movement_pairs2, movement_ranges2) if mrange2>= 10]

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

    if len(filtered_pairs2) > 0:
        print("****************Why were you standing up?************************")


    metrics_data = {
        "total_metrics": {
           "***************LIMU1- HEAD*************":{
            "number_of_movements": int(len(filtered_pairs)),
            "pace_movements_per_second": float(pace),
            "mean_movement_range_degrees": float((mean_range)),
            "std_movement_range_degrees": float(std_range),
            "mean_movement_duration_seconds": float(mean_duration),
            "std_movement_duration_seconds": float(std_duration),
            "Degrees per movement": movement_details,
            "Exersice_duration" : total_duration_seconds,
            "movement_duration": movement_durations
        },
            "***************LIMU2- BACK*************":{
            "number_of_movements": int(len(filtered_pairs2)),
            "pace_movements_per_second": float(pace2)
        }
        }
        }
    

    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{datetime_string}_VOR_Vertical_metrics.txt"

    # Save the metrics to a file
    save_metrics_to_txt(metrics_data, filename)

    return json.dumps(metrics_data, indent=4)

    
def save_metrics_to_txt(metrics, file_path):
    main_directory = "Sitting Metrics Data"
    sub_directory = "VOR_Vertical Metrics Data"

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


