import pandas as pd
import os
from datetime import datetime
import json
import numpy as np
from scipy.signal import find_peaks, butter, filtfilt
import matplotlib.pyplot as plt

def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs  
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

def preprocess_imu_data(df):
    df['elapsed (s)'] = pd.to_datetime(df['elapsed (s)'])
    df.sort_values(by='elapsed (s)', inplace=True)
    df.set_index('elapsed (s)', inplace=True)
    return df

def calculate_cadence(step_times):
    if len(step_times) < 2:
        return 0
    total_time = (step_times.iloc[-1] - step_times.iloc[0]).total_seconds() / 60.0  # total time in minutes
    number_of_steps = len(step_times)
    cadence = number_of_steps / total_time
    return cadence

def getMetricsGaitNew01(df_Limu1, df_Limu2, plot_diagrams=False):
    fs = 30
    cutoff = 0.425

    Z_filtered1 = butter_lowpass_filter(df_Limu1['z-axis (g)'], cutoff, fs, order=5)
    X_filtered1 = butter_lowpass_filter(df_Limu1['x-axis (g)'], cutoff, fs, order=5)
    Y_filtered1 = butter_lowpass_filter(df_Limu1['y-axis (g)'], cutoff, fs, order=5)

    Z_filtered2 = butter_lowpass_filter(df_Limu2['z-axis (g)'], cutoff, fs, order=5)
    X_filtered2 = butter_lowpass_filter(df_Limu2['x-axis (g)'], cutoff, fs, order=5)
    Y_filtered2 = butter_lowpass_filter(df_Limu2['y-axis (g)'], cutoff, fs, order=5)

    movement_magnitude1 = np.sqrt(np.square(X_filtered1) + np.square(Y_filtered1) + np.square(Z_filtered1))
    movement_magnitude2 = np.sqrt(np.square(X_filtered2) + np.square(Y_filtered2) + np.square(Z_filtered2))

    peaks1, _ = find_peaks(movement_magnitude1, distance=fs//2)
    valleys1, _ = find_peaks(-movement_magnitude1, distance=fs//2)

    if len(peaks1) == 0 or len(valleys1) == 0:
        return {}

    if valleys1[0] > peaks1[0]:
        peaks1 = peaks1[1:]
    if peaks1[-1] < valleys1[-1]:
        valleys1 = valleys1[:-1]

    movement_pairs1 = [(valleys1[i], peaks1[i]) for i in range(min(len(peaks1), len(valleys1)))]

    peaks2, _ = find_peaks(movement_magnitude2, distance=fs//2)
    valleys2, _ = find_peaks(-movement_magnitude2, distance=fs//2)

    if len(peaks2) == 0 or len(valleys2) == 0:
        return {}

    if valleys2[0] > peaks2[0]:
        peaks2 = peaks2[1:]
    if peaks2[-1] < valleys2[-1]:
        valleys2 = valleys2[:-1]

    movement_pairs2 = [(valleys2[i], peaks2[i]) for i in range(min(len(peaks2), len(valleys2)))]

    steps = (min(len(movement_pairs1), len(movement_pairs2)))/3

    heel_strikes_times_Right, properties1 = find_peaks(movement_magnitude1, prominence=0.01)
    toe_off_times_Right, properties1 = find_peaks(-movement_magnitude1, prominence=0.01)
    heel_strikes_times_Left, properties2 = find_peaks(movement_magnitude2, prominence=0.09)
    toe_off_times_Left, properties2 = find_peaks(-movement_magnitude2, prominence=0.09)

    t1_series = pd.Series(heel_strikes_times_Right)
    t2_series = pd.Series(heel_strikes_times_Left)
    t3_series = pd.Series(toe_off_times_Right)
    t4_series = pd.Series(toe_off_times_Left)

    right_single_support_time = (t4_series.shift(-1) - t2_series)/400
    left_single_support_time = (t1_series.shift(-1) - t3_series)/100
    double_support_time = (t4_series - t1_series) + (t3_series - t2_series)
    right_stance_phase_duration = t3_series - t1_series
    left_stance_phase_duration = t4_series.shift(-1) - t2_series
    right_load_response_time = t4_series - t1_series
    right_gait_cycle_time = (t1_series.shift(-1) - t1_series)/60
    left_load_response_time = t3_series - t2_series
    left_gait_cycle_time = (t4_series.shift(-1) - t4_series)/60
    cadence = 1/(t4_series.shift(-1) - t1_series)
    # right_cadence = (steps/right_gait_cycle_time)
    # left_cadence = (steps/left_gait_cycle_time)
    right_single_support_time_percentage = (right_single_support_time / right_gait_cycle_time) * 100
    left_single_support_time_percentage = (left_single_support_time / right_gait_cycle_time) * 100
    double_support_time_percentage = (double_support_time / right_gait_cycle_time) * 100
    right_stance_phase_percentage = (right_stance_phase_duration / right_gait_cycle_time) * 100
    left_stance_phase_percentage = (left_stance_phase_duration / right_gait_cycle_time) * 100
    right_loading_response_percentage = (right_load_response_time / right_gait_cycle_time) * 100
    left_loading_response_percentage = (left_load_response_time / right_gait_cycle_time) * 100


    right_cadence = calculate_cadence(t1_series.to_series())
    left_cadence = calculate_cadence(t2_series.to_series())

    metrics_data = {
        "total_metrics": {
            "Gait Cycle": {
                "Number of steps": steps,
                "Right Single Support Time": right_single_support_time.tolist(),
                "Left Single Support Time": left_single_support_time.tolist(),
                "Right cadence (steps/min)": right_cadence.tolist(),
                "Left cadence (steps/min)": left_cadence.tolist(),
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

    if plot_diagrams:
        plt.figure(figsize=(14, 8))
        plt.plot(df_Limu1.index, movement_magnitude1, label='Right Leg', linewidth=2)
        plt.plot(df_Limu2.index, movement_magnitude2, label='Left Leg', linewidth=2)
        plt.scatter(df_Limu1.index[peaks1], movement_magnitude1[peaks1], c='red', label='Peaks Right', marker='x')
        plt.scatter(df_Limu1.index[valleys1], movement_magnitude1[valleys1], c='blue', label='Valleys Right', marker='o')
        plt.scatter(df_Limu2.index[peaks2], movement_magnitude2[peaks2], c='green', label='Peaks Left', marker='x')
        plt.scatter(df_Limu2.index[valleys2], movement_magnitude2[valleys2], c='orange', label='Valleys Left', marker='o')
        plt.xlabel('Timestamp')
        plt.ylabel('Movement Magnitude')
        plt.title('Movement Magnitude with Detected Peaks and Valleys')
        plt.legend()
        plt.show()

    return metrics_data

def save_metrics_to_txt(metrics, file_path):
    main_directory = "Gait Metrics Data"
    sub_directory = "SideStepping Metrics Data"

    directory = os.path.join(main_directory, sub_directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    full_path = os.path.join(directory, file_path)

    with open(full_path, 'w') as file:
        json.dump(metrics, file, indent=4)

def main():
    right_df = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/Apostolidis Kosmas/07_linear_9steps/Right_2024-06-18T10.32.56.873_C172766109C5_LinearAcceleration.csv')
    left_df = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/Apostolidis Kosmas/07_linear_9steps/Left_2024-06-18T10.32.56.873_E15561CB9161_LinearAcceleration.csv')

    right_df = preprocess_imu_data(right_df)
    left_df = preprocess_imu_data(left_df)

    metrics_data = getMetricsGaitNew01(right_df, left_df, plot_diagrams=True)

    if metrics_data:
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{datetime_string}_SideStepping_metrics.txt"
        save_metrics_to_txt(metrics_data, filename)
        print("Metrics saved to:", filename)
    else:
        print("Insufficient data to calculate metrics.")

if __name__ == "__main__":
    main()