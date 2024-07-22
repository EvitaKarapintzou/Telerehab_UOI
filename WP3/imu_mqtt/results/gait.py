

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
from scipy.fft import fft, fftfreq

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

df_Limu1 = '/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Chrysa/Oneway/right_FEAC84C53DE7_2024-07-17_16:34:58.csv'
df_Limu2 = '/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Chrysa/Oneway/left_E25AD03D0194_2024-07-17_16:34:58.csv'


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
    # Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    #Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    if len(Limu1) > 0 and len(Limu2) > 0:
        returnedJson = getMetricsGaitNew01(Limu1, Limu2, False) 
        return returnedJson
    

# def calculate_steps_with_fft(signal, fs, low_freq, high_freq):
#     N = len(signal)
#     yf = fft(signal)
#     xf = fftfreq(N, 1 / fs)

#     # Apply a Hamming window to the signal to reduce spectral leakage
#     windowed_signal = signal * np.hamming(N)

#     yf = fft(windowed_signal)
#     xf = fftfreq(N, 1 / fs)

#     # Filter the FFT output to keep only the frequencies of interest
#     indices = np.where((xf >= low_freq) & (xf <= high_freq))
#     filtered_signal = np.abs(yf[indices])

#     # Apply a threshold to eliminate low-intensity noise peaks
#     threshold = np.mean(filtered_signal) + 2 * np.std(filtered_signal)
#     significant_peaks = filtered_signal[filtered_signal > threshold]

#     if len(significant_peaks) == 0:
#         print("No significant peaks found in the FFT.")
#         return None

#     # Find the peak frequency within the filtered signal
#     peak_index = np.argmax(significant_peaks)
#     peak_freq = xf[indices][np.argmax(filtered_signal)]


#     # Calculate steps based on peak frequency
#     stepsF = peak_freq * (N / fs)
#     return stepsF
    



def getMetricsGaitNew01(Limu1, Limu2, plotdiagrams):

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

    
   
    
    linear_df1 = df_Limu1;
    linear_df2 = df_Limu2;
    
   
    fs = 30
    cutoff = 0.425

      
    Z_filtered1 = butter_lowpass_filter(linear_df1['Z (number)'], cutoff, fs, order=5)
    X_filtered1 = butter_lowpass_filter(linear_df1['X(number)'], cutoff, fs, order=5)
    Y_filtered1 = butter_lowpass_filter(linear_df1['Y (number)'], cutoff, fs, order=5)

    Z_filtered2 = butter_lowpass_filter(linear_df2['Z (number)'], cutoff, fs, order=5)
    X_filtered2 = butter_lowpass_filter(linear_df2['X(number)'], cutoff, fs, order=5)
    Y_filtered2 = butter_lowpass_filter(linear_df2['Y (number)'], cutoff, fs, order=5)


  

    movement_magnitude1 = np.sqrt(np.square(X_filtered1) + np.square(Y_filtered1) + np.square(Z_filtered1))
    movement_magnitude2 = np.sqrt(np.square(X_filtered2) + np.square(Y_filtered2) + np.square(Z_filtered2))
    
   

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
    
    movement_pairs1 = [(valleys1[i], peaks1[i]) for i in range(min(len(peaks1), len(valleys1)))]

    for i in range(min(len(peaks1), len(valleys1))):
        movement_pairs1.append((valleys1[i], peaks1[i]))

    print("Movement pairs for Right Leg (as index positions):", movement_pairs1)



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
        
    movement_pairs2 = [(valleys2[i], peaks2[i]) for i in range(min(len(peaks2), len(valleys2)))]

    for i in range(min(len(peaks2), len(valleys2))):
        movement_pairs2.append((valleys2[i], peaks2[i]))

    print("Movement pairs for Left Leg (as index positions):", movement_pairs2)
    steps = min(len(movement_pairs1), len(movement_pairs2))
   

    #=============IMU1-Right Leg====================#
    movement_ranges_z1 = []
    movement_ranges_y1 = []
   

    for valley1, peak1 in movement_pairs1:
            z_range1 = abs(Z_filtered1[peak1] - Z_filtered1[valley1])
            movement_ranges_z1.append(z_range1)

            y_range1 = abs(X_filtered1[peak1] - X_filtered1[valley1])
            movement_ranges_y1.append(y_range1)
            
           

    combined_movement_ranges1 = [np.sqrt(z1**2 + y1**2) for z1, y1 in zip(movement_ranges_z1, movement_ranges_y1)]

    for i, (z_range1, y_range1) in enumerate(zip(movement_ranges_z1, movement_ranges_y1)):
            combined_range1 = np.sqrt(z_range1**2  + y_range1**2)
            print(f"MovementRight {i+1}: Z Range Right = {z_range1:.2f} degrees, Y Range Right = {y_range1:.2f} degrees, Combined Range Right = {combined_range1:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements1 = [(pair1, z1, y1,  np.sqrt(z1**2 + y1**2)) for pair1, z1, y1 in zip(movement_pairs1, movement_ranges_z1, movement_ranges_y1 ) if np.sqrt(z1**2 + y1**2 ) >= 0.01]

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
    movement_ranges_z2 = []
    movement_ranges_y2 = []
  

    for valley2, peak2 in movement_pairs2:
            z_range2 = abs(Z_filtered2[peak2] - Z_filtered2[valley2])
            movement_ranges_z2.append(z_range2)

            y_range2 = abs(X_filtered2[peak2] - X_filtered2[valley2])
            movement_ranges_y2.append(y_range2)
            
            

    combined_movement_ranges2 = [np.sqrt(z2**2 + y2**2) for z2, y2 in zip(movement_ranges_z2, movement_ranges_y2)]

    for i, (z_range2, y_range2) in enumerate(zip(movement_ranges_z2, movement_ranges_y2)):
            combined_range2 = np.sqrt(z_range2**2 + y_range2**2)
            print(f"MovementLeft {i+1}: Z Range Left = {z_range2:.2f} degrees, Y Range Left = {y_range2:.2f} degrees,  Combined Range Left = {combined_range2:.2f} degrees")

        # Filter the movement ranges and corresponding pairs for combined ranges >= 8 degrees
    significant_movements2 = [(pair2, z2, y2, np.sqrt(z2**2 + y2**2)) for pair2, z2, y2 in zip(movement_pairs2, movement_ranges_z2, movement_ranges_y2) if np.sqrt(z2**2 + y2**2) >= 0.01]

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



    ###GAIT CYCLE###

    right_single_support_time = (t4_series.shift(-1) - t2_series)
    left_single_support_time = (t1_series.shift(-1) - t3_series)
    double_support_time = (t4_series - t1_series) + (t3_series - t2_series)
    right_stance_phase_duration = t3_series - t1_series
    left_stance_phase_duration = t4_series.shift(-1) - t2_series
    right_load_response_time = t4_series - t1_series
    right_gait_cycle_time = (t1_series.shift(-1) - t1_series)/60
    left_load_response_time = t3_series - t2_series
    left_gait_cycle_time = (t4_series.shift(-1) - t4_series)/60
    cadence = 1/(t4_series.shift(-1) - t1_series)
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
                "Number of steps": int(steps),
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
                            }
             
    }
    }



    datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{datetime_string}_SideStepping_metrics.txt"

    # Save the metrics to a file
    save_metrics_to_txt(metrics_data, filename)

    return json.dumps(metrics_data, indent=4)

    
def save_metrics_to_txt(metrics, file_path):
    main_directory = "Gait Metrics Data"
    sub_directory = "SideStepping Metrics Data"

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
         

