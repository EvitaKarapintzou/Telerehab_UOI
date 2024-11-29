import pandas as pd
import numpy as np
import os
from datetime import datetime
import statistics 
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.signal import correlate
from scipy.spatial.transform import Rotation as R
from scipy.signal import butter, filtfilt
import json
from scipy.signal import find_peaks
from scipy.fft import fft, fftfreq
from scipy.optimize import minimize
from scipy.signal import butter, filtfilt
from scipy.signal import medfilt

# Keep only the smallest minimum between each pair of maxima
def filter_minima(signal, maxima, minima):
    filtered_minima = []
    if isinstance(signal, np.ndarray):
        signal = pd.Series(signal)
    for i in range(len(maxima) - 1):
        # Get minima between two maxima
        start, end = maxima[i], maxima[i + 1]
        interval_minima = [m for m in minima if start < m < end]
        if interval_minima:
            # Find the smallest minimum in the interval
            smallest_minimum = min(interval_minima, key=lambda m: signal.iloc[m])
            filtered_minima.append(smallest_minimum)
    return filtered_minima

# Filter maxima based on one standard deviation
def filter_maxima(signal, peaks):
    if isinstance(signal, np.ndarray):
        signal = pd.Series(signal)
    max_val = signal.max()
    std_dev = 1.5 * signal.std()
    return peaks[signal.iloc[peaks] >= (max_val - std_dev)]

# Calculate autocorrelation to determine the distance parameter
def calculate_autocorrelation(data):
    autocorr = correlate(data, data, mode='full')
    autocorr = autocorr[autocorr.size // 2:]  # Use only positive lags
    lags = range(len(autocorr))
    return autocorr, lags

def low_pass_filter(data, cutoff, fs, order=4):
    nyquist = 0.5 * fs  # Nyquist frequency
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_data = filtfilt(b, a, data)
    return filtered_data

# Normalize the 'w' components to 0-1 range
def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

def process_imu_data(imu_data_lists, fs, plotdiagrams=True):
    # Ensure lists are not empty and convert to DataFrames
    dataframes = []
    initial_empty_lists = [len(imu_data) == 0 for imu_data in imu_data_lists]  # Track initially empty lists

    c = 0;
    for imu_data in imu_data_lists:
        if imu_data:
            #print('imu_data = ', imu_data)
            columns = ['Timestamp', 'elapsed(time)', 'W(number)', 'X(number)', 'Y(number)', 'Z(number)']
            df = pd.DataFrame(imu_data, columns=columns)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            df = df.sort_values(by='Timestamp')
            df.set_index('Timestamp', inplace=True)
            dataframes.append(df)
            c = c + 1


    if not dataframes:
        print('no data to process')
        return None  # No data to process
    else:
        print(dataframes)

    # Find the common time range
    max_start_time = max(df.index[0] for df in dataframes)
    min_end_time = min(df.index[-1] for df in dataframes)

    print('max_start_time = ', max_start_time)
    print('min_end_time = ', min_end_time)

    # Filter dataframes to the common time range
    #dataframes = [df[max_start_time:min_end_time] for df in dataframes]

    # Determine the maximum number of samples across lists
    #max_samples = max(len(df) for df in dataframes)

    # Resample and interpolate dataframes to have the same number of samples
    resampled_dataframes = []
    for df in dataframes:
        #df_resampled = df.resample(f'{1000//fs}ms').mean()  # Resampling to match the sampling frequency
        #df_interpolated = df_resampled.interpolate(method='time')
        #df_interpolated = df_interpolated.dropna().head(max_samples)
        #resampled_dataframes.append(df_interpolated)
        resampled_dataframes.append(df)

    if plotdiagrams:
        for idx, df in enumerate(resampled_dataframes):
            plt.figure(figsize=(10, 6))
            plt.plot(df.index, df['W(number)'], label='W')
            plt.plot(df.index, df['X(number)'], label='X')
            plt.plot(df.index, df['Y(number)'], label='Y')
            plt.plot(df.index, df['Z(number)'], label='Z')
            plt.xlabel('Timestamp')
            plt.ylabel('Quaternion Components')
            plt.title(f'IMU {idx+1} Quaternion Components (W, X, Y, Z) over Time')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'quaternion_components_plot_{idx+1}.png')
            # plt.show()

    # Convert the processed DataFrames back to lists
    #resampled_lists = [df.reset_index().values.tolist() for df in resampled_dataframes]

    #20241013
    resampled_lists = []

    data_idx = 0
    for is_empty in initial_empty_lists:
        if is_empty:
            resampled_lists.append([])  # Keep the list empty if it was initially empty
        else:
            resampled_lists.append(resampled_dataframes[data_idx].reset_index().values.tolist())  # Add processed data
            data_idx += 1

    return resampled_lists, c

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
    #Limu1 = striplist(imu1[2:])
    #Limu2 = striplist(imu2[2:])
    #Limu3 = striplist(imu3[2:])
    #Limu4 = striplist(imu4[2:])
    

    Limu1 = reformat_sensor_data(imu1)
    Limu2 = reformat_sensor_data(imu2)
    Limu3 = reformat_sensor_data(imu3)   
    Limu4 = reformat_sensor_data(imu4)
    imu_data_lists = [Limu1, Limu2, Limu3, Limu4]
    processed_dataframes, c = process_imu_data(imu_data_lists, 50, True)

    Limu1 = processed_dataframes[0]
    #print('Limu1 = ', Limu1)
    if (c >= 2):
        Limu2 = processed_dataframes[1]
    if (c >= 3):
        Limu3 = processed_dataframes[2]
    if (c >= 4):
        Limu4 = processed_dataframes[3]

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

    head_normalized = normalize(df_Limu1['W(number)'])
    pelvis_normalized = normalize(df_Limu2['W(number)'])     

    # Parameters for the filter
    cutoff = 1.5  # Cutoff frequency in Hz
    sampling_rate = 100  # Sampling rate in Hz (adjust based on your data)

    # Apply the low-pass filter
    head_filtered = low_pass_filter(head_normalized, cutoff, sampling_rate)
    pelvis_filtered = low_pass_filter(pelvis_normalized, cutoff, sampling_rate)

    # Get autocorrelation and lag for each signal
    head_autocorr, head_lags = calculate_autocorrelation(head_filtered)
    pelvis_autocorr, pelvis_lags = calculate_autocorrelation(pelvis_filtered)

    # Find the lag of the first significant peak in autocorrelation
    head_distance = head_lags[next(i for i in range(1, len(head_autocorr)) if head_autocorr[i] < head_autocorr[0] * 0.9)]
    pelvis_distance = pelvis_lags[next(i for i in range(1, len(pelvis_autocorr)) if pelvis_autocorr[i] < pelvis_autocorr[0] * 0.3)]

    # Detect maxima
    head_maxima, _ = find_peaks(head_filtered, distance=head_distance)
    pelvis_maxima, _ = find_peaks(pelvis_filtered, distance=pelvis_distance)

    head_maxima_filtered = filter_maxima(head_filtered, head_maxima)
    pelvis_maxima_filtered = filter_maxima(pelvis_filtered, pelvis_maxima)

    # Detect minima by inverting the filtered signals
    head_minima, _ = find_peaks(-head_filtered, distance=head_distance)
    pelvis_minima, _ = find_peaks(-pelvis_filtered, distance=pelvis_distance)


    head_minima_filtered = filter_minima(head_filtered, head_maxima_filtered, head_minima)
    pelvis_minima_filtered = filter_minima(pelvis_filtered, pelvis_maxima_filtered, pelvis_minima)
    
    # Define time interval (0.01 seconds between points)
    time_interval = 0.01  # seconds

    # Initialize a dictionary to store the metrics
    metrics = {}

    # 1. Number of repetitions (pelvis maxima)
    metrics['number_of_movements'] = len(pelvis_maxima_filtered)

    # 2. Time between two pelvis maxima (time of movement)
    time_between_pelvis_maxima = np.diff(pelvis_maxima_filtered) * time_interval
    metrics['movement_mean_time'] = np.mean(time_between_pelvis_maxima)
    metrics['movement_std_time'] = np.std(time_between_pelvis_maxima)

    # 3. From a pelvis maximum to a pelvis minimum (bend over time)
    bend_over_times = []
    for i in range(len(pelvis_maxima_filtered) - 1):
        start_index = pelvis_maxima_filtered[i]
        end_index = pelvis_minima_filtered[i]
        bend_over_times.append((end_index - start_index) * time_interval)
    metrics['bend_over_mean_time'] = np.mean(bend_over_times)
    metrics['bend_over_std_time'] = np.std(bend_over_times)

    # 4. From a pelvis minimum to a pelvis maximum (return up time)
    return_up_times = []
    for i in range(len(pelvis_minima_filtered)):
        start_index = pelvis_minima_filtered[i]
        end_index = pelvis_maxima_filtered[i + 1]
        return_up_times.append((end_index - start_index) * time_interval)
    metrics['return_up_mean_time'] = np.mean(return_up_times)
    metrics['return_up_std_time'] = np.std(return_up_times)

    # 5. Head movements: chin to chest (head max to head min) and chest to chin (head min to head max)
    chin_to_chest_times = []
    chest_to_chin_times = []

    for i in range(len(head_minima_filtered)):
        start_index = head_maxima_filtered[i]
        end_index = head_minima_filtered[i]
        chin_to_chest_times.append((end_index - start_index) * time_interval)

    for i in range(len(head_minima_filtered)):
        start_index = head_minima_filtered[i]
        end_index = head_maxima_filtered[i + 1]
        chest_to_chin_times.append((end_index - start_index) * time_interval)

    metrics['chin_to_chest_mean_time'] = np.mean(chin_to_chest_times)
    metrics['chin_to_chest_std_time'] = np.std(chin_to_chest_times)
    metrics['chest_to_chin_mean_time'] = np.mean(chest_to_chin_times)
    metrics['chest_to_chin_std_time'] = np.std(chest_to_chin_times)

    metrics_data = {   
        "total_metrics": {
            "number_of_movements": len(pelvis_maxima_filtered),
            "movement_mean_time": np.mean(time_between_pelvis_maxima),
            "movement_std_time": np.std(time_between_pelvis_maxima),
            "bend_over_mean_time": np.mean(bend_over_times),
            "bend_over_std_time": np.std(bend_over_times),
            "return_up_mean_time": np.mean(return_up_times),
            "return_up_std_time": np.std(return_up_times),
            "chin_to_chest_mean_time": np.mean(chin_to_chest_times),
            "chin_to_chest_std_time": np.std(chin_to_chest_times),
            "chest_to_chin_mean_time": np.mean(chest_to_chin_times),
            "chest_to_chin_std_time": np.std(chest_to_chin_times)
        }
    }

    print(metrics_data)
        
        
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