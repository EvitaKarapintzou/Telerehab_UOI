import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load IMU data from four trials
#BACKWARD
imu_data_trial1 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/anteroposteriorDirection/Back_2024-03-04T14.03.50.795_E25AD03D0194_Quaternion.csv')
imu_data_trial2 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/anteroposteriorDirection/Back_2024-03-04T14.06.04.032_E25AD03D0194_Quaternion.csv')
#FORWARD
# imu_data_trial3 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/anteroposteriorDirection/FEAC84C53DE7_2024-02-08_14_28_51_kefali.csv')
# imu_data_trial4 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/anteroposteriorDirection/FEAC84C53DE7_2024-02-08_14_44_03_kefali.csv')


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
    pitch_list = []
    roll_list = []
    for _, row in data.iterrows():
        w, x, y, z = row['w (number)'], row['x (number)'], row['y (number)'], row['z (number)']
        yaw, pitch, roll = quaternion_to_euler(w, x, y, z)
        yaw_list.append(yaw)
        pitch_list.append(pitch)
        roll_list.append(roll)
    return np.array(yaw_list), np.array(pitch_list), np.array(roll_list)

# Process Data to Get Yaw, Pitch, and Roll
yaw_trial1, pitch_trial1, roll_trial1 = process_data(imu_data_trial1)
yaw_trial2, pitch_trial2, roll_trial2 = process_data(imu_data_trial2)

# Ensure both trials are of the same length
min_length = min(len(yaw_trial1), len(yaw_trial2))
yaw_trial1 = yaw_trial1[:min_length]
yaw_trial2 = yaw_trial2[:min_length]

pitch_trial1 = pitch_trial1[:min_length]
pitch_trial2 = pitch_trial2[:min_length]

roll_trial1 = roll_trial1[:min_length]
roll_trial2 = roll_trial2[:min_length]

# Calculate Mean and Standard Deviation for Yaw
mean_yaw_trial1 = np.mean(yaw_trial1)
std_yaw_trial1 = np.std(yaw_trial1)

mean_yaw_trial2 = np.mean(yaw_trial2)
std_yaw_trial2 = np.std(yaw_trial2)

# Calculate Mean and Standard Deviation for Pitch
mean_pitch_trial1 = np.mean(pitch_trial1)
std_pitch_trial1 = np.std(pitch_trial1)

mean_pitch_trial2 = np.mean(pitch_trial2)
std_pitch_trial2 = np.std(pitch_trial2)

# Calculate Mean and Standard Deviation for Roll
mean_roll_trial1 = np.mean(roll_trial1)
std_roll_trial1 = np.std(roll_trial1)

mean_roll_trial2 = np.mean(roll_trial2)
std_roll_trial2 = np.std(roll_trial2)

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

# Calculate ICC for Yaw, Pitch, and Roll
yaw_data = np.array([yaw_trial1, yaw_trial2])
icc_yaw = calculate_icc(yaw_data)

pitch_data = np.array([pitch_trial1, pitch_trial2])
icc_pitch = calculate_icc(pitch_data)

roll_data = np.array([roll_trial1, roll_trial2])
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
    ax.set_title(title)
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

# Create combined figure
fig, axes = plt.subplots(3, 3, figsize=(18, 18))
fig.suptitle('Yaw, Pitch, and Roll Analysis', fontsize=16)

# Plot Mean and Standard Deviation for Each Trial
axes[0, 0].plot(yaw_trial1, label='Trial 1 Yaw', alpha=0.6)
axes[0, 0].plot(yaw_trial2, label='Trial 2 Yaw', alpha=0.6)
axes[0, 0].axhline(mean_yaw_trial1, color='blue', linestyle='--', label='Mean Yaw Trial 1')
axes[0, 0].axhline(mean_yaw_trial2, color='orange', linestyle='--', label='Mean Yaw Trial 2')
axes[0, 0].fill_between(range(min_length), mean_yaw_trial1-std_yaw_trial1, mean_yaw_trial1+std_yaw_trial1, color='blue', alpha=0.2)
axes[0, 0].fill_between(range(min_length), mean_yaw_trial2-std_yaw_trial2, mean_yaw_trial2+std_yaw_trial2, color='orange', alpha=0.2)
axes[0, 0].set_title('Yaw Data with Mean and Standard Deviation')
axes[0, 0].set_xlabel('Sample')
axes[0, 0].set_ylabel('Yaw (radians)')
axes[0, 0].legend(fontsize = 6)

axes[0, 1].plot(pitch_trial1, label='Trial 1 Pitch', alpha=0.6)
axes[0, 1].plot(pitch_trial2, label='Trial 2 Pitch', alpha=0.6)
axes[0, 1].axhline(mean_pitch_trial1, color='blue', linestyle='--', label='Mean Pitch Trial 1')
axes[0, 1].axhline(mean_pitch_trial2, color='orange', linestyle='--', label='Mean Pitch Trial 2')
axes[0, 1].fill_between(range(min_length), mean_pitch_trial1-std_pitch_trial1, mean_pitch_trial1+std_pitch_trial1, color='blue', alpha=0.2)
axes[0, 1].fill_between(range(min_length), mean_pitch_trial2-std_pitch_trial2, mean_pitch_trial2+std_pitch_trial2, color='orange', alpha=0.2)
axes[0, 1].set_title('Pitch Data with Mean and Standard Deviation')
axes[0, 1].set_xlabel('Sample')
axes[0, 1].set_ylabel('Pitch (radians)')
axes[0, 1].legend(fontsize = 6)

axes[0, 2].plot(roll_trial1, label='Trial 1 Roll', alpha=0.6)
axes[0, 2].plot(roll_trial2, label='Trial 2 Roll', alpha=0.6)
axes[0, 2].axhline(mean_roll_trial1, color='blue', linestyle='--', label='Mean Roll Trial 1')
axes[0, 2].axhline(mean_roll_trial2, color='orange', linestyle='--', label='Mean Roll Trial 2')
axes[0, 2].fill_between(range(min_length), mean_roll_trial1-std_roll_trial1, mean_roll_trial1+std_roll_trial1, color='blue', alpha=0.2)
axes[0, 2].fill_between(range(min_length), mean_roll_trial2-std_roll_trial2, mean_roll_trial2+std_roll_trial2, color='orange', alpha=0.2)
axes[0, 2].set_title('Roll Data with Mean and Standard Deviation')
axes[0, 2].set_xlabel('Sample')
axes[0, 2].set_ylabel('Roll (radians)')
axes[0, 2].legend(fontsize = 6)

# Bland-Altman Plots
bland_altman_plot(yaw_trial1, yaw_trial2, axes[1, 0], 'Bland-Altman Plot for Yaw')
bland_altman_plot(pitch_trial1, pitch_trial2, axes[1, 1], 'Bland-Altman Plot for Pitch')
bland_altman_plot(roll_trial1, roll_trial2, axes[1, 2], 'Bland-Altman Plot for Roll')

# Correlation and RMSE Plots
plot_correlation_and_rmse(yaw_trial1, yaw_trial2, axes[2, 0], 'Trial 1 Yaw', 'Trial 2 Yaw')
plot_correlation_and_rmse(pitch_trial1, pitch_trial2, axes[2, 1], 'Trial 1 Pitch', 'Trial 2 Pitch')
plot_correlation_and_rmse(roll_trial1, roll_trial2, axes[2, 2], 'Trial 1 Roll', 'Trial 2 Roll')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Print ICC values
print(f'ICC for Yaw: {icc_yaw}')
print(f'ICC for Pitch: {icc_pitch}')
print(f'ICC for Roll: {icc_roll}')

# Print Correlation and RMSE
corr_yaw, rmse_yaw = plot_correlation_and_rmse(yaw_trial1, yaw_trial2, axes[2, 0], 'Trial 1 Yaw', 'Trial 2 Yaw')
corr_pitch, rmse_pitch = plot_correlation_and_rmse(pitch_trial1, pitch_trial2, axes[2, 1], 'Trial 1 Pitch', 'Trial 2 Pitch')
corr_roll, rmse_roll = plot_correlation_and_rmse(roll_trial1, roll_trial2, axes[2, 2], 'Trial 1 Roll', 'Trial 2 Roll')

print(f'Trial 1 vs Trial 2 (Yaw) - Correlation: {corr_yaw:.2f}, RMSE: {rmse_yaw:.2f}')
print(f'Trial 1 vs Trial 2 (Pitch) - Correlation: {corr_pitch:.2f}, RMSE: {rmse_pitch:.2f}')
print(f'Trial 1 vs Trial 2 (Roll) - Correlation: {corr_roll:.2f}, RMSE: {rmse_roll:.2f}')

