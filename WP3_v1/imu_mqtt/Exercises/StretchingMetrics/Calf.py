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
    plt.show()


# def interpolate_imu_data(imu_data, starttime, endtime, N):
#     """
#     Interpolate IMU data (w, x, y, z) between starttime and endtime into N samples.

#     Parameters:
#     imu_data (list of lists): The IMU data in format [time, w, x, y, z, _, _].
#     starttime (float): The start time for interpolation.
#     endtime (float): The end time for interpolation.
#     N (int): Number of samples to interpolate.

#     Returns:
#     list of lists: Interpolated IMU data with N entries.
#     """
#     # Convert imu_data to a NumPy array for easier slicing
#     imu_data_np = np.array(imu_data)

#     # Filter data to only include entries within starttime and endtime
#     filtered_data = imu_data_np[(imu_data_np[:,0] >= starttime) & (imu_data_np[:,0] <= endtime)]

#     # Extract time and quaternion components
#     times = filtered_data[:, 0]
#     # quaternions = filtered_data[:, 1:7]  # Assuming w, x, y, z are in columns 1-4
#     linear = filtered_data[:, 1:6]

#     # Generate N evenly spaced new timestamps between starttime and endtime
#     new_times = np.linspace(starttime, endtime, N)

#     # Initialize a list to hold interpolated data
#     interpolated_data = []

#     # Interpolate each quaternion component
#     for i in range(6):  # For  x, y, z
#         interp_func = interp1d(times, linear[:, i], kind='linear')
#         interpolated_component = interp_func(new_times)
#         interpolated_data.append(interpolated_component)

#     # Transpose and combine the interpolated data with new timestamps
#     interpolated_data = np.array(interpolated_data).T
#     interpolated_data_with_time = np.column_stack((new_times, interpolated_data))

#     return interpolated_data_with_time.tolist()

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
        print(item)
        t = item[2:-1]
        if ',' in t:
            t = t.split(',')
        else:
            t = t.split(' ')
        if "number" not in t:
            A.append([t[-6],t[-4],t[-3],t[-2],t[-1]])
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
    #Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    if len(Limu1) > 0 and len(Limu2) > 0 and len(Limu3) > 0:
        returnedJson = getMetricsStretchingNew03(Limu1, Limu2, Limu3, False) 
        return returnedJson
    
def getMetricsStretchingNew03(Limu1, Limu2, Limu3, plotdiagrams):

    # linear1 = df_Limu1[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    # linear1_df = df_Limu1
    # linear2 = df_Limu2[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    # linear2_df = df_Limu2

    
    # if plotdiagrams:
    #     # Adjust this section to plot both Limu1 and Limu2 data
    #     plt.figure(figsize=(12, 6))
    #     plt.plot(linear1_df.index, movement_magnitude_1, label='Limu1 Movement Magnitude', linewidth=2)
    #     plt.plot(linear2_df.index, movement_magnitude_2, label='Limu2 Movement Magnitude', linewidth=2, linestyle='--')
    #     plt.xlabel('Timestamp')
    #     plt.ylabel('Magnitude of Movement')
    #     plt.title('Combined X and Z Movement Magnitude for Limu1 and Limu2')
    #     plt.legend()
    #     plt.show()

    #Limu1
    columns = ['Timestamp', 'elapsed(time)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu1 = pd.DataFrame(Limu1, columns=columns)
    df_Limu1['Timestamp'] = pd.to_datetime(df_Limu1['Timestamp'], unit='ms')
    df_Limu1 = df_Limu1.sort_values(by='Timestamp')
    df_Limu1.set_index('Timestamp', inplace=True)
    
    #Limu2
    df_Limu2 = pd.DataFrame(Limu2, columns=columns)
    df_Limu2['Timestamp'] = pd.to_datetime(df_Limu2['Timestamp'], unit='ms')
    df_Limu2 = df_Limu2.sort_values(by='Timestamp')
    df_Limu2.set_index('Timestamp', inplace=True)

    #Limu3
    df_Limu3 = pd.DataFrame(Limu3, columns=columns)
    df_Limu3['Timestamp'] = pd.to_datetime(df_Limu3['Timestamp'], unit='ms')
    df_Limu3 = df_Limu3.sort_values(by='Timestamp')
    df_Limu3.set_index('Timestamp', inplace=True)
    
    # quaternions3 = df_Limu3[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    # rotations3 = R.from_quat(quaternions3)
    # euler_angles3 = rotations3.as_euler('xyz', degrees=False)
    # euler_df3 = pd.DataFrame(euler_angles3, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    # euler_angles_degrees3 = rotations3.as_euler('xyz', degrees=True)
    # euler_df_degrees3 = pd.DataFrame(euler_angles_degrees3, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])
   
    # quaternions_df3 = df_Limu3;


    # W_filtered3 = butter_lowpass_filter(quaternions_df3['W(number)'], cutoff, fs, order=5)
    # Y_filtered3 = butter_lowpass_filter(quaternions_df3['Y (number)'], cutoff, fs, order=5)



    # start_time = df_Limu1.index.min()
    # end_time = df_Limu1.index.max()
    # interval_length = pd.Timedelta(seconds=5)
    
    # current_time = start_time
    # while current_time + interval_length <= end_time:
    #     interval_end_time = current_time + interval_length
        
    #     # Filter data within the current interval for both datasets
    #     interval_data1 = df_Limu1.loc[current_time:interval_end_time]
    #     interval_data2 = df_Limu2.loc[current_time:interval_end_time]

    #     # Calculate metrics for the interval (you can implement your metric calculation here)
    #     metrics = getMetricsGaitNew02(interval_data1, interval_data2)  # Placeholder for the real calculation function

   

    # if (plotdiagrams):
    #     plt.figure(figsize=(10, 6))
    #     plt.xlabel('Timestamp')
    #     plt.ylabel('Linear Components')
    #     plt.title('Linear Components (X, Y, Z) over Time')
    #     plt.legend()
    #     plt.xticks(rotation=45)
    #     plt.tight_layout()

    #     plt.savefig('linear_components_plot!!!!!!!.png')
    #     plt.show()
    
    linear_df1 = df_Limu1;
    linear_df2 = df_Limu2;
    linear_df3 = df_Limu3;
   
    fs = 30
    cutoff = 0.425

        # Apply the filter to the Yaw data
    Z_filtered1 = butter_lowpass_filter(linear_df1['Z (number)'], cutoff, fs, order=5)
    X_filtered1 = butter_lowpass_filter(linear_df1['X(number)'], cutoff, fs, order=5)
    Y_filtered1 = butter_lowpass_filter(linear_df1['Y (number)'], cutoff, fs, order=5)

    Z_filtered2 = butter_lowpass_filter(linear_df2['Z (number)'], cutoff, fs, order=5)
    X_filtered2 = butter_lowpass_filter(linear_df2['X(number)'], cutoff, fs, order=5)
    Y_filtered2 = butter_lowpass_filter(linear_df2['Y (number)'], cutoff, fs, order=5)

    Z_filtered3 = butter_lowpass_filter(linear_df3['Z (number)'], cutoff, fs, order=5)
    X_filtered3 = butter_lowpass_filter(linear_df3['X(number)'], cutoff, fs, order=5)
    Y_filtered3 = butter_lowpass_filter(linear_df3['Y (number)'], cutoff, fs, order=5)

    # # Plotting the original and filtered signals
    # plt.figure(figsize=(14, 8))
    # plt.plot(linear_df1.index, linear_df1['X(number)'], label='X -Right Leg', linewidth=1, alpha=0.5)
    # plt.plot(linear_df1.index, X_filtered1, label='Filtered X-Right Leg', linewidth=2)
    # plt.plot(linear_df2.index, linear_df2['X(number)'], label='X -Left Leg', linewidth=1, alpha=0.5)
    # plt.plot(linear_df2.index, X_filtered2, label='Filtered X -Left Leg', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('X(number)')
    # plt.title('X Signal Filtering')
    # plt.legend()
    # plt.show()

    # # Plotting the original and filtered signals
    # plt.figure(figsize=(12, 6))
    # plt.plot(quaternions_df2.index, quaternions_df2['Z (number)'], label='Z', linewidth=1, alpha=0.5)
    # plt.plot(quaternions_df2.index, Z_filtered2, label='Filtered Z', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('Z(number)')
    # plt.title('Z Signal filtering Filtering for IMU2')
    # plt.legend()
    # plt.show()

        # Calculate the magnitude of movement considering both yaw and roll
    movement_magnitude1 = np.sqrt(np.square(X_filtered1) + np.square(Y_filtered1) + np.square(Z_filtered1))
    movement_magnitude2 = np.sqrt(np.square(X_filtered2) + np.square(Y_filtered2) + np.square(Z_filtered2))
    movement_magnitude3 = np.sqrt(np.square(X_filtered3) + np.square(Y_filtered3) + np.square(Z_filtered3))

    # movement_magnitude1 = np.sqrt(np.square(X_filtered1) + np.square(Z_filtered1))
    # movement_magnitude2 = np.sqrt(np.square(X_filtered2) + np.square(Z_filtered2))


    # # Plot the combined metric over time
    # plt.figure(figsize=(12, 6))
    # plt.plot(linear_df1.index, movement_magnitude, label='Movement Magnitude-Right Leg', linewidth=2)
    # plt.plot(linear_df2.index, movement_magnitude2, label='Movement Magnitude-Left Leg', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('Magnitude of Movement')
    # plt.title('Combined Y and Z Movement Magnitude')
    # plt.legend()
    # plt.show()

    #IMU1
    peaks1, _ = find_peaks(movement_magnitude1)
    valleys1, _ = find_peaks(-movement_magnitude1)

    print("peaks Right IMU ", peaks1)
    print("valleys Right IMU", valleys1)
    if(len(peaks1) == 0):
        return 0
    if(len(valleys1) == 0):
        return 0

    if valleys1[0] > peaks1[0]:
        peaks1 = peaks1[1:]  
    if peaks1[-1] < valleys1[-1]:
        valleys1 = valleys1[:-1]  
    
    movement_pairs1 = []

    for i in range(min(len(peaks1), len(valleys1))):
        movement_pairs1.append((valleys1[i], peaks1[i]))

    print("Movement pairs for Right Leg (as index positions):", movement_pairs1)

    # #For evaluation for XYZ peaks and valleys
    # plt.figure(figsize=(12, 6))
    # plt.plot(linear_df1.index, movement_magnitude1, label='Movement Magnitude - Right Leg', linewidth=2)
    # plt.scatter(linear_df1.index[peaks1], movement_magnitude1[peaks1], c='red', label='Peaks', marker='x')
    # plt.scatter(linear_df1.index[valleys1], movement_magnitude1[valleys1], c='blue', label='Valleys', marker='o')
    # plt.xlabel('Timestamp')
    # plt.ylabel('Magnitude of Movement')
    # plt.title('Combined XYZ Movement Magnitude with Detected Peaks and Valleys')
    # plt.legend()
    # plt.show()
    

    #IMU2
    peaks2, _ = find_peaks(movement_magnitude2)
    valleys2, _ = find_peaks(-movement_magnitude2)

    print("peaks Left IMU ", peaks2)
    print("valleys Left IMU", valleys2)
    if(len(peaks2) == 0):
        return 0
    if(len(valleys2) == 0):
        return 0

    if valleys2[0] > peaks2[0]:
        peaks2 = peaks2[1:]  
    if peaks2[-1] < valleys2[-1]:
        valleys2 = valleys2[:-1]  
        
    movement_pairs2 = []

    for i in range(min(len(peaks2), len(valleys2))):
        movement_pairs2.append((valleys2[i], peaks2[i]))

    print("Movement pairs for Left Leg (as index positions):", movement_pairs2)

    # if (plotdiagrams):
    #     plt.figure(figsize=(12, 6))
    #     plt.plot(movement_magnitude, label='movement_magnitude', linewidth=1)
    #     # Plot peaks and valleys
    #     plt.plot(peaks, movement_magnitude[peaks], "x", label='Maxima')
    #     plt.plot(valleys, movement_magnitude[valleys], "o", label='Minima')
    #     plt.xlabel('Sample index')
    #     plt.ylabel('movement_magnitude')
    #     plt.title('Fused W-Y signal with Detected Movements')
    #     plt.legend()
    #     plt.show()

    #IMU3
    peaks3, _ = find_peaks(movement_magnitude3)
    valleys3, _ = find_peaks(-movement_magnitude3)

    print("peaks Left IMU ", peaks3)
    print("valleys Left IMU", valleys3)
    if(len(peaks3) == 0):
        return 0
    if(len(valleys3) == 0):
        return 0

    if valleys3[0] > peaks3[0]:
        peaks3 = peaks3[1:]  
    if peaks3[-1] < valleys3[-1]:
        valleys3 = valleys3[:-1]  
        
    movement_pairs3 = []

    for i in range(min(len(peaks3), len(valleys3))):
        movement_pairs3.append((valleys3[i], peaks3[i]))

    print("Movement pairs for Left Leg (as index positions):", movement_pairs2)

    #=============IMU1-Right Leg====================#
    movement_ranges_yaw1 = []
    movement_ranges_pitch1 = []
    movement_ranges_roll1 = []

    for valley1, peak1 in movement_pairs1:
            yaw_range1 = abs(Z_filtered1[peak1] - Z_filtered1[valley1])
            movement_ranges_yaw1.append(yaw_range1)

            pitch_range1 = abs(X_filtered1[peak1] - X_filtered1[valley1])
            movement_ranges_pitch1.append(pitch_range1)
            
            roll_range1 = abs(Y_filtered1[peak1] - Y_filtered1[valley1])
            movement_ranges_roll1.append(roll_range1)

    combined_movement_ranges1 = [np.sqrt(yaw1**2 + pitch1**2 + roll1**2) for yaw1, pitch1, roll1 in zip(movement_ranges_yaw1, movement_ranges_roll1, movement_ranges_pitch1)]

    for i, (yaw_range1, roll_range1, pitch_range1) in enumerate(zip(movement_ranges_yaw1, movement_ranges_roll1, movement_ranges_pitch1)):
            combined_range1 = np.sqrt(yaw_range1**2 + roll_range1**2 + pitch_range1**2)
            print(f"MovementRight {i+1}: Yaw Range Right = {yaw_range1:.2f} degrees, Pitch Range Right = {pitch_range1:.2f} degrees, Roll Range Right = {roll_range1:.2f} degrees, Combined Range Right = {combined_range1:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements1 = [(pair1, yaw1, pitch1, roll1, np.sqrt(yaw1**2 + pitch1**2 + roll1**2)) for pair1, yaw1, pitch1, roll1 in zip(movement_pairs1, movement_ranges_yaw1, movement_ranges_pitch1 ,movement_ranges_roll1) if np.sqrt(yaw1**2 + pitch1**2 + roll1**2) >= 0.01]

    filtered_pairs1 = [item[0] for item in significant_movements1]
    filtered_combined_ranges1 = [item[3] for item in significant_movements1]

        # Print the significant movements and their combined ranges
    for i, (_, _, _, _, combined_range1) in enumerate(significant_movements1):
            print(f"Significant Movement Right Leg {i+1}: Combined Range Right = {combined_range1:.2f} degrees")

        # Calculate durations for significant movements using timestamps
    movement_durations1 = []

    for start, end in filtered_pairs1:
        start_time1 = df_Limu1.iloc[start].name  # Assuming the DataFrame index is datetime or similar
        end_time1 = df_Limu1.iloc[end].name
        duration1 = (end_time1 - start_time1).total_seconds()
        movement_durations1.append(duration1)

    # Calculate pace: total number of movements divided by the total observation period in seconds
    total_duration_seconds1 = (df_Limu1.index[-1] - df_Limu1.index[0]).total_seconds()
    pace1 = len(filtered_pairs1) / total_duration_seconds1  # Movements per second

    # Calculate mean and STD for combined ranges and durations
    mean_combined_range1 = np.mean(filtered_combined_ranges1)
    std_combined_range1 = np.std(filtered_combined_ranges1, ddof=1)  # ddof=1 for sample standard deviation

    mean_duration1 = np.mean(movement_durations1)
    std_duration1 = np.std(movement_durations1, ddof=1)  # ddof=1 for sample standard deviation    


#=============IMU2-Left Leg====================#
    movement_ranges_yaw2 = []
    movement_ranges_pitch2 = []
    movement_ranges_roll2 = []

    for valley2, peak2 in movement_pairs2:
            yaw_range2 = abs(Z_filtered2[peak2] - Z_filtered2[valley2])
            movement_ranges_yaw2.append(yaw_range2)

            pitch_range2 = abs(X_filtered2[peak2] - X_filtered2[valley2])
            movement_ranges_pitch2.append(pitch_range2)
            
            roll_range2 = abs(Y_filtered2[peak2] - Y_filtered2[valley2])
            movement_ranges_roll2.append(roll_range2)

    combined_movement_ranges2 = [np.sqrt(yaw2**2 + pitch2**2 + roll2**2) for yaw2, pitch2, roll2 in zip(movement_ranges_yaw2, movement_ranges_roll2, movement_ranges_pitch2)]

    for i, (yaw_range2, roll_range2, pitch_range2) in enumerate(zip(movement_ranges_yaw2, movement_ranges_roll2, movement_ranges_pitch2)):
            combined_range2 = np.sqrt(yaw_range2**2 + roll_range2**2 + pitch_range2**2)
            print(f"MovementLeft {i+1}: Yaw Range Left = {yaw_range2:.2f} degrees, Pitch Range Left = {pitch_range2:.2f} degrees, Roll Range Left = {roll_range2:.2f} degrees, Combined Range Left = {combined_range2:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements2 = [(pair2, yaw2, pitch2, roll2, np.sqrt(yaw2**2 + pitch2**2 + roll2**2)) for pair2, yaw2, pitch2, roll2 in zip(movement_pairs2, movement_ranges_yaw2, movement_ranges_pitch2 ,movement_ranges_roll2) if np.sqrt(yaw2**2 + pitch2**2 + roll2**2) >= 0.01]

    filtered_pairs2 = [item[0] for item in significant_movements2]
    filtered_combined_ranges2 = [item[3] for item in significant_movements2]

        # Print the significant movements and their combined ranges
    for i, (_, _, _, _, combined_range2) in enumerate(significant_movements2):
            print(f"Significant Movement Left Leg {i+1}: Combined Range Left = {combined_range2:.2f} degrees")

        # Calculate durations for significant movements using timestamps
    movement_durations2 = []

    for start, end in filtered_pairs2:
        start_time2 = df_Limu2.iloc[start].name  # Assuming the DataFrame index is datetime or similar
        end_time2 = df_Limu2.iloc[end].name
        duration2 = (end_time2 - start_time2).total_seconds()
        movement_durations2.append(duration2)

    # Calculate pace: total number of movements divided by the total observation period in seconds
    total_duration_seconds2 = (df_Limu2.index[-1] - df_Limu2.index[0]).total_seconds()
    pace2 = len(filtered_pairs2) / total_duration_seconds2  # Movements per second

    # Calculate mean and STD for combined ranges and durations
    mean_combined_range2 = np.mean(filtered_combined_ranges2)
    std_combined_range2 = np.std(filtered_combined_ranges2, ddof=1)  # ddof=1 for sample standard deviation

    mean_duration2 = np.mean(movement_durations2)
    std_duration2 = np.std(movement_durations2, ddof=1)  # ddof=1 for sample standard deviation    

#=============IMU3-BACK====================#
    movement_ranges_yaw3 = []
    movement_ranges_pitch3 = []
    movement_ranges_roll3 = []

    for valley3, peak3 in movement_pairs3:
            yaw_range3 = abs(Z_filtered3[peak3] - Z_filtered3[valley3])
            movement_ranges_yaw3.append(yaw_range3)

            pitch_range3 = abs(X_filtered3[peak3] - X_filtered3[valley3])
            movement_ranges_pitch3.append(pitch_range3)
            
            roll_range3 = abs(Y_filtered3[peak3] - Y_filtered3[valley3])
            movement_ranges_roll3.append(roll_range3)

    combined_movement_ranges3 = [np.sqrt(yaw3**2 + pitch3**2 + roll3**2) for yaw3, pitch3, roll3 in zip(movement_ranges_yaw3, movement_ranges_roll3, movement_ranges_pitch3)]

    for i, (yaw_range3, roll_range3, pitch_range3) in enumerate(zip(movement_ranges_yaw3, movement_ranges_roll3, movement_ranges_pitch3)):
            combined_range3 = np.sqrt(yaw_range3**2 + roll_range3**2 + pitch_range3**2)
            print(f"MovementBack {i+1}: Yaw Range Back = {yaw_range3:.2f} degrees, Pitch Range Back = {pitch_range3:.2f} degrees, Roll Range Back = {roll_range3:.2f} degrees, Combined Range Back = {combined_range3:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements3 = [(pair3, yaw3, pitch3, roll3, np.sqrt(yaw3**2 + pitch3**2 + roll3**2)) for pair3, yaw3, pitch3, roll3 in zip(movement_pairs3, movement_ranges_yaw3, movement_ranges_pitch3 ,movement_ranges_roll3) if np.sqrt(yaw3**2 + pitch3**2 + roll3**2) >= 0.01]

    filtered_pairs3 = [item[0] for item in significant_movements3]
    filtered_combined_ranges3 = [item[3] for item in significant_movements3]

        # Print the significant movements and their combined ranges
    for i, (_, _, _, _, combined_range3) in enumerate(significant_movements3):
            print(f"Significant Movement Back {i+1}: Combined Range Back = {combined_range3:.2f} degrees")

        # Calculate durations for significant movements using timestamps
    movement_durations3 = []

    for start, end in filtered_pairs3:
        start_time3 = df_Limu3.iloc[start].name  # Assuming the DataFrame index is datetime or similar
        end_time3 = df_Limu3.iloc[end].name
        duration3 = (end_time3 - start_time3).total_seconds()
        movement_durations3.append(duration3)

    # Calculate pace: total number of movements divided by the total observation period in seconds
    total_duration_seconds3 = (df_Limu3.index[-1] - df_Limu3.index[0]).total_seconds()
    pace3 = len(filtered_pairs3) / total_duration_seconds3  # Movements per second

    # Calculate mean and STD for combined ranges and durations
    mean_combined_range3 = np.mean(filtered_combined_ranges3)
    std_combined_range3 = np.std(filtered_combined_ranges3, ddof=1)  # ddof=1 for sample standard deviation

    mean_duration3 = np.mean(movement_durations3)
    std_duration3 = np.std(movement_durations3, ddof=1)  # ddof=1 for sample standard deviation    
    peak_acceleration3 = np.max(movement_magnitude3) #if len(movement_magnitude2) > 0 else 0

    steps = min(len(movement_pairs1), len(movement_pairs2)) 

    heel_strikes_times_Right, properties1 = find_peaks(movement_magnitude1, prominence = 0.0)  # Adjust the prominence as needed
    print(heel_strikes_times_Right)
    toe_off_times_Right, properties1 = find_peaks(-movement_magnitude1, prominence = 0.0) # Adjust the prominence as needed
    print(toe_off_times_Right)
    heel_strikes_times_Left, properties2 = find_peaks(movement_magnitude2, prominence = 0.1)  # Adjust the prominence as needed
    print(heel_strikes_times_Left)
    toe_off_times_Left, properties2 = find_peaks(-movement_magnitude2, prominence = 0.1)  # Adjust the prominence as needed
    print(toe_off_times_Left)

    t1 = heel_strikes_times_Right
    t2 = heel_strikes_times_Left
    t3 = toe_off_times_Right  
    t4 = toe_off_times_Left

    t1_series = pd.Series(t1)
    print(t1_series)
    t2_series = pd.Series(t2)
    print(t2_series)
    t3_series = pd.Series(t3)
    print(t3_series)
    t4_series = pd.Series(t4)
    print(t4_series)

    # time_vector = np.linspace(0, len(linear_df1) / 100, len(Limu1))
    # plt.figure(figsize=(12, 6))
    # plt.plot(time_vector, linear_df1, label='IMU Data')

    # # Add heel strikes and toe offs to the plot
    # plt.scatter(t1, linear_df1[peaks1], color='red', label='Heel Strikes (t1)')
    # plt.scatter(t3, linear_df1[valleys1], color='blue', label='Toe Offs (t3)')
    # # plt.scatter(t2, Limu1[heel_strike2], color='green', label='Heel Strikes (t2)')
    # # plt.scatter(t4, Limu1[toe_off2], color='orange', label='Toe Offs (t4)')

    # plt.title('Detected Heel Strikes and Toe Offs Over Time')
    # plt.xlabel('Time (seconds)')
    # plt.ylabel('Sensor Data')
    # plt.legend()
    # plt.show()

    ###GAIT CYCLE###

    # Right single support time = t4|nextcycle - t2
    right_single_support_time = t4_series.shift(-1) - t2_series
    # Left single support time =  t1|nextcycle - t3
    left_single_support_time = t1_series.shift(-1) - t3_series
    # Double support time = (t4 -t1) + (t3-t2)
    double_support_time = (t4_series - t1_series) + (t3_series - t2_series)
    # Right stance phase duration = t3 -t1
    right_stance_phase_duration = t3_series - t1_series
    # Left stance phase duration =  t4|nextcycle - t2
    left_stance_phase_duration = t4_series.shift(-1) - t2_series
    # Right load response time = t4 - t1
    right_load_response_time = t4_series - t1_series
    # Right gait cycle time = t1|nextcycle - t1
    right_gait_cycle_time = t1_series.shift(-1) - t1_series
    # Left loading response time = t3 - t2
    left_load_response_time = t3_series - t2_series
    # Left gait cycle = t4|nextcycle - t4
    left_gait_cycle_time = t4_series.shift(-1) - t4_series
    # Cadence = 1/ t4|nextcycle - t1
    cadence = 1/ (t4_series.shift(-1) - t1_series)
    # Right single support time percentage over gait cycle =  Right single support time/Right gait cycle time
    right_single_support_time_percentage = (right_single_support_time / right_gait_cycle_time) * 100
    # Left single support time percentage over gait cycle = Left single support time/Right gait cycle time
    left_single_support_time_percentage = (left_single_support_time / right_gait_cycle_time) * 100
    # Double support time percentage over gait cycle =  Double support time/Right gait cycle time
    double_support_time_percentage = (double_support_time / right_gait_cycle_time) * 100
    # Right stance phase time percentage over gait cycle = Right stance phase duration/Right gait cycle time 
    right_stance_phase_percentage = (right_stance_phase_duration / right_gait_cycle_time) * 100
    # Left stance phase time percentage over gait cycle = Left stance phase duration/Right gait cycle time
    left_stance_phase_percentage = (left_stance_phase_duration / right_gait_cycle_time) * 100
    # Right loading response percentage time over gait cycle = Right load response time/Right gait cycle time
    right_loading_response_percentage = (right_load_response_time / right_gait_cycle_time) * 100
    # Left loading response percentage phase time over gait cycle = Left loading response time/Right gait cycle time
    left_loading_response_percentage = (left_load_response_time / right_gait_cycle_time) * 100

    metrics_data = {
        "total_metrics": {
             "Gait Cycle":{
                "Number of steps": int(steps/3),
                "Right Single Support Time": right_single_support_time.tolist(),
                "Left Single Support Time": left_single_support_time.tolist(),
                "Double Support Time": double_support_time.tolist(),
                "Right Stance Phase Duration": right_stance_phase_duration.tolist(),
                "Left Stance Phase Duration": left_stance_phase_duration.tolist(),
                "Right Load Response Time": right_load_response_time.tolist(),
                "Right Gait Cycle Time": right_gait_cycle_time.tolist(),
                "Left Load Response Time": left_load_response_time.tolist(),
                "Left Gait Cycle Time": left_gait_cycle_time.tolist(),
                "Cadence": cadence.tolist(),
                "Right Single Support Percentage": right_single_support_time_percentage.tolist(),
                "Left Single Support Percentage": left_single_support_time_percentage.tolist(),
                "Double Support Percentage": double_support_time_percentage.tolist(),
                "Right Stance Phase Percentage": right_stance_phase_percentage.tolist(),
                "Left Stance Phase Percentage": left_stance_phase_percentage.tolist(),
                "Right Loading Response Percentage": right_loading_response_percentage.tolist(),
                "Left Loading Response Percentage": left_loading_response_percentage.tolist()   
                            },
             "BACK METRICS":{
                "number_of_movements": int(len(filtered_pairs3)),
                "pace_movements_per_second": float(pace3),
                "mean_combined_range_degrees": float(mean_combined_range3),
                "std_combined_range_degrees": float(std_combined_range3),
                "mean_duration_seconds": float(mean_duration3),
                "std_duration_seconds": float(std_duration3),
                "acceleration1": float(peak_acceleration3),
                }
    }
    }



    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{datetime_string}_Calf_metrics.txt"

    # Save the metrics to a file
    save_metrics_to_txt(metrics_data, filename)

    return json.dumps(metrics_data, indent=4)

    
def save_metrics_to_txt(metrics, file_path):
    main_directory = "Stretching Metrics Data"
    sub_directory = "Calf Metrics Data"

    directory = os.path.join(main_directory, sub_directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
   
    full_path = os.path.join(directory, file_path)

   
    with open(full_path, 'w') as file:
        for main_key, main_value in metrics.items():
            file.write(f"{main_key}:\n")
            for key, value in main_value.items():
                file.write(f"  {key}:\n")
                for sub_key, sub_value in value.items():
                    file.write(f"    {sub_key}: {sub_value}\n")
                file.write("\n") 
         

# def calculate_correlation(metric1, metric2):
#     # Calculate the correlation between two metrics
#     correlation = metric1.corr(metric2)
#     return correlation
