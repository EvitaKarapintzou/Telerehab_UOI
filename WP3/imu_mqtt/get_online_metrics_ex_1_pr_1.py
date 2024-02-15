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

def calculate_angles(data):
    # Calculate the angle in radians and then convert to degrees
    angles = np.arctan2(data['y'], data['x']) * (180 / np.pi)
    return angles

def calculate_angle_changes(angles):
    # Calculate absolute differences between consecutive angles
    angle_changes = angles.diff().abs()
    return angle_changes

def define_dynamic_threshold(angle_changes):
    threshold = angle_changes.mean() + 1.5 * angle_changes.std()
    return threshold

def calculate_repetitions_dynamically(angle_changes, threshold):
    repetitions_count = (angle_changes > threshold).sum()
    return repetitions_count
def plotIMUDATA(Limu, x, filename):
        # Extract time and w components from your data
    time = [row[0] for row in Limu]
    w = [row[x] for row in Limu]

    # Plotting
    plt.figure(figsize=(10, 6))  # Optional: Adjusts the size of the plot
    plt.plot(time, w, marker='o', linestyle='-', color='b')  # marker and linestyle are optional

    plt.title('Time vs W Component')
    plt.xlabel('Time (sec)')
    plt.ylabel('W component of quaternion')
    plt.grid(True)  # Optional: Shows a grid for easier reading

    plt.savefig(filename)

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



# Call the function
#interpolated_imu_data = interpolate_imu_data(imu_data, starttime, endtime, N)
#print(interpolated_imu_data)

def striplist(L):
    A = []
    for item in L:
        t = item[1:-1]
        #print(t)
        t = t.split(' ')
        A.append([t[-7], t[-6],t[-5],t[-4],t[-3],t[-2],t[-1]])
    return A

def get_metrics(imu1,imu2,imu3,imu4, counter):
    
    print(" imu1 ", len(imu1), " imu2 ", len(imu2), " imu3 ", len(imu3), " imu4 ", len(imu4)) 
    # if(len(imu2) > 1):
    #     print(imu2[1])
    Limu1 = striplist(imu1)
    Limu2 = striplist(imu2)
    Limu3 = striplist(imu3)
    Limu4 = striplist(imu4)
    print('IMU1 ->', Limu1[0][0], Limu1[-1][0])
    print('IMU2 ->', Limu2[0][0], Limu2[-1][0])
    print('IMU3 ->', Limu3[0][0], Limu3[-1][0])
    print('IMU4 ->', Limu4[0][0], Limu4[-1][0])

    dt1 = float(Limu1[-1][0]) - float(Limu1[0][0]);
    dt2 = float(Limu2[-1][0]) - float(Limu2[0][0]);
    dt3 = float(Limu3[-1][0]) - float(Limu3[0][0]);
    dt4 = float(Limu4[-1][0]) - float(Limu4[0][0]);

    mean = statistics.mean([dt1, dt2, dt3, dt4])
    std = statistics.stdev([dt1, dt2, dt3, dt4])
    print(mean, std)


    Limu1 = [[float(item) for item in sublist] for sublist in Limu1]
    Limu2 = [[float(item) for item in sublist] for sublist in Limu2]
    Limu3 = [[float(item) for item in sublist] for sublist in Limu3]
    Limu4 = [[float(item) for item in sublist] for sublist in Limu4]

    starttime = max(Limu1[0][0], Limu2[0][0], Limu3[0][0], Limu4[0][0])
    endtime = min(Limu1[-1][0], Limu2[-1][0], Limu3[-1][0], Limu4[-1][0])
    iLimu1 = interpolate_imu_data(Limu1, starttime, endtime, 1000)
    iLimu2 = interpolate_imu_data(Limu2, starttime, endtime, 1000)
    iLimu3 = interpolate_imu_data(Limu3, starttime, endtime, 1000)
    iLimu4 = interpolate_imu_data(Limu4, starttime, endtime, 1000)

    plotIMUDATA(Limu1, 2, 'origIMU1_'+str(counter)+'.png')
    plotIMUDATA(iLimu1, 2, 'intetrpIMU1_'+str(counter)+'.png')
    plotIMUDATA(Limu2, 2, 'origIMU2_'+str(counter)+'.png')
    plotIMUDATA(iLimu2, 2, 'intetrpIMU2_'+str(counter)+'.png')


    piLimu1 = pd.DataFrame(iLimu1, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    piLimu2 = pd.DataFrame(iLimu2, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    piLimu3 = pd.DataFrame(iLimu3, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
    piLimu4 = pd.DataFrame(iLimu4, columns=['time', 'w', 'x', 'y', 'z', 'd1', 'd2'])
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

    #===========================

#HEAD DATA
#imu_data_path_sensor_head = r'C:\Users\xrysa\OneDrive\Υπολογιστής\Sitting_data\New Sitting 1_left\Normal\2024-02-08_12_44_56_sitting_1_normal_1\head_FEAC84C53DE7_2024-02-08_12_44_56.csv'

#BACK DATA
#imu_data_path_sensor_back = r'C:\Users\xrysa\OneDrive\Υπολογιστής\Sitting_data\New Sitting 1_left\Normal\2024-02-08_12_44_56_sitting_1_normal_1\back_E25AD03D0194_2024-02-08_12_44_56.csv'

# imu1 = pd.read_csv(imu_data_path_sensor_head)
#imu2 = pd.read_csv(imu_data_path_sensor_back)

# Function to convert quaternions to Euler angles (in radians)
    def quaternion_to_euler(w, x, y, z):
        r = R.from_quat([x, y, z, w])
        return r.as_euler('xyz', degrees=False)
    
    # Assuming the IMU data includes quaternion columns named 'W', 'X', 'Y', 'Z'
    # Replace these with your actual quaternion column names
    quaternions = piLimu2[['w', 'x', 'y', 'z',]].to_numpy()
    
    # Convert quaternions to Euler angles
    euler_angles = np.array([quaternion_to_euler(*q) for q in quaternions])

    # Calculate ROM for each Euler angle
    # For example, if we're interested in the 'yaw' angle (rotation around the z-axis),
    # which is typically the third angle in the XYZ convention
    yaw_angles = euler_angles[:, 2]
    rom_yaw = np.max(yaw_angles) - np.min(yaw_angles)
    
    
    # Find the indices of the local maxima with a height condition
    maxima_indices_back = find_peaks(piLimu2['y'], height=-0.6)[0]
    # Invert the signal to find the min peaks and then filter them with the condition that they are less than -0.7
    min_peaks_back, _ = find_peaks(-piLimu2['y'])
    filtered_min_peaks_back = min_peaks_back[piLimu2['y'][min_peaks_back] < -0.7]
    
    # # Plot the Y component and the maxima for 'back' data
    # plt.figure(figsize=(12, 6))
    # plt.plot(imu_data_sensor_back['Elapsed(s)'], imu_data_sensor_back['Y (number)'], label='Y Component Back', color= 'green')
    
    # # Only plot the peaks that are greater than -0.65
    filtered_maxima_indices_back = maxima_indices_back[piLimu2['y'][maxima_indices_back] > -0.65]
    # plt.plot(imu_data_sensor_back['Elapsed(s)'][filtered_maxima_indices_back], 
    #          imu_data_sensor_back['Y (number)'][filtered_maxima_indices_back], 
    #          'x', color='red', label='Maxima > -0.65')
    # plt.plot(imu_data_sensor_back['Elapsed(s)'][filtered_min_peaks_back], imu_data_sensor_back['Y (number)'][filtered_min_peaks_back], 'o', color='blue', label='Minima < -0.7')
    
    # # Add labels and title to the plot
    # plt.xlabel('Elapsed Time (s)')
    # plt.ylabel('Y Component Value')
    # plt.title('Y Component over Time with Maxima > -0.65')
    # plt.legend()
    # plt.grid(True)
    # plt.show()
    
    repetitions = len(maxima_indices_back)
    rom_back = np.ptp(piLimu2['y'])  # Peak-to-peak (max-min) range
    
    # Calculate the speed/tempo of rotations
    # Assuming that `Elapsed(s)` is uniformly sampled
    time_diffs = np.diff(piLimu2['time'][maxima_indices_back])
    rotation_speed = 1 / time_diffs.mean()  # Average rotations per second
    
    # Assess the consistency
    peak_values_back = piLimu2['y'][maxima_indices_back]
    consistency_back = np.std(peak_values_back)


    
    #print(filtered_maxima_indices_back)
    
    print(f"Number of maxima greater than -0.65: {len(filtered_maxima_indices_back)}")
    print(f"Number of minima less than -0.7: {len(filtered_min_peaks_back)}")
    
    print(f"Repetitions: {repetitions}")
    print(f"Range of Motion: {rom_back}")
    print(f"Range of Motion (Yaw): {np.degrees(rom_yaw)} degrees")
    print(f"Rotation Speed (Tempo): {rotation_speed} rotations per second")
    print(f"Consistency (Std. Dev. of Peaks): {consistency_back}")


    #===========================
    
    
    # save_data(imu1,imu2,imu3,imu4)
    #return(imu2)

def save_data(imu1,imu2,imu3,imu4):
    if(len(imu1) > 0):
        print(len(imu1))


																																	
