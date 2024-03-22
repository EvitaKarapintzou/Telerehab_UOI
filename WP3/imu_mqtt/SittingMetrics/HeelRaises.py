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


def interpolate_imu_data(imu_data, starttime, endtime, N):
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
    
# def butter_lowpass_filter(data, cutoff, fs, order=5):
#     nyq = 0.5 * fs  
#     normal_cutoff = cutoff / nyq
#     b, a = butter(order, normal_cutoff, btype='low', analog=False)
#     y = filtfilt(b, a, data)
#     return y
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
    Limu1 = striplist(imu1)
    Limu2 = striplist(imu2)
    Limu3 = striplist(imu3)
    Limu4 = striplist(imu4)

    dt1 = 0 
    dt2 = 0
    dt3 = 0
    dt4 = 0
    
    if(len(Limu1) > 0 ):
        dt1 = float(Limu1[-1][0]) - float(Limu1[0][0]);
    if(len(Limu2) > 0 ):
        dt2 = float(Limu2[-1][0]) - float(Limu2[0][0]);
    if(len(Limu3) > 0 ):
        dt3 = float(Limu3[-1][0]) - float(Limu3[0][0]);
    if(len(Limu4) > 0 ):
        dt4 = float(Limu4[-1][0]) - float(Limu4[0][0]);

    mean = statistics.mean([dt1, dt2, dt3, dt4])
    std = statistics.stdev([dt1, dt2, dt3, dt4])

    Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    if(len(Limu1) > 0):
        returnedJson = getMetricsSittingNew03(Limu1, False) 
        return returnedJson

def getMetricsSittingNew03(Limu1, plotdiagrams):
   
    columns = ['Timestamp', 'elapsed(time)',  'W(number)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu1 = pd.DataFrame(Limu1, columns=columns)
    df_Limu1['Timestamp'] = pd.to_datetime(df_Limu1['Timestamp'])
    df_Limu1 = df_Limu1.sort_values(by='Timestamp')
    df_Limu1.set_index('Timestamp', inplace=True)
    

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
    
    quaternions = df_Limu1[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    rotations = R.from_quat(quaternions)
    euler_angles = rotations.as_euler('xyz', degrees=False)
    euler_df = pd.DataFrame(euler_angles, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    euler_angles_degrees = rotations.as_euler('xyz', degrees=True)
    euler_df_degrees = pd.DataFrame(euler_angles_degrees, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])
   
    
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

    quaternions_df1 = df_Limu1;

    fs = 50
    cutoff = 0.5

        # Apply the filter to the Yaw data
    W_filtered = butter_lowpass_filter(quaternions_df1['W(number)'], cutoff, fs, order=5)
    Y_filtered = butter_lowpass_filter(quaternions_df1['Y (number)'], cutoff, fs, order=5)

    # Plotting the original and filtered signals
    plt.figure(figsize=(12, 6))
    plt.plot(quaternions_df1.index, quaternions_df1['W(number)'], label='W', linewidth=1, alpha=0.5)
    plt.plot(quaternions_df1.index, W_filtered, label='Filtered W', linewidth=2)
    plt.xlabel('Timestamp')
    plt.ylabel('W(number)')
    plt.title('W Signal filtering Filtering')
    plt.legend()
    plt.show()

        # Calculate the magnitude of movement considering both yaw and roll
    movement_magnitude = np.sqrt(np.square(W_filtered) + np.square(Y_filtered))

    # Plot the combined metric over time
    plt.figure(figsize=(12, 6))
    plt.plot(quaternions_df1.index, movement_magnitude, label='Movement Magnitude', linewidth=2)
    plt.xlabel('Timestamp')
    plt.ylabel('Magnitude of Movement')
    plt.title('Combined X and Z Movement Magnitude')
    plt.legend()
    plt.show()

    
    peaks, _ = find_peaks(movement_magnitude)


    valleys, _ = find_peaks(-movement_magnitude)

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

    if (plotdiagrams):
        plt.figure(figsize=(12, 6))
        plt.plot(movement_magnitude, label='movement_magnitude', linewidth=1)
        # Plot peaks and valleys
        plt.plot(peaks, movement_magnitude[peaks], "x", label='Maxima')
        plt.plot(valleys, movement_magnitude[valleys], "o", label='Minima')
        plt.xlabel('Sample index')
        plt.ylabel('movement_magnitude')
        plt.title('Fused W-Y signal with Detected Movements')
        plt.legend()
        plt.show()

    movement_ranges_yaw = []
    movement_ranges_roll = []

    for valley, peak in movement_pairs:
            yaw_range = abs(W_filtered[peak] - W_filtered[valley])
            movement_ranges_yaw.append(yaw_range)
            
            roll_range = abs(Y_filtered[peak] - Y_filtered[valley])
            movement_ranges_roll.append(roll_range)

    combined_movement_ranges = [np.sqrt(yaw**2 + roll**2) for yaw, roll in zip(movement_ranges_yaw, movement_ranges_roll)]

    for i, (yaw_range, roll_range) in enumerate(zip(movement_ranges_yaw, movement_ranges_roll)):
            combined_range = np.sqrt(yaw_range**2 + roll_range**2)
            print(f"Movement {i+1}: Yaw Range = {yaw_range:.2f} degrees, Roll Range = {roll_range:.2f} degrees, Combined Range = {combined_range:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements = [(pair, yaw, roll, np.sqrt(yaw**2 + roll**2)) for pair, yaw, roll in zip(movement_pairs, movement_ranges_yaw, movement_ranges_roll) if np.sqrt(yaw**2 + roll**2) >= 0.01]

        # Separate the filtered pairs and combined ranges again if needed
    filtered_pairs = [item[0] for item in significant_movements]
    filtered_combined_ranges = [item[3] for item in significant_movements]

        # Print the significant movements and their combined ranges
    for i, (_, _, _, combined_range) in enumerate(significant_movements):
            print(f"Significant Movement {i+1}: Combined Range = {combined_range:.2f} degrees")

        # Calculate durations for significant movements using timestamps
    movement_durations = []

    # for start, end in filtered_pairs:
    #         start_time = df_Limu1.iloc[start].name
    #         end_time = df_Limu1.iloc[end].name
    #         duration = (end_time - start_time).total_seconds()
    #         movement_durations.append(duration)

    # total_duration_seconds = (df_Limu1.index[-1] - df_Limu1.index[0]).total_seconds()
    # if (total_duration_seconds > 0):
    #         pace = len(filtered_pairs) / total_duration_seconds  
    # else:
    #         pace = -1;

    # if (len(filtered_ranges) > 0):
    #         mean_range = np.mean(filtered_ranges)
    #         std_range = np.std(filtered_ranges, ddof=1) 
    # else:
    #         mean_range = -1;
    #         std_range = -1;

    # if (len(movement_durations) > 0):
    #         mean_duration = np.mean(movement_durations)
    #         std_duration = np.std(movement_durations, ddof=1)
    #     else:
    #         mean_duration = -1
    #         std_duration = -1    

    for start, end in filtered_pairs:
        start_time = df_Limu1.iloc[start].name  # Assuming the DataFrame index is datetime or similar
        end_time = df_Limu1.iloc[end].name
        duration = (end_time - start_time).total_seconds()
        movement_durations.append(duration)

    # Calculate pace: total number of movements divided by the total observation period in seconds
    total_duration_seconds = (df_Limu1.index[-1] - df_Limu1.index[0]).total_seconds()
    pace = len(filtered_pairs) / total_duration_seconds  # Movements per second

    # Calculate mean and STD for combined ranges and durations
    mean_combined_range = np.mean(filtered_combined_ranges)
    std_combined_range = np.std(filtered_combined_ranges, ddof=1)  # ddof=1 for sample standard deviation

    mean_duration = np.mean(movement_durations)
    std_duration = np.std(movement_durations, ddof=1)  # ddof=1 for sample standard deviation    

    # Output the metrics
    #print(f"Number of movements: {len(filtered_pairs)}")
    #print(f"Pace: {pace:.2f} movements per second")
    #print(f"Mean Movement Range: {mean_range:.2f} degrees, STD: {std_range:.2f}")
    #print(f"Mean Movement Duration: {mean_duration:.2f} seconds, STD: {std_duration:.2f}")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    metrics_data = {
            # "movements": [
            #     {"id": i+1, "duration_seconds": float(duration), "range_degrees": float(mrange)}
            #     for i, ((_, _), mrange, duration) in enumerate(zip(filtered_pairs, filtered_ranges, movement_durations))
            # ],
            "total_metrics": {
                "number_of_movements": int(len(filtered_pairs)),
                "pace_movements_per_second": float(pace),
                "mean_range_degrees": float(mean_combined_range),
                "std_range_degrees": float(std_combined_range),
                "mean_duration_seconds": float(mean_duration),
                "std_duration_seconds": float(std_duration)
            }
        }
        
    return json.dumps(metrics_data, indent=4)
