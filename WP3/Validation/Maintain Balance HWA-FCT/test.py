import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load IMU data from four trials
imu_data_trial1 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/TrunkRotation/NewSitting1_right/quick/back_E25AD03D0194_2024-02-08_12_22_38.csv')
imu_data_trial2 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/TrunkRotation/NewSitting1_right/quick/back_E25AD03D0194_2024-02-08_12_27_14.csv')
imu_data_trial3 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/TrunkRotation/NewSitting1_right/quick/back_E25AD03D0194_2024-02-08_12_30_11.csv')
imu_data_trial4 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/TrunkRotation/NewSitting1_right/quick/back_E25AD03D0194_2024-02-08_12_32_39.csv')

def quaternion_to_euler(w, x, y, z):
    t0 = +2.0 * (w * z + x * y)
    t1 = +1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t0, t1)
    
    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch = np.arcsin(t2)
    
    t3 = +2.0 * (w * x + y * z)
    t4 = +1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(t3, t4)
    
    return yaw, pitch, roll

def process_data(data):
    yaw_list = []
    roll_list = []
    for _, row in data.iterrows():
        w, x, y, z = row['W(number)'], row['X(number)'], row['Y (number)'], row['Z (number)']
        yaw, pitch, roll = quaternion_to_euler(w, x, y, z)
        yaw_list.append(yaw)
        roll_list.append(roll)
    return np.array(yaw_list), np.array(roll_list)

# Process Data to Get Yaw and Roll
yaw_trial1, roll_trial1 = process_data(imu_data_trial1)
yaw_trial2, roll_trial2 = process_data(imu_data_trial2)
yaw_trial3, roll_trial3 = process_data(imu_data_trial3)
yaw_trial4, roll_trial4 = process_data(imu_data_trial4)

# Ensure all trials are of the same length
min_length = min(len(yaw_trial1), len(yaw_trial2), len(yaw_trial3), len(yaw_trial4))
yaw_trial1 = yaw_trial1[:min_length]
yaw_trial2 = yaw_trial2[:min_length]
yaw_trial3 = yaw_trial3[:min_length]
yaw_trial4 = yaw_trial4[:min_length]

roll_trial1 = roll_trial1[:min_length]
roll_trial2 = roll_trial2[:min_length]
roll_trial3 = roll_trial3[:min_length]
roll_trial4 = roll_trial4[:min_length]

# Calculate Mean and Standard Deviation for Yaw
mean_yaw_trial1 = np.mean(yaw_trial1)
std_yaw_trial1 = np.std(yaw_trial1)
mean_yaw_trial2 = np.mean(yaw_trial2)
std_yaw_trial2 = np.std(yaw_trial2)
mean_yaw_trial3 = np.mean(yaw_trial3)
std_yaw_trial3 = np.std(yaw_trial3)
mean_yaw_trial4 = np.mean(yaw_trial4)
std_yaw_trial4 = np.std(yaw_trial4)

# Calculate Mean and Standard Deviation for Roll
mean_roll_trial1 = np.mean(roll_trial1)
std_roll_trial1 = np.std(roll_trial1)
mean_roll_trial2 = np.mean(roll_trial2)
std_roll_trial2 = np.std(roll_trial2)
mean_roll_trial3 = np.mean(roll_trial3)
std_roll_trial3 = np.std(roll_trial3)
mean_roll_trial4 = np.mean(roll_trial4)
std_roll_trial4 = np.std(roll_trial4)

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

# Calculate ICC for Yaw
yaw_data = np.array([yaw_trial1, yaw_trial2, yaw_trial3, yaw_trial4])
icc_yaw = calculate_icc(yaw_data)

# Calculate ICC for Roll
roll_data = np.array([roll_trial1, roll_trial2, roll_trial3, roll_trial4])
icc_roll = calculate_icc(roll_data)

def bland_altman_plot(data1, data2, ax, title):
    mean = np.mean([data1, data2], axis=0)
    diff = data1 - data2
    md = np.mean(diff)
    sd = np.std(diff)

    ax.scatter(mean, diff, alpha=0.6)
    ax.axhline(md, color='gray', linestyle='--')
    ax.axhline(md + 1.96*sd, color='red', linestyle='--')
    ax.axhline(md - 1.96*sd, color='red', linestyle='--')
    ax.set_title(title, fontsize=8)
    ax.set_xlabel('Mean of Two Trials')
    ax.set_ylabel('Difference Between Two Trials')

def plot_correlation_and_rmse(data1, data2, ax, trial1_label, trial2_label):
    ax.scatter(data1, data2, alpha=0.6, label=f'{trial1_label} vs {trial2_label}')
    correlation = np.corrcoef(data1, data2)[0, 1]
    rmse = np.sqrt(mean_squared_error(data1, data2))
    ax.plot([min(data1), max(data1)], [min(data1), max(data1)], 'r--')
    ax.set_title(f'Correlation: {correlation:.2f}, RMSE: {rmse:.2f}')
    ax.set_xlabel(f'{trial1_label}')
    ax.set_ylabel(f'{trial2_label}')
    return correlation, rmse

# Create combined figure for Mean and Standard Deviation with subplots
fig1, axes1 = plt.subplots(2, 2, figsize=(18, 12))
fig1.suptitle('Yaw and Roll Analysis - Mean and Standard Deviation, Bland-Altman Plots', fontsize=16)

# # Plot Mean and Standard Deviation for Each Trial (Yaw)
# axes1[0, 0].plot(yaw_trial1, label='Trial 1 Yaw', alpha=0.6)
# axes1[0, 0].plot(yaw_trial2, label='Trial 2 Yaw', alpha=0.6)
# axes1[0, 0].plot(yaw_trial3, label='Trial 3 Yaw', alpha=0.6)
# axes1[0, 0].plot(yaw_trial4, label='Trial 4 Yaw', alpha=0.6)
# axes1[0, 0].axhline(mean_yaw_trial1, color='blue', linestyle='--', label='Mean Yaw Trial 1')
# axes1[0, 0].axhline(mean_yaw_trial2, color='orange', linestyle='--', label='Mean Yaw Trial 2')
# axes1[0, 0].axhline(mean_yaw_trial3, color='green', linestyle='--', label='Mean Yaw Trial 3')
# axes1[0, 0].axhline(mean_yaw_trial4, color='red', linestyle='--', label='Mean Yaw Trial 4')
# axes1[0, 0].fill_between(range(min_length), mean_yaw_trial1-std_yaw_trial1, mean_yaw_trial1+std_yaw_trial1, color='blue', alpha=0.2)
# axes1[0, 0].fill_between(range(min_length), mean_yaw_trial2-std_yaw_trial2, mean_yaw_trial2+std_yaw_trial2, color='orange', alpha=0.2)
# axes1[0, 0].fill_between(range(min_length), mean_yaw_trial3-std_yaw_trial3, mean_yaw_trial3+std_yaw_trial3, color='green', alpha=0.2)
# axes1[0, 0].fill_between(range(min_length), mean_yaw_trial4-std_yaw_trial4, mean_yaw_trial4+std_yaw_trial4, color='red', alpha=0.2)
# axes1[0, 0].set_title('Yaw Data with Mean \nand Standard Deviation')
# axes1[0, 0].set_xlabel('Sample')
# axes1[0, 0].set_ylabel('Yaw (radians)')
# axes1[0, 0].legend(fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))

# # Plot Mean and Standard Deviation for Each Trial (Roll)
# axes1[1, 0].plot(roll_trial1, label='Trial 1 Roll', alpha=0.6)
# axes1[1, 0].plot(roll_trial2, label='Trial 2 Roll', alpha=0.6)
# axes1[1, 0].plot(roll_trial3, label='Trial 3 Roll', alpha=0.6)
# axes1[1, 0].plot(roll_trial4, label='Trial 4 Roll', alpha=0.6)
# axes1[1, 0].axhline(mean_roll_trial1, color='blue', linestyle='--', label='Mean Roll Trial 1')
# axes1[1, 0].axhline(mean_roll_trial2, color='orange', linestyle='--', label='Mean Roll Trial 2')
# axes1[1, 0].axhline(mean_roll_trial3, color='green', linestyle='--', label='Mean Roll Trial 3')
# axes1[1, 0].axhline(mean_roll_trial4, color='red', linestyle='--', label='Mean Roll Trial 4')
# axes1[1, 0].fill_between(range(min_length), mean_roll_trial1-std_roll_trial1, mean_roll_trial1+std_roll_trial1, color='blue', alpha=0.2)
# axes1[1, 0].fill_between(range(min_length), mean_roll_trial2-std_roll_trial2, mean_roll_trial2+std_roll_trial2, color='orange', alpha=0.2)
# axes1[1, 0].fill_between(range(min_length), mean_roll_trial3-std_roll_trial3, mean_roll_trial3+std_roll_trial3, color='green', alpha=0.2)
# axes1[1, 0].fill_between(range(min_length), mean_roll_trial4-std_roll_trial4, mean_roll_trial4+std_roll_trial4, color='red', alpha=0.2)
# axes1[1, 0].set_title('Roll Data with Mean \nand Standard Deviation')
# axes1[1, 0].set_xlabel('Sample')
# axes1[1, 0].set_ylabel('Roll (radians)')
# axes1[1, 0].legend(fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))

# Bland-Altman Plots for Yaw and Roll
bland_altman_plot(yaw_trial1, yaw_trial2, axes1[0, 0], 'Bland-Altman Plot for Yaw Trial FCT-Eye closed and FCT-Eye open')
bland_altman_plot(yaw_trial1, yaw_trial3, axes1[0, 1], 'Bland-Altman Plot for Yaw FCT-Eye closed and 3')
bland_altman_plot(roll_trial1, roll_trial2, axes1[1, 0], 'Bland-Altman Plot for Roll Trial 1 and 2')
bland_altman_plot(roll_trial1, roll_trial3, axes1[1, 1], 'Bland-Altman Plot for Roll Trial 1 and 3')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Create separate figure for Correlation and RMSE
fig2, axes2 = plt.subplots(3, 3, figsize=(18, 18))
fig2.suptitle('Yaw and Roll Analysis - Correlation and RMSE', fontsize=16)

# Correlation and RMSE Plots for Yaw
plot_correlation_and_rmse(yaw_trial1, yaw_trial2, axes2[0, 0], 'Trial 1 Yaw', 'Trial 2 Yaw')
plot_correlation_and_rmse(yaw_trial1, yaw_trial3, axes2[0, 1], 'Trial 1 Yaw', 'Trial 3 Yaw')
plot_correlation_and_rmse(yaw_trial1, yaw_trial4, axes2[0, 2], 'Trial 1 Yaw', 'Trial 4 Yaw')
plot_correlation_and_rmse(yaw_trial2, yaw_trial3, axes2[1, 0], 'Trial 2 Yaw', 'Trial 3 Yaw')
plot_correlation_and_rmse(yaw_trial2, yaw_trial4, axes2[1, 1], 'Trial 2 Yaw', 'Trial 4 Yaw')
plot_correlation_and_rmse(yaw_trial3, yaw_trial4, axes2[1, 2], 'Trial 3 Yaw', 'Trial 4 Yaw')

# Correlation and RMSE Plots for Roll
plot_correlation_and_rmse(roll_trial1, roll_trial2, axes2[2, 0], 'Trial 1 Roll', 'Trial 2 Roll')
plot_correlation_and_rmse(roll_trial1, roll_trial3, axes2[2, 1], 'Trial 1 Roll', 'Trial 3 Roll')
plot_correlation_and_rmse(roll_trial1, roll_trial4, axes2[2, 2], 'Trial 1 Roll', 'Trial 4 Roll')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Print ICC values
print(f'ICC for Yaw: {icc_yaw}')
print(f'ICC for Roll: {icc_roll}')
