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

    if len(Limu1) > 0 and len(Limu2) > 0:
        returnedJson = getMetricsStandingOld04(Limu1, Limu2, False) 
        return returnedJson

def getMetricsStandingOld04(Limu1, Limu2, plotdiagrams):
   
    columns = ['Timestamp', 'elapsed(time)',  'W(number)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu1 = pd.DataFrame(Limu1, columns=columns)
    df_Limu1['Timestamp'] = pd.to_datetime(df_Limu1['Timestamp'], unit='ms')
    df_Limu1 = df_Limu1.sort_values(by='Timestamp')
    df_Limu1.set_index('Timestamp', inplace=True)
    
    # #Limu2
    # df_Limu2 = pd.DataFrame(Limu2, columns=columns)
    # df_Limu2['Timestamp'] = pd.to_datetime(df_Limu2['Timestamp'])
    # df_Limu2 = df_Limu2.sort_values(by='Timestamp')
    # df_Limu2.set_index('Timestamp', inplace=True)

#     start_time = df_Limu1.index.min()
#     end_time = df_Limu1.index.max()
#     interval_length = pd.Timedelta(seconds=5)
    
#     current_time = start_time
#     while current_time + interval_length <= end_time:
#         interval_end_time = current_time + interval_length
        
#         # Filter data within the current interval for both datasets
#         interval_data1 = df_Limu1.loc[current_time:interval_end_time]
#         interval_data2 = df_Limu2.loc[current_time:interval_end_time]
# # Calculate metrics for the interval (you can implement your metric calculation here)
#         metrics = getMetricsStandingOld04(interval_data1, interval_data2)  # Placeholder for the real calculation function

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
    columns = ['Timestamp', 'elapsed(time)',  'W(number)', 'X(number)', 'Y (number)', 'Z (number)']
    df_Limu2 = pd.DataFrame(Limu2, columns=columns)
    df_Limu2['Timestamp'] = pd.to_datetime(df_Limu2['Timestamp'], unit='ms')
    df_Limu2 = df_Limu2.sort_values(by='Timestamp')
    df_Limu2.set_index('Timestamp', inplace=True)
    

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
    # quaternions_df2 = df_Limu2;

    fs = 50
    cutoff = 0.5

        # Apply the filter to the Yaw data
    W_filtered1 = butter_lowpass_filter(quaternions_df1['W(number)'], cutoff, fs, order=5)
    Y_filtered1 = butter_lowpass_filter(quaternions_df1['Y (number)'], cutoff, fs, order=5)

    # W_filtered2 = butter_lowpass_filter(quaternions_df2['W(number)'], cutoff, fs, order=5)
    # Y_filtered2 = butter_lowpass_filter(quaternions_df2['Y (number)'], cutoff, fs, order=5)
    # Z_filtered2 = butter_lowpass_filter(quaternions_df2['Z (number)'], cutoff, fs, order=5)

    
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
    # movement_magnitude2 = np.sqrt(np.square(W_filtered2) + np.square(Y_filtered2))

    yaw_filtered = butter_lowpass_filter(euler_df_degrees2['Yaw (degrees)'], cutoff, fs, order=5)
    # # Plot the combined metric over time
    # plt.figure(figsize=(12, 6))
    # plt.plot(quaternions_df1.index, movement_magnitude1, label='Movement Magnitude', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('Magnitude of Movement')
    # plt.title('Combined X and Z Movement Magnitude')
    # plt.legend()
    # plt.show()

    # # Plot the combined metric over time
    # plt.figure(figsize=(12, 6))
    # plt.plot(quaternions_df1.index, movement_magnitude2, label='Movement Magnitude', linewidth=2)
    # plt.xlabel('Timestamp')
    # plt.ylabel('Magnitude of Movement')
    # plt.title('Combined X and Z Movement Magnitude')
    # plt.legend()
    # plt.show()

    #IMU1 HEAD

    peaks1, _ = find_peaks(movement_magnitude1)
    valleys1, _ = find_peaks(-movement_magnitude1)

   
    print("peaks HEAD IMU ", peaks1)
    print("valleys HEAD IMU", valleys1)
    
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
    #     plt.plot(movement_magnitude1, label='movement_magnitude1', linewidth=1)
    #     # Plot peaks and valleys
    #     plt.plot(peaks1, movement_magnitude1[peaks1],    x   , label='Maxima')
    #     plt.plot(valleys1, movement_magnitude1[valleys1],    o   , label='Minima')
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
            print(f"MovementHead {i+1}: Yaw Range Head = {yaw_range1:.2f} degrees, Roll Range Head = {roll_range1:.2f} degrees, Combined Range Head= {combined_range1:.2f} degrees")

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

    #     # Sample IMU data processing to get acceleration magnitude
    # imu_data = ... # Your IMU data containing 'acc_x', 'acc_y', 'acc_z'
    # acc_magnitude = np.sqrt(imu_data['acc_x']**2 + imu_data['acc_y']**2 + imu_data['acc_z']**2)

    # # Detect steps
    # step_threshold = np.mean(acc_magnitude) + np.std(acc_magnitude)  # Example threshold
    # steps_detected = detect_steps(acc_magnitude, step_threshold)

    # # Estimate step length (assuming you have the user's height)
    # user_height = 1.75  # Example height in meters
    # step_length = estimate_step_length(len(steps_detected), user_height)

    # print(f   Detected steps: {len(steps_detected)}   )
    # print(f   Estimated step length: {step_length:.2f} meters   )

    # Output the metrics
    #print(f   Number of movements: {len(filtered_pairs)}   )
    #print(f   Pace: {pace:.2f} movements per second   )
    #print(f   Mean Movement Range: {mean_range:.2f} degrees, STD: {std_range:.2f}   )
    #print(f   Mean Movement Duration: {mean_duration:.2f} seconds, STD: {std_duration:.2f}   )
    

    #IMU2 BACK
    peaks, _ = find_peaks(yaw_filtered)

    valleys, _ = find_peaks(-yaw_filtered)



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
        plt.plot(yaw_filtered, label='Filtered Yaw', linewidth=1)

        plt.plot(peaks, yaw_filtered[peaks], "x", label='Maxima')
        plt.plot(valleys, yaw_filtered[valleys], "o", label='Minima')

        plt.xlabel('Sample index')
        plt.ylabel('Yaw (degrees)')
        plt.title('Yaw Signal with Detected Movements')
        plt.legend()
        plt.show()

    movement_ranges = []

    for valley, peak in movement_pairs:
        movement_range = yaw_filtered[peak] - yaw_filtered[valley]
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
        start_time = df_Limu2.iloc[start].name
        end_time = df_Limu2.iloc[end].name
        duration = (end_time - start_time).total_seconds()
        print(duration)
        movement_durations.append(duration)
        print(movement_durations)



    total_duration_seconds = (df_Limu2.index[-1] - df_Limu2.index[0]).total_seconds()
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


    metrics_data = {
            #    movements   : [
            #     {   id   : i+1,    duration_seconds   : float(duration),    range_degrees   : float(mrange)}
            #     for i, ((_, _), mrange, duration) in enumerate(zip(filtered_pairs, filtered_ranges, movement_durations))
            # ],
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
                   "number_of_movements2": int(len(filtered_pairs)),
                   "pace_movements_per_second2": float(pace),
                   "mean_range_degrees2": float(mean_range),
                   "std_range_degrees2": float(std_range),
                   "mean_duration_seconds2": float(mean_duration),
                   "std_duration_seconds2": float(std_duration),
                   "Exercise duration": total_duration_seconds,
                   "Sway_Range": max(filtered_ranges)-min(filtered_ranges)
                }
            }
        }
        
    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{datetime_string}_SwivelTurning_metrics.txt"

    # Save the metrics to a file
    save_metrics_to_txt(metrics_data, filename)

    return json.dumps(metrics_data, indent=4)

    
def save_metrics_to_txt(metrics, file_path):
    main_directory = "Standing Metrics Data"
    sub_directory = "SwivelTurning Metrics Data"

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
                    