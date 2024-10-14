import pandas as pd
import numpy as np
import pandas as pd
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

right_df = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Gaitlinear/NewGait2/01_Walk_2024-03-29_14:56:45/right_FEAC84C53DE7_2024-03-29_14:56:45.csv')
left_df = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Gaitlinear/NewGait2/01_Walk_2024-03-29_14:56:45/left_C8925E7DC6BD_2024-03-29_14:56:45.csv')

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

linear = right_df[['X(number)', 'Y (number)', 'Z (number)', 'W(number)']].to_numpy()
linear_df = right_df
    
fs = 30
cutoff = 0.6

X_filtered = butter_lowpass_filter(linear_df['X(number)'], cutoff, fs, order=5)
Z_filtered = butter_lowpass_filter(linear_df['Y (number)'], cutoff, fs, order=5)

movement_magnitude = np.sqrt(np.square(X_filtered) + np.square(Z_filtered))


# if (plotdiagrams):
#         plt.figure(figsize=(12, 6))
#         plt.plot(linear_df.index, movement_magnitude, label='Movement Magnitude', linewidth=2)
#         plt.xlabel('Timestamp')
#         plt.ylabel('Magnitude of Movement')
#         plt.title('Combined X and Z Movement Magnitude')
#         plt.legend()
#         plt.show()

peaks, _ = find_peaks(movement_magnitude)
print(peaks)
valleys, _ = find_peaks(-movement_magnitude)
print(valleys)

# t1 = right_df['heel']  
# t2 = left_df['heel']
#  # Assuming 'Toe Off' is the column containing toe off times
# t3 = right_df['toe']          
# t4 = left_df['toe'] 
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
    # Convert imu_data to a NumPy array for easier slicing
    imu_data_np = np.array(imu_data)

    # Filter data to only include entries within starttime and endtime
    filtered_data = imu_data_np[(imu_data_np[:,0] >= starttime) & (imu_data_np[:,0] <= endtime)]

    # Extract time and quaternion components
    times = filtered_data[:, 0]
    quaternions = filtered_data[:, 1:7]  # Assuming w, x, y, z are in columns 1-4

    # Generate N evenly spaced new timestamps between starttime and endtime
    new_times = np.linspace(starttime, endtime, N)

    # Initialize a list to hold interpolated data
    interpolated_data = []

    # Interpolate each quaternion component
    for i in range(6):  # For w, x, y, z
        interp_func = interp1d(times, quaternions[:, i], kind='linear')
        interpolated_component = interp_func(new_times)
        interpolated_data.append(interpolated_component)

    # Transpose and combine the interpolated data with new timestamps
    interpolated_data = np.array(interpolated_data).T
    interpolated_data_with_time = np.column_stack((new_times, interpolated_data))

    return interpolated_data_with_time.tolist()



    # if(len(imu2) > 1):
    #     print(imu2[1])
    # Limu1 = striplist(imu1)
    # Limu2 = striplist(imu2)
    # Limu3 = striplist(imu3)
    # Limu4 = striplist(imu4)
    # print('IMU1 ->', Limu1[0][0], Limu1[-1][0])
    # print('IMU2 ->', Limu2[0][0], Limu2[-1][0])
    # print('IMU3 ->', Limu3[0][0], Limu3[-1][0])
    # print('IMU4 ->', Limu4[0][0], Limu4[-1][0])

    # dt1 = float(Limu1[-1][0]) - float(Limu1[0][0]);
    # dt2 = float(Limu2[-1][0]) - float(Limu2[0][0]);
    # dt3 = float(Limu3[-1][0]) - float(Limu3[0][0]);
    # dt4 = float(Limu4[-1][0]) - float(Limu4[0][0]);

    # mean = statistics.mean([dt1, dt2, dt3, dt4])
    # std = statistics.stdev([dt1, dt2, dt3, dt4])
    # print(mean, std)


    # Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    # Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    # Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    # Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    # starttime = max(Limu1[0][0], Limu2[0][0], Limu3[0][0], Limu4[0][0])
    # endtime = min(Limu1[-1][0], Limu2[-1][0], Limu3[-1][0], Limu4[-1][0])
    # iLimu1 = interpolate_imu_data(Limu1, starttime, endtime, 1000)
    # iLimu2 = interpolate_imu_data(Limu2, starttime, endtime, 1000)
    # iLimu3 = interpolate_imu_data(Limu3, starttime, endtime, 1000)
    # iLimu4 = interpolate_imu_data(Limu4, starttime, endtime, 1000)

    # plotIMUDATA(Limu1, 2, 'origIMU1_'+str(counter)+'.png')
    # plotIMUDATA(iLimu1, 2, 'intetrpIMU1_'+str(counter)+'.png')
    # plotIMUDATA(Limu2, 2, 'origIMU2_'+str(counter)+'.png')
    # plotIMUDATA(iLimu2, 2, 'intetrpIMU2_'+str(counter)+'.png')


    # piLimu1 = pd.DataFrame(iLimu1, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    # piLimu2 = pd.DataFrame(iLimu2, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    # piLimu3 = pd.DataFrame(iLimu3, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    # piLimu4 = pd.DataFrame(iLimu4, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    #Calculate angles for the interval in degrees
    # angles = calculate_angles(piLimu1[['x', 'y']])
    # # Calculate angle changes for the interval
    # angle_changes = calculate_angle_changes(angles)
    # dynamic_threshold = define_dynamic_threshold(angle_changes)
    # repetitions = calculate_repetitions_dynamically(angle_changes, dynamic_threshold)

    # print(angle_changes)
    # print(repetitions)

    #for item in imu1:
    #    print(item)


t1 = peaks
t2 = valleys

right_gait_cycle_time = t1.shift(-1) - t1
print(right_gait_cycle_time)

# def calculate_gait_metrics(right_df, left_df): 

    # # Right single support time = t4|nextcycle - t2
    # # right_single_support_time = t4.shift(-1) - t2
    # # Left single support time =  t1|nextcycle - t3
    # #left_single_support_time = t1.shift(-1) - t3
    # # Double support time = (t4 -t1) + (t3-t2)
    # #double_support_time = (t4 - t1) + (t3 - t2)
    # # Right stance phase duration = t3 -t1
    # #right_stance_phase_duration = t3 - t1
    # # Left stance phase duration =  t4|nextcycle - t2
    # #left_stance_phase_duration = t4.shift(-1) - t2
    # # Right load response time = t4 - t1
    # # right_load_response_time = t4 - t1
    # # Right gait cycle time = t1|nextcycle - t1
    # right_gait_cycle_time = t1.shift(-1) - t1
    # # # Left loading response time = t3 - t2
    # # left_load_response_time = t3 - t2
    # # # Left gait cycle = t4|nextcycle - t4
    # # left_gait_cycle_time = t4.shift(-1) - t4
    # # Cadence = 1/ t4|nextcycle - t1
    # # cadence = 1/ (t4.shift(-1) - t1)
    # # Right single support time percentage over gait cycle =  Right single support time/Right gait cycle time
    # # right_single_support_time_percentage = (right_single_support_time / right_gait_cycle_time) * 100
    # # # Left single support time percentage over gait cycle = Left single support time/Right gait cycle time
    # # left_single_support_time_percentage = (left_single_support_time / right_gait_cycle_time) * 100
    # # # Double support time percentage over gait cycle =  Double support time/Right gait cycle time
    # # double_support_time_percentage = (double_support_time / right_gait_cycle_time) * 100
    # # Right stance phase time percentage over gait cycle = Right stance phase duration/Right gait cycle time 
    # # right_stance_phase_percentage = (right_stance_phase_duration / right_gait_cycle_time) * 100
    # # # Left stance phase time percentage over gait cycle = Left stance phase duration/Right gait cycle time
    # # left_stance_phase_percentage = (left_stance_phase_duration / right_gait_cycle_time) * 100
    # # # Right loading response percentage time over gait cycle = Right load response time/Right gait cycle time
    # # right_loading_response_percentage = (right_load_response_time / right_gait_cycle_time) * 100
    # # # Left loading response percentage phase time over gait cycle = Left loading response time/Right gait cycle time
    # # left_loading_response_percentage = (left_load_response_time / right_gait_cycle_time) * 100

    # # Combine the results into a dictionary for easy access
    # gait_metrics = {
    #     # 'Right Single Support Time': right_single_support_time,
    #     # 'Left Single Support Time': left_single_support_time,
    #     # 'Double Support Time': double_support_time,
    #     # 'Right Stance Phase Duration': right_stance_phase_duration,
    #     # 'Left Stance Phase Duration': left_stance_phase_duration,
    #     # 'Right Load Response Time': right_load_response_time,
    #     'Right Gait Cycle Time': right_gait_cycle_time,
    #     # 'Left Load Response Time': left_load_response_time,
    #     # 'Left Gait Cycle Time': left_gait_cycle_time,
    #     # 'Cadence': cadence,
    #     # 'Right Single Support Percentage': right_single_support_time_percentage
    #     # 'Left Single Support Percentage': left_single_support_time_percentage,
    #     # 'Double Support Percentage': double_support_time_percentage,
    #     # 'Right Stance Phase Percentage': right_stance_phase_percentage,
    #     # 'Left Stance Phase Percentage': left_stance_phase_percentage,
    #     # 'Right Loading Response Percentage': right_loading_response_percentage,
    #     # 'Left Loading Response Percentage': left_loading_response_percentage,
    # }
    
    # return gait_metrics

    def get_metrics(imu1,imu2,imu3,imu4, counter):
    
    print(" imu1 ", len(imu1), " imu2 ", len(imu2), " imu3 ", len(imu3), " imu4 ", len(imu4)) 

    # data = {
    #     "Number of maxima greater than -0.65": 10,
    #     "Number of minima less than -0.7": 59,
    #     "Repetitions": 10,
    #     "Range of Motion": 0.23487970000000002,
    #     "Range of Motion (Yaw)": "359.10205910490043 degrees",
    #     "Rotation Speed (Tempo)": "0.40909090909090906 rotations per second",
    #     "Consistency (Std. Dev. of Peaks)": 0.010178870711628313
    # }

    # return data

    # if(len(imu2) > 1):
    #     print(imu2[1])
    # Limu1 = striplist(imu1)
    # Limu2 = striplist(imu2)
    # Limu3 = striplist(imu3)
    # Limu4 = striplist(imu4)
    # print('IMU1 ->', Limu1[0][0], Limu1[-1][0])
    # print('IMU2 ->', Limu2[0][0], Limu2[-1][0])
    # print('IMU3 ->', Limu3[0][0], Limu3[-1][0])
    # print('IMU4 ->', Limu4[0][0], Limu4[-1][0])

    # dt1 = float(Limu1[-1][0]) - float(Limu1[0][0]);
    # dt2 = float(Limu2[-1][0]) - float(Limu2[0][0]);
    # dt3 = float(Limu3[-1][0]) - float(Limu3[0][0]);
    # dt4 = float(Limu4[-1][0]) - float(Limu4[0][0]);

    # mean = statistics.mean([dt1, dt2, dt3, dt4])
    # std = statistics.stdev([dt1, dt2, dt3, dt4])
    # print(mean, std)


    # Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    # Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    # Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    # Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    # starttime = max(Limu1[0][0], Limu2[0][0], Limu3[0][0], Limu4[0][0])
    # endtime = min(Limu1[-1][0], Limu2[-1][0], Limu3[-1][0], Limu4[-1][0])
    # iLimu1 = interpolate_imu_data(Limu1, starttime, endtime, 1000)
    # iLimu2 = interpolate_imu_data(Limu2, starttime, endtime, 1000)
    # iLimu3 = interpolate_imu_data(Limu3, starttime, endtime, 1000)
    # iLimu4 = interpolate_imu_data(Limu4, starttime, endtime, 1000)

    # plotIMUDATA(Limu1, 2, 'origIMU1_'+str(counter)+'.png')
    # plotIMUDATA(iLimu1, 2, 'intetrpIMU1_'+str(counter)+'.png')
    # plotIMUDATA(Limu2, 2, 'origIMU2_'+str(counter)+'.png')
    # plotIMUDATA(iLimu2, 2, 'intetrpIMU2_'+str(counter)+'.png')


    # piLimu1 = pd.DataFrame(iLimu1, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    # piLimu2 = pd.DataFrame(iLimu2, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    # piLimu3 = pd.DataFrame(iLimu3, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    # piLimu4 = pd.DataFrame(iLimu4, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    #Calculate angles for the interval in degrees
    # angles = calculate_angles(piLimu1[['x', 'y']])
    # # Calculate angle changes for the interval
    # angle_changes = calculate_angle_changes(angles)
    # dynamic_threshold = define_dynamic_threshold(angle_changes)
    # repetitions = calculate_repetitions_dynamically(angle_changes, dynamic_threshold)

    # print(angle_changes)
    # print(repetitions)

    #for item in imu1:
    #    print(item)