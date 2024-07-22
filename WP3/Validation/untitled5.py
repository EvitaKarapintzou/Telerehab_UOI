# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 19:30:09 2024

@author: User
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load IMU data from multiple trials
imu_data_trial1 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/head_FEAC84C53DE7_2024-02-08_14_25_45.csv')
imu_data_trial2 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/FEAC84C53DE7_2024-02-08_14_38_07_kefali.csv')
imu_data_trial3 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/FEAC84C53DE7_2024-02-08_14_28_51_kefali.csv')
imu_data_trial4 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/FEAC84C53DE7_2024-02-08_14_44_03_kefali.csv')
imu_data_trial5 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/FEAC84C53DE7_2024-02-08_14_49_24_kefali.csv')

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
yaw_trial4 = process_data(imu_data_trial4)
yaw_trial5 = process_data(imu_data_trial5)

# Ensure all trials are of the same length
min_length = min(len(yaw_trial1), len(yaw_trial2), len(yaw_trial3), len(yaw_trial4), len(yaw_trial5))
yaw_trial1 = yaw_trial1[:min_length]
yaw_trial2 = yaw_trial2[:min_length]
yaw_trial3 = yaw_trial3[:min_length]
yaw_trial4 = yaw_trial4[:min_length]
yaw_trial5 = yaw_trial5[:min_length]

# Calculate Mean and Standard Deviation
mean_yaw_trial1 = np.mean(yaw_trial1)
std_yaw_trial1 = np.std(yaw_trial1)

mean_yaw_trial2 = np.mean(yaw_trial2)
std_yaw_trial2 = np.std(yaw_trial2)

mean_yaw_trial3 = np.mean(yaw_trial3)
std_yaw_trial3 = np.std(yaw_trial3)

mean_yaw_trial4 = np.mean(yaw_trial4)
std_yaw_trial4 = np.std(yaw_trial4)

mean_yaw_trial5 = np.mean(yaw_trial5)
std_yaw_trial5 = np.std(yaw_trial5)

print(f'Mean Yaw Trial 1: {mean_yaw_trial1}, STD Yaw Trial 1: {std_yaw_trial1}')
print(f'Mean Yaw Trial 2: {mean_yaw_trial2}, STD Yaw Trial 2: {std_yaw_trial2}')
print(f'Mean Yaw Trial 3: {mean_yaw_trial3}, STD Yaw Trial 3: {std_yaw_trial3}')
print(f'Mean Yaw Trial 4: {mean_yaw_trial4}, STD Yaw Trial 4: {std_yaw_trial4}')
print(f'Mean Yaw Trial 5: {mean_yaw_trial5}, STD Yaw Trial 5: {std_yaw_trial5}')

# Plot Mean and Standard Deviation for Each Trial
plt.figure(figsize=(12, 6))

plt.plot(yaw_trial1, label='Trial 1 Yaw', alpha=0.6)
plt.plot(yaw_trial2, label='Trial 2 Yaw', alpha=0.6)
plt.plot(yaw_trial3, label='Trial 3 Yaw', alpha=0.6)
plt.plot(yaw_trial4, label='Trial 4 Yaw', alpha=0.6)
plt.plot(yaw_trial5, label='Trial 5 Yaw', alpha=0.6)

# Plot Mean and STD
plt.axhline(mean_yaw_trial1, color='blue', linestyle='--', label='Mean Yaw Trial 1')
plt.axhline(mean_yaw_trial2, color='orange', linestyle='--', label='Mean Yaw Trial 2')
plt.axhline(mean_yaw_trial3, color='green', linestyle='--', label='Mean Yaw Trial 3')
plt.axhline(mean_yaw_trial4, color='red', linestyle='--', label='Mean Yaw Trial 4')
plt.axhline(mean_yaw_trial5, color='purple', linestyle='--', label='Mean Yaw Trial 5')

plt.fill_between(range(min_length), mean_yaw_trial1-std_yaw_trial1, mean_yaw_trial1+std_yaw_trial1, color='blue', alpha=0.2)
plt.fill_between(range(min_length), mean_yaw_trial2-std_yaw_trial2, mean_yaw_trial2+std_yaw_trial2, color='orange', alpha=0.2)
plt.fill_between(range(min_length), mean_yaw_trial3-std_yaw_trial3, mean_yaw_trial3+std_yaw_trial3, color='green', alpha=0.2)
plt.fill_between(range(min_length), mean_yaw_trial4-std_yaw_trial4, mean_yaw_trial4+std_yaw_trial4, color='red', alpha=0.2)
plt.fill_between(range(min_length), mean_yaw_trial5-std_yaw_trial5, mean_yaw_trial5+std_yaw_trial5, color='purple', alpha=0.2)

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

yaw_data = np.array([yaw_trial1, yaw_trial2, yaw_trial3, yaw_trial4, yaw_trial5])
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
bland_altman_plot(yaw_trial1, yaw_trial4, 'Bland-Altman Plot for Trial 1 and Trial 4')
bland_altman_plot(yaw_trial1, yaw_trial5, 'Bland-Altman Plot for Trial 1 and Trial 5')
bland_altman_plot(yaw_trial2, yaw_trial3, 'Bland-Altman Plot for Trial 2 and Trial 3')
bland_altman_plot(yaw_trial2, yaw_trial4, 'Bland-Altman Plot for Trial 2 and Trial 4')
bland_altman_plot(yaw_trial2, yaw_trial5, 'Bland-Altman Plot for Trial 2 and Trial 5')
bland_altman_plot(yaw_trial3, yaw_trial4, 'Bland-Altman Plot for Trial 3 and Trial 4')
bland_altman_plot(yaw_trial3, yaw_trial5, 'Bland-Altman Plot for Trial 3 and Trial 5')
bland_altman_plot(yaw_trial4, yaw_trial5, 'Bland-Altman Plot for Trial 4 and Trial 5')

# Correlation and RMSE
def plot_correlation_and_rmse(data1, data2, trial1_label, trial2_label):
    plt.scatter(data1, data2, alpha=0.6, label=f'{trial1_label} vs {trial2_label}')
    correlation = np.corrcoef(data1, data2)[0, 1]
    rmse = np.sqrt(mean_squared_error(data1, data2))
    return correlation, rmse

# Combined plot for Correlation and RMSE
plt.figure(figsize=(25, 27))

plt.subplot(3, 3, 1)
corr_12, rmse_12 = plot_correlation_and_rmse(yaw_trial1, yaw_trial2, 'Trial 1 Yaw', 'Trial 2 Yaw')
plt.plot([min(yaw_trial1), max(yaw_trial1)], [min(yaw_trial1), max(yaw_trial1)], 'r--')
plt.title(f'Correlation: {corr_12:.2f}, RMSE: {rmse_12:.2f}')
plt.xlabel('Trial 1 Yaw')
plt.ylabel('Trial 2 Yaw')

plt.subplot(3, 3, 2)
corr_13, rmse_13 = plot_correlation_and_rmse(yaw_trial1, yaw_trial3, 'Trial 1 Yaw', 'Trial 3 Yaw')
plt.plot([min(yaw_trial1), max(yaw_trial1)], [min(yaw_trial1), max(yaw_trial1)], 'r--')
plt.title(f'Correlation: {corr_13:.2f}, RMSE: {rmse_13:.2f}')
plt.xlabel('Trial 1 Yaw')
plt.ylabel('Trial 3 Yaw')

plt.subplot(3, 3, 3)
corr_14, rmse_14 = plot_correlation_and_rmse(yaw_trial1, yaw_trial4, 'Trial 1 Yaw', 'Trial 4 Yaw')
plt.plot([min(yaw_trial1), max(yaw_trial1)], [min(yaw_trial1), max(yaw_trial1)], 'r--')
plt.title(f'Correlation: {corr_14:.2f}, RMSE: {rmse_14:.2f}')
plt.xlabel('Trial 1 Yaw')
plt.ylabel('Trial 4 Yaw')

plt.subplot(3, 3, 4)
corr_15, rmse_15 = plot_correlation_and_rmse(yaw_trial1, yaw_trial5, 'Trial 1 Yaw', 'Trial 5 Yaw')
plt.plot([min(yaw_trial1), max(yaw_trial1)], [min(yaw_trial1), max(yaw_trial1)], 'r--')
plt.title(f'Correlation: {corr_15:.2f}, RMSE: {rmse_15:.2f}')
plt.xlabel('Trial 1 Yaw')
plt.ylabel('Trial 5 Yaw')

plt.subplot(3, 3, 5)
corr_23, rmse_23 = plot_correlation_and_rmse(yaw_trial2, yaw_trial3, 'Trial 2 Yaw', 'Trial 3 Yaw')
plt.plot([min(yaw_trial2), max(yaw_trial2)], [min(yaw_trial2), max(yaw_trial2)], 'r--')
plt.title(f'Correlation: {corr_23:.2f}, RMSE: {rmse_23:.2f}')
plt.xlabel('Trial 2 Yaw')
plt.ylabel('Trial 3 Yaw')

plt.subplot(3, 3, 6)
corr_24, rmse_24 = plot_correlation_and_rmse(yaw_trial2, yaw_trial4, 'Trial 2 Yaw', 'Trial 4 Yaw')
plt.plot([min(yaw_trial2), max(yaw_trial2)], [min(yaw_trial2), max(yaw_trial2)], 'r--')
plt.title(f'Correlation: {corr_24:.2f}, RMSE: {rmse_24:.2f}')
plt.xlabel('Trial 2 Yaw')
plt.ylabel('Trial 4 Yaw')

plt.subplot(3, 3, 7)
corr_25, rmse_25 = plot_correlation_and_rmse(yaw_trial2, yaw_trial5, 'Trial 2 Yaw', 'Trial 5 Yaw')
plt.plot([min(yaw_trial2), max(yaw_trial2)], [min(yaw_trial2), max(yaw_trial2)], 'r--')
plt.title(f'Correlation: {corr_25:.2f}, RMSE: {rmse_25:.2f}')
plt.xlabel('Trial 2 Yaw')
plt.ylabel('Trial 5 Yaw')

plt.subplot(3, 3, 8)
corr_34, rmse_34 = plot_correlation_and_rmse(yaw_trial3, yaw_trial4, 'Trial 3 Yaw', 'Trial 4 Yaw')
plt.plot([min(yaw_trial3), max(yaw_trial3)], [min(yaw_trial3), max(yaw_trial3)], 'r--')
plt.title(f'Correlation: {corr_34:.2f}, RMSE: {rmse_34:.2f}')
plt.xlabel('Trial 3 Yaw')
plt.ylabel('Trial 4 Yaw')

plt.subplot(3, 3, 9)
corr_35, rmse_35 = plot_correlation_and_rmse(yaw_trial3, yaw_trial5, 'Trial 3 Yaw', 'Trial 5 Yaw')
plt.plot([min(yaw_trial3), max(yaw_trial3)], [min(yaw_trial3), max(yaw_trial3)], 'r--')
plt.title(f'Correlation: {corr_35:.2f}, RMSE: {rmse_35:.2f}')
plt.xlabel('Trial 3 Yaw')
plt.ylabel('Trial 5 Yaw')

plt.tight_layout()
plt.show()

# Print Correlation and RMSE
print(f'Trial 1 vs Trial 2 - Correlation: {corr_12:.2f}, RMSE: {rmse_12:.2f}')
print(f'Trial 1 vs Trial 3 - Correlation: {corr_13:.2f}, RMSE: {rmse_13:.2f}')
print(f'Trial 1 vs Trial 4 - Correlation: {corr_14:.2f}, RMSE: {rmse_14:.2f}')
print(f'Trial 1 vs Trial 5 - Correlation: {corr_15:.2f}, RMSE: {rmse_15:.2f}')
print(f'Trial 2 vs Trial 3 - Correlation: {corr_23:.2f}, RMSE: {rmse_23:.2f}')
print(f'Trial 2 vs Trial 4 - Correlation: {corr_24:.2f}, RMSE: {rmse_24:.2f}')
print(f'Trial 2 vs Trial 5 - Correlation: {corr_25:.2f}, RMSE: {rmse_25:.2f}')
print(f'Trial 3 vs Trial 4 - Correlation: {corr_34:.2f}, RMSE: {rmse_34:.2f}')
print(f'Trial 3 vs Trial 5 - Correlation: {corr_35:.2f}, RMSE: {rmse_35:.2f}')