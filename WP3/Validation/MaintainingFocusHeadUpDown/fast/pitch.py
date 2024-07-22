import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load IMU data from three trials
imu_data_trial1 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/MaintainingFocusHeadUpDown/fast/2024-02-16_14_32_38_old_sitting_2_fast_1/head_E25AD03D0194_2024-02-16_14_32_38.csv')
imu_data_trial2 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/MaintainingFocusHeadUpDown/fast/2024-02-16_14_34_26_old_sitting_2_fast_2/head_E25AD03D0194_2024-02-16_14_34_26.csv')
imu_data_trial3 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/MaintainingFocusHeadUpDown/fast/2024-02-16_14_36_18_old_sitting_2_fast_3/head_E25AD03D0194_2024-02-16_14_36_18.csv')


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
    pitch_list = []
    for _, row in data.iterrows():
        w, x, y, z = row['W(number)'], row['X(number)'], row['Y (number)'], row['Z (number)']
        _, pitch, _ = quaternion_to_euler(w, x, y, z)
        pitch_list.append(pitch)
    return np.array(pitch_list)

# Process Data to Get Pitch
pitch_trial1 = process_data(imu_data_trial1)
pitch_trial2 = process_data(imu_data_trial2)
pitch_trial3 = process_data(imu_data_trial3)

# Ensure all trials are of the same length
min_length = min(len(pitch_trial1), len(pitch_trial2), len(pitch_trial3))
pitch_trial1 = pitch_trial1[:min_length]
pitch_trial2 = pitch_trial2[:min_length]
pitch_trial3 = pitch_trial3[:min_length]

# Calculate Mean and Standard Deviation for Pitch
mean_pitch_trial1 = np.mean(pitch_trial1)
std_pitch_trial1 = np.std(pitch_trial1)

mean_pitch_trial2 = np.mean(pitch_trial2)
std_pitch_trial2 = np.std(pitch_trial2)

mean_pitch_trial3 = np.mean(pitch_trial3)
std_pitch_trial3 = np.std(pitch_trial3)

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

# Calculate ICC for Pitch
pitch_data = np.array([pitch_trial1, pitch_trial2, pitch_trial3])
icc_pitch = calculate_icc(pitch_data)

def bland_altman_plot(data1, data2, ax, title):
    mean = np.mean([data1, data2], axis=0)
    diff = data1 - data2
    md = np.mean(diff)
    sd = np.std(diff)

    ax.scatter(mean, diff, alpha=0.6)
    ax.axhline(md, color='gray', linestyle='--')
    ax.axhline(md + 1.96*sd, color='red', linestyle='--')
    ax.axhline(md - 1.96*sd, color='red', linestyle='--')
    ax.set_title(title, fontsize=8)  # Setting a smaller font size for the title
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

# Create combined figure for Mean and Standard Deviation with 1x4 subplots
fig1, axes1 = plt.subplots(2, 2, figsize=(15, 10))
fig1.suptitle('Pitch Analysis - Mean and Standard Deviation', fontsize=16)

# Plot Mean and Standard Deviation for Each Trial
axes1[0, 0].plot(pitch_trial1, label='Trial 1 Pitch', alpha=0.6)
axes1[0, 0].plot(pitch_trial2, label='Trial 2 Pitch', alpha=0.6)
axes1[0, 0].plot(pitch_trial3, label='Trial 3 Pitch', alpha=0.6)
axes1[0, 0].axhline(mean_pitch_trial1, color='blue', linestyle='--', label='Mean Pitch Trial 1')
axes1[0, 0].axhline(mean_pitch_trial2, color='orange', linestyle='--', label='Mean Pitch Trial 2')
axes1[0, 0].axhline(mean_pitch_trial3, color='green', linestyle='--', label='Mean Pitch Trial 3')
axes1[0, 0].fill_between(range(min_length), mean_pitch_trial1-std_pitch_trial1, mean_pitch_trial1+std_pitch_trial1, color='blue', alpha=0.2)
axes1[0, 0].fill_between(range(min_length), mean_pitch_trial2-std_pitch_trial2, mean_pitch_trial2+std_pitch_trial2, color='orange', alpha=0.2)
axes1[0, 0].fill_between(range(min_length), mean_pitch_trial3-std_pitch_trial3, mean_pitch_trial3+std_pitch_trial3, color='green', alpha=0.2)
axes1[0, 0].set_title('Pitch Data with Mean and Standard Deviation')
axes1[0, 0].set_xlabel('Sample')
axes1[0, 0].set_ylabel('Pitch (radians)')
axes1[0, 0].legend(fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))

# Bland-Altman Plots
bland_altman_plot(pitch_trial1, pitch_trial2, axes1[0, 1], 'Bland-Altman Plot for Pitch Trial 1 and 2')
bland_altman_plot(pitch_trial1, pitch_trial3, axes1[1, 0], 'Bland-Altman Plot for Pitch Trial 1 and 3')
bland_altman_plot(pitch_trial2, pitch_trial3, axes1[1, 1], 'Bland-Altman Plot for Pitch Trial 2 and 3')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Create separate figure for Correlation and RMSE
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
fig2.suptitle('Pitch Analysis - Correlation and RMSE', fontsize=16)

# Correlation and RMSE Plots
corr_12, rmse_12 = plot_correlation_and_rmse(pitch_trial1, pitch_trial2, axes2[0], 'Trial 1 Pitch', 'Trial 2 Pitch')
corr_13, rmse_13 = plot_correlation_and_rmse(pitch_trial1, pitch_trial3, axes2[1], 'Trial 1 Pitch', 'Trial 3 Pitch')
corr_23, rmse_23 = plot_correlation_and_rmse(pitch_trial2, pitch_trial3, axes2[2], 'Trial 2 Pitch', 'Trial 3 Pitch')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Print ICC value
print(f'ICC for Pitch: {icc_pitch}')

# Print Correlation and RMSE
print(f'Trial 1 vs Trial 2 (Pitch) - Correlation: {corr_12:.2f}, RMSE: {rmse_12:.2f}')
print(f'Trial 1 vs Trial 3 (Pitch) - Correlation: {corr_13:.2f}, RMSE: {rmse_13:.2f}')
print(f'Trial 2 vs Trial 3 (Pitch) - Correlation: {corr_23:.2f}, RMSE: {rmse_23:.2f}')
