# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 19:52:17 2024

@author: User
"""



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load IMU data from multiple trials
imu_data_trial1 = pd.read_csv(r'C:\Users\User\Desktop\LAB\Validation\head_FEAC84C53DE7_2024-02-08_14_25_45.csv')
imu_data_trial2 = pd.read_csv(r'C:\Users\User\Desktop\LAB\Validation\FEAC84C53DE7_2024-02-08_14_38_07_kefali.csv')
imu_data_trial3 = pd.read_csv(r'C:\Users\User\Desktop\LAB\Validation\FEAC84C53DE7_2024-02-08_14_28_51_kefali.csv')

def quaternion_to_euler(w, x, y, z):
    """
    Convert a quaternion into Euler angles (yaw, pitch, roll)
    yaw is the rotation around the z-axis (in radians)
    pitch is the rotation around the y-axis (in radians)
    roll is the rotation around the x-axis (in radians)
    """
    t0 = +2.0 * (w * z + x * y)
    t1 = +1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t0, t1)
    
    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)  # Clipping to handle numerical errors
    pitch = np.arcsin(t2)
    
    t3 = +2.0 * (w * x + y * z)
    t4 = +1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(t3, t4)
    
    return yaw, pitch, roll

def process_data(data):
    yaw_list = []
    for _, row in data.iterrows():
        w, x, y, z = row['W(number)'], row['X(number)'], row['Y (number)'], row['Z (number)']
        yaw, pitch, roll = quaternion_to_euler(w, x, y, z)
        yaw_list.append(yaw)
    return np.array(yaw_list)

# Process Data to Get Yaw
yaw_trial1 = process_data(imu_data_trial1)
yaw_trial2 = process_data(imu_data_trial2)
yaw_trial3 = process_data(imu_data_trial3)

# Ensure all trials are of the same length
min_length = min(len(yaw_trial1), len(yaw_trial2), len(yaw_trial3))
yaw_trial1 = yaw_trial1[:min_length]
yaw_trial2 = yaw_trial2[:min_length]
yaw_trial3 = yaw_trial3[:min_length]

# Calculate Mean and Standard Deviation
mean_yaw_trial1 = np.mean(yaw_trial1)
std_yaw_trial1 = np.std(yaw_trial1)

mean_yaw_trial2 = np.mean(yaw_trial2)
std_yaw_trial2 = np.std(yaw_trial2)

mean_yaw_trial3 = np.mean(yaw_trial3)
std_yaw_trial3 = np.std(yaw_trial3)

print(f'Mean Yaw Trial 1: {mean_yaw_trial1}, STD Yaw Trial 1: {std_yaw_trial1}')
print(f'Mean Yaw Trial 2: {mean_yaw_trial2}, STD Yaw Trial 2: {std_yaw_trial2}')
print(f'Mean Yaw Trial 3: {mean_yaw_trial3}, STD Yaw Trial 3: {std_yaw_trial3}')

# Plot Mean and Standard Deviation for Each Trial
plt.figure(figsize=(12, 6))

plt.plot(yaw_trial1, label='Trial 1 Yaw', alpha=0.6)
plt.plot(yaw_trial2, label='Trial 2 Yaw', alpha=0.6)
plt.plot(yaw_trial3, label='Trial 3 Yaw', alpha=0.6)

# Plot Mean and STD
plt.axhline(mean_yaw_trial1, color='blue', linestyle='--', label='Mean Yaw Trial 1')
plt.axhline(mean_yaw_trial2, color='orange', linestyle='--', label='Mean Yaw Trial 2')
plt.axhline(mean_yaw_trial3, color='green', linestyle='--', label='Mean Yaw Trial 3')

plt.fill_between(range(min_length), mean_yaw_trial1-std_yaw_trial1, mean_yaw_trial1+std_yaw_trial1, color='blue', alpha=0.2)
plt.fill_between(range(min_length), mean_yaw_trial2-std_yaw_trial2, mean_yaw_trial2+std_yaw_trial2, color='orange', alpha=0.2)
plt.fill_between(range(min_length), mean_yaw_trial3-std_yaw_trial3, mean_yaw_trial3+std_yaw_trial3, color='green', alpha=0.2)

plt.title('Yaw Data with Mean and Standard Deviation from Multiple Trials')
plt.xlabel('Sample')
plt.ylabel('Yaw (radians)')
plt.legend()
plt.show()

def calculate_icc(data):
    k = len(data)
    n = len(data[0])
    mean_ratings = np.mean(data, axis=0)
    grand_mean = np.mean(mean_ratings)
    
    ss_between = sum((mean_ratings - grand_mean) ** 2) * n
    ss_within = sum(sum((data[i] - mean_ratings) ** 2) for i in range(k))
    
    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (k * (n - 1))
    
    icc = (ms_between - ms_within) / (ms_between + (k - 1) * ms_within)
    return icc

yaw_data = np.array([yaw_trial1, yaw_trial2, yaw_trial3])
icc_yaw = calculate_icc(yaw_data)
print(f'ICC for Yaw: {icc_yaw}')

# Bland-Altman Plot
def bland_altman_plot(data1, data2, title):
    mean = np.mean([data1, data2], axis=0)
    diff = data1 - data2
    md = np.mean(diff)
    sd = np.std(diff)

    plt.figure(figsize=(12, 6))
    plt.scatter(mean, diff, alpha=0.6)
    plt.axhline(md, color='gray', linestyle='--')
    plt.axhline(md + 1.96*sd, color='red', linestyle='--')
    plt.axhline(md - 1.96*sd, color='red', linestyle='--')
    plt.title(title)
    plt.xlabel('Mean of Two Trials')
    plt.ylabel('Difference Between Two Trials')
    plt.show()

bland_altman_plot(yaw_trial1, yaw_trial2, 'Bland-Altman Plot for Trial 1 and Trial 2')
bland_altman_plot(yaw_trial1, yaw_trial3, 'Bland-Altman Plot for Trial 1 and Trial 3')
bland_altman_plot(yaw_trial2, yaw_trial3, 'Bland-Altman Plot for Trial 2 and Trial 3')

# Correlation and RMSE
def plot_correlation_and_rmse(data1, data2, title):
    plt.figure(figsize=(12, 6))
    plt.scatter(data1, data2, alpha=0.6)
    plt.plot([min(data1), max(data1)], [min(data1), max(data1)], 'r--')  # Diagonal line for reference
    plt.title(title)
    plt.xlabel('Trial 1 Yaw')
    plt.ylabel('Trial 2 Yaw')
    plt.show()

    correlation = np.corrcoef(data1, data2)[0, 1]
    rmse = np.sqrt(mean_squared_error(data1, data2))
    print(f'{title} - Correlation: {correlation}, RMSE: {rmse}')
    return correlation, rmse

# Plot Correlation and RMSE for each pair of trials
corr_12, rmse_12 = plot_correlation_and_rmse(yaw_trial1, yaw_trial2, 'Correlation and RMSE for Trial 1 and Trial 2')
corr_13, rmse_13 = plot_correlation_and_rmse(yaw_trial1, yaw_trial3, 'Correlation and RMSE for Trial 1 and Trial 3')
corr_23, rmse_23 = plot_correlation_and_rmse(yaw_trial2, yaw_trial3, 'Correlation and RMSE for Trial 2 and Trial 3')
