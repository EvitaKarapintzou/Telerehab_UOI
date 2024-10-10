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
      
#     Interpolate IMU data (w, x, y, z) between starttime and endtime into N samples.

#     Parameters:
#     imu_data (list of lists): The IMU data in format [time, w, x, y, z, _, _].
#     starttime (float): The start time for interpolation.
#     endtime (float): The end time for interpolation.
#     N (int): Number of samples to interpolate.

#     Returns:
#     list of lists: Interpolated IMU data with N entries.
      
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
    

    dt1 = 0 
    dt2 = 0
    dt3 = 0
    dt4 = 0
    
    if(len(Limu1) > 0 ):
        dt1 = float(Limu1[-1][0]) - float(Limu1[0][1]);
    if(len(Limu2) > 0 ):
        dt2 = float(Limu2[-1][0]) - float(Limu2[0][1]);
    if(len(Limu3) > 0 ):
        dt3 = float(Limu3[-1][0]) - float(Limu3[0][1]);
    # if(len(Limu4) > 0 ):
    #     dt4 = float(Limu4[-1][0]) - float(Limu4[0][1]);

    mean = statistics.mean([dt1, dt2, dt3, dt4])
    std = statistics.stdev([dt1, dt2, dt3, dt4])

    Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    # Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    if len(Limu1) > 0 and len(Limu2) > 0 and len(Limu3) > 0:
        returnedJson = getMetricsForwardReach(Limu1, Limu2, Limu3, False) 
        return returnedJson

def getMetricsForwardReach(Limu1, Limu2, Limu3, plotdiagrams):
   
    columns = ['Timestamp', 'elapsed(time)',  'W(number)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu1 = pd.DataFrame(Limu1, columns=columns)
    df_Limu1['elapsed(time)'] = pd.to_datetime(df_Limu1['elapsed(time)'], unit='ms')
    df_Limu1 = df_Limu1.sort_values(by='elapsed(time)')
    df_Limu1.set_index('elapsed(time)', inplace=True)
    
    #Limu2
    df_Limu2 = pd.DataFrame(Limu2, columns=columns)
    df_Limu2['elapsed(time)'] = pd.to_datetime(df_Limu2['elapsed(time)'], unit='ms')
    df_Limu2 = df_Limu2.sort_values(by='elapsed(time)')
    df_Limu2.set_index('elapsed(time)', inplace=True)

    #Limu3
    df_Limu3 = pd.DataFrame(Limu3, columns=columns)
    df_Limu3['elapsed(time)'] = pd.to_datetime(df_Limu3['elapsed(time)'], unit='ms')
    df_Limu3 = df_Limu3.sort_values(by='elapsed(time)')
    df_Limu3.set_index('elapsed(time)', inplace=True)

    # if (plotdiagrams):
    #     plt.figure(figsize=(10, 6))
    #     plt.xlabel('Timestamp')
    #     plt.ylabel('Quaternion Components')
    #     plt.title('Quaternion Components (W, X, Y, Z) over Time')
    #     plt.legend()
    #     plt.xticks(rotation=45)
    #     plt.tight_layout()

    #     plt.savefig('quaternion_components_plot!!!!!!!.png')
    #     #plt.show()
    
    
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
   

    quaternions3 = df_Limu3[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
    rotations3 = R.from_quat(quaternions3)
    euler_angles3 = rotations3.as_euler('xyz', degrees=False)
    euler_df3 = pd.DataFrame(euler_angles3, columns=['Roll (rad)', 'Pitch (rad)', 'Yaw (rad)'])
    euler_angles_degrees3 = rotations3.as_euler('xyz', degrees=True)
    euler_df_degrees3 = pd.DataFrame(euler_angles_degrees3, columns=['Roll (degrees)', 'Pitch (degrees)', 'Yaw (degrees)'])
   
    
    # if (plotdiagrams):
    #     plt.figure(figsize=(12, 8))
    #     plt.plot(euler_df_degrees.index, euler_df_degrees['Roll (degrees)'], label='Roll', linewidth=1)
    #     plt.plot(euler_df_degrees.index, euler_df_degrees['Pitch (degrees)'], label='Pitch', linewidth=1)
    #     plt.plot(euler_df_degrees.index, euler_df_degrees['Yaw (degrees)'], label='Yaw', linewidth=1)

    #     plt.xlabel('Timestamp')
    #     plt.ylabel('Euler Angles (degrees)')
    #     plt.title('Euler Angles (Roll, Pitch, Yaw) over Time')
    #     plt.legend()
    #     plt.xticks(rotation=45)
    #     plt.tight_layout()  
    #     plt.show()

    quaternions_df1 = df_Limu1;
    quaternions_df2 = df_Limu2;
    quaternions_df3 = df_Limu3;

    fs = 50
    cutoff = 0.5

        # Apply the filter to the Yaw data
    W_filtered1 = butter_lowpass_filter(quaternions_df1['W(number)'], cutoff, fs, order=5)
    Y_filtered1 = butter_lowpass_filter(quaternions_df1['Y (number)'], cutoff, fs, order=5)

    W_filtered2 = butter_lowpass_filter(quaternions_df2['W(number)'], cutoff, fs, order=5)
    Y_filtered2 = butter_lowpass_filter(quaternions_df2['Y (number)'], cutoff, fs, order=5)
    
    W_filtered3 = butter_lowpass_filter(quaternions_df3['W(number)'], cutoff, fs, order=5)
    Y_filtered3 = butter_lowpass_filter(quaternions_df3['Y (number)'], cutoff, fs, order=5)

    # # Plotting the original and filtered signals
    # plt.figure(figsize=(12, 6))
    # plt.plot(quaternions_df1.index, quaternions_df1['W(number)'], label='W', linewidth=1, alpha=0.5)
    # plt.plot(quaternions_df1.index, W_filtered, label='Filtered W', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('W(number)')
    # plt.title('W Signal filtering Filtering')
    # plt.legend()
    # plt.show()

        # Calculate the magnitude of movement considering both yaw and roll
    movement_magnitude1 = np.sqrt(np.square(W_filtered1) + np.square(Y_filtered1))
    movement_magnitude2 = np.sqrt(np.square(W_filtered2) + np.square(Y_filtered2))
    movement_magnitude3 = np.sqrt(np.square(W_filtered3) + np.square(Y_filtered3))

    # # Plot the combined metric over time
    # plt.figure(figsize=(12, 6))
    # plt.plot(quaternions_df1.index, movement_magnitude, label='Movement Magnitude', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('Magnitude of Movement')
    # plt.title('Combined X and Z Movement Magnitude')
    # plt.legend()
    # plt.show()

    
#IMU1 RIGHT
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

    print("Movement pairs (as index positions): ", movement_pairs1)

    # if (plotdiagrams):
    #     plt.figure(figsize=(12, 6))
    #     plt.plot(movement_magnitude, label='movement_magnitude', linewidth=1)
    #     # Plot peaks and valleys
    #     plt.plot(peaks, movement_magnitude[peaks],    x   , label='Maxima')
    #     plt.plot(valleys, movement_magnitude[valleys],    o   , label='Minima')
    #     plt.xlabel('Sample index')
    #     plt.ylabel('movement_magnitude')
    #     plt.title('Fused W-Y signal with Detected Movements')
    #     plt.legend()
    #     plt.show()

    movement_ranges_yaw1 = []
    movement_ranges_roll1 = []

    for valley1, peak1 in movement_pairs1:
            yaw_range1 = abs(W_filtered1[peak1] - W_filtered1[valley1])
            movement_ranges_yaw1.append(yaw_range1)
            
            roll_range1 = abs(Y_filtered1[peak1] - Y_filtered1[valley1])
            movement_ranges_roll1.append(roll_range1)

    combined_movement_ranges1 = [np.sqrt(yaw1**2 + roll1**2) for yaw1, roll1 in zip(movement_ranges_yaw1, movement_ranges_roll1)]

    for i, (yaw_range1, roll_range1) in enumerate(zip(movement_ranges_yaw1, movement_ranges_roll1)):
            combined_range1 = np.sqrt(yaw_range1**2 + roll_range1**2)
            print(f"MovementRight {i+1}: Yaw Range Right = {yaw_range1:.2f} degrees, Roll Range Right = {roll_range1:.2f} degrees, Combined Range Right= {combined_range1:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements1 = [(pair1, yaw1, roll1, np.sqrt(yaw1**2 + roll1**2)) for pair1, yaw1, roll1 in zip(movement_pairs1, movement_ranges_yaw1, movement_ranges_roll1) if np.sqrt(yaw1**2 + roll1**2) >= 0.01]

        # Separate the filtered pairs and combined ranges again if needed
    filtered_pairs1 = [item[0] for item in significant_movements1]
    filtered_combined_ranges1 = [item[3] for item in significant_movements1]

       # Print the significant movements and their combined ranges
    for i, (_, _, _, combined_range1) in enumerate(significant_movements1):
            print(f"Significant Movement Head {i+1}: Combined Range Head = {combined_range1:.2f} degrees")

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

    
#*******************LIMU2 LEFT*****************
#IMU1 RIGHT
    peaks2, _ = find_peaks(movement_magnitude2)
    valleys2, _ = find_peaks(-movement_magnitude2)
    print("peaks Left IMU ", peaks1)
    print("valleys Left IMU", valleys1)
    
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

    print("Movement pairs (as index positions): ", movement_pairs2)

    movement_ranges_yaw2 = []
    movement_ranges_roll2 = []

    for valley2, peak2 in movement_pairs2:
            yaw_range2 = abs(W_filtered2[peak2] - W_filtered2[valley2])
            movement_ranges_yaw2.append(yaw_range2)
            
            roll_range2 = abs(Y_filtered2[peak2] - Y_filtered2[valley2])
            movement_ranges_roll2.append(roll_range2)

    combined_movement_ranges2 = [np.sqrt(yaw2**2 + roll2**2) for yaw2, roll2 in zip(movement_ranges_yaw2, movement_ranges_roll2)]

    for i, (yaw_range2, roll_range2) in enumerate(zip(movement_ranges_yaw2, movement_ranges_roll2)):
            combined_range2 = np.sqrt(yaw_range2**2 + roll_range2**2)
            print(f"MovementLeft {i+1}: Yaw Range Left = {yaw_range2:.2f} degrees, Roll Range Left = {roll_range2:.2f} degrees, Combined Range Right= {combined_range2:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements2 = [(pair2, yaw2, roll2, np.sqrt(yaw2**2 + roll2**2)) for pair2, yaw2, roll2 in zip(movement_pairs2, movement_ranges_yaw2, movement_ranges_roll2) if np.sqrt(yaw2**2 + roll2**2) >= 0.01]

        # Separate the filtered pairs and combined ranges again if needed
    filtered_pairs2 = [item[0] for item in significant_movements2]
    filtered_combined_ranges2 = [item[3] for item in significant_movements2]

       # Print the significant movements and their combined ranges
    for i, (_, _, _, combined_range2) in enumerate(significant_movements2):
            print(f"Significant Movement LEFT {i+1}: Combined Range LEFT = {combined_range2:.2f} degrees")

        # Calculate durations for significant movements using timestamps
    movement_durations2 = []

   
    for start, end in filtered_pairs1:
        start_time2 = df_Limu2.iloc[start].name  # Assuming the DataFrame index is datetime or similar
        end_time2 = df_Limu2.iloc[end].name
        duration2 = (end_time2 - start_time2).total_seconds()
        movement_durations2.append(duration2)

    # Calculate pace: total number of movements divided by the total observation period in seconds
    total_duration_seconds2 = (df_Limu2.index[-1] - df_Limu2.index[0]).total_seconds()
    pace2 = len(filtered_pairs2) / total_duration_seconds2  # Movements per second

    # Calculate mean and STD for combined ranges and durations
    mean_combined_range2 = np.mean(filtered_combined_ranges2)
    std_combined_range2= np.std(filtered_combined_ranges2, ddof=1)  # ddof=1 for sample standard deviation

    mean_duration2 = np.mean(movement_durations2)
    std_duration2 = np.std(movement_durations2, ddof=1)  # ddof=1 for sample standard deviation    

    #*********************LIMU3 BACK*****************

    #IMU1 RIGHT
    peaks3, _ = find_peaks(movement_magnitude3)
    valleys3, _ = find_peaks(-movement_magnitude3)
    print("peaks Back IMU ", peaks3)
    print("valleys Back IMU", valleys3)
    
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

    print("Movement pairs (as index positions): ", movement_pairs3)

    # if (plotdiagrams):
    #     plt.figure(figsize=(12, 6))
    #     plt.plot(movement_magnitude, label='movement_magnitude', linewidth=1)
    #     # Plot peaks and valleys
    #     plt.plot(peaks, movement_magnitude[peaks],    x   , label='Maxima')
    #     plt.plot(valleys, movement_magnitude[valleys],    o   , label='Minima')
    #     plt.xlabel('Sample index')
    #     plt.ylabel('movement_magnitude')
    #     plt.title('Fused W-Y signal with Detected Movements')
    #     plt.legend()
    #     plt.show()

    movement_ranges_yaw3 = []
    movement_ranges_roll3 = []

    for valley3, peak3 in movement_pairs3:
            yaw_range3 = abs(W_filtered3[peak3] - W_filtered3[valley3])
            movement_ranges_yaw3.append(yaw_range3)
            
            roll_range3 = abs(Y_filtered3[peak3] - Y_filtered3[valley3])
            movement_ranges_roll3.append(roll_range3)

    combined_movement_ranges3 = [np.sqrt(yaw3**2 + roll3**2) for yaw3, roll3 in zip(movement_ranges_yaw3, movement_ranges_roll3)]

    for i, (yaw_range3, roll_range3) in enumerate(zip(movement_ranges_yaw3, movement_ranges_roll3)):
            combined_range3 = np.sqrt(yaw_range3**2 + roll_range3**2)
            print(f"MovementBack {i+1}: Yaw Range Back = {yaw_range3:.2f} degrees, Roll Range Back = {roll_range3:.2f} degrees, Combined Range Back= {combined_range3:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements3 = [(pair3, yaw3, roll3, np.sqrt(yaw3**2 + roll3**2)) for pair3, yaw3, roll3 in zip(movement_pairs3, movement_ranges_yaw3, movement_ranges_roll3) if np.sqrt(yaw3**2 + roll3**2) >= 0.01]

        # Separate the filtered pairs and combined ranges again if needed
    filtered_pairs3 = [item[0] for item in significant_movements3]
    filtered_combined_ranges3 = [item[3] for item in significant_movements3]

       # Print the significant movements and their combined ranges
    for i, (_, _, _, combined_range3) in enumerate(significant_movements3):
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


    symmetry_index = (mean_combined_range1 - mean_combined_range2) / ((mean_combined_range1 + mean_combined_range2) / 2) #if (mean_combined_range1 + mean_combined_range2) != 0 else 0
    peak_acceleration1 = np.max(movement_magnitude1) #if len(movement_magnitude1) > 0 else 0
    peak_acceleration2 = np.max(movement_magnitude2) #if len(movement_magnitude2) > 0 else 0


    metrics_data = {
            "total_metrics": {
             "***************LIMU1*************":{
            "number_of_movements": int(len(filtered_pairs1)),
            "pace_movements_per_second": float(pace1),
            "mean_combined_range_degrees": float(mean_combined_range1),
            "std_combined_range_degrees": float(std_combined_range1),
            "mean_duration_seconds": float(mean_duration1),
            "std_duration_seconds": float(std_duration1),
            "symmetry": float(symmetry_index),
            "acceleration1": float(peak_acceleration1),
            "Exercise duration": max(total_duration_seconds1,total_duration_seconds2, total_duration_seconds3)
             },
             "***************LIMU2*************":{
            "number_of_movements": int(len(filtered_pairs2)),
            "pace_movements_per_second": float(pace2),
            "mean_combined_range_degrees": float(mean_combined_range2),
            "std_combined_range_degrees": float(std_combined_range2),
            "mean_duration_seconds": float(mean_duration2),
            "std_duration_seconds": float(std_duration2),
            "symmetry": float(symmetry_index),
            "acceleration2": float(peak_acceleration2),
             },
             "***************LIMU3*************":{
            "number_of_movements": int(len(filtered_pairs3)),
            "pace_movements_per_second": float(pace3),
            "mean_combined_range_degrees": float(mean_combined_range3),
            "std_combined_range_degrees": float(std_combined_range3),
            "mean_duration_seconds": float(mean_duration3),
            "std_duration_seconds": float(std_duration3)
         }
        }
    }  
    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{datetime_string}_ForwardReach_metrics.txt"

    # Save the metrics to a file
    save_metrics_to_txt(metrics_data, filename)

    return json.dumps(metrics_data, indent=4)

    
def save_metrics_to_txt(metrics, file_path):
    main_directory = "Standing Metrics Data"
    sub_directory = "ForwardReach Metrics Data"

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
         
