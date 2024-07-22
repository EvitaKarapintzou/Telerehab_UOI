import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load IMU data from four trials
imu_data_trial1 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/Maintain Balance HWA-FCT/OldStanding1-FCT_eye-closed/Back_E25AD03D0194_2024-03-05_15_07_50.csv')
imu_data_trial2 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/Maintain Balance HWA-FCT/OldStanding1-FCT_eye-open/Back_E25AD03D0194_2024-03-05_15_04_35.csv')
imu_data_trial3 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/Maintain Balance HWA-FCT/OldStanding1-HWA_eye-closed/Back_E25AD03D0194_2024-03-05_15_00_14.csv')
imu_data_trial4 = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/Validation/Maintain Balance HWA-FCT/OldStanding1-HWA_eye-open/Back_E25AD03D0194_2024-03-05_14_54_24.csv')

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

# Calculate Mean and Standard Deviation for Yaw and Roll
mean_yaw_trial1 = np.mean(yaw_trial1)
std_yaw_trial1 = np.std(yaw_trial1)
mean_yaw_trial2 = np.mean(yaw_trial2)
std_yaw_trial2 = np.std(yaw_trial2)
mean_yaw_trial3 = np.mean(yaw_trial3)
std_yaw_trial3 = np.std(yaw_trial3)
mean_yaw_trial4 = np.mean(yaw_trial4)
std_yaw_trial4 = np.std(yaw_trial4)

mean_roll_trial1 = np.mean(roll_trial1)
std_roll_trial1 = np.std(roll_trial1)
mean_roll_trial2 = np.mean(roll_trial2)
std_roll_trial2 = np.std(roll_trial2)
mean_roll_trial3 = np.mean(roll_trial3)
std_roll_trial3 = np.std(roll_trial3)
mean_roll_trial4 = np.mean(roll_trial4)
std_roll_trial4 = np.std(roll_trial4)

print(f'Mean Yaw FCT-Eye closed: {mean_yaw_trial1}, STD Yaw FCT-Eye closed: {std_yaw_trial1}')
print(f'Mean Yaw FCT-Eye open: {mean_yaw_trial2}, STD Yaw FCT-Eye open: {std_yaw_trial2}')
print(f'Mean Yaw HWA-Eye closed: {mean_yaw_trial3}, STD Yaw HWA-Eye closed: {std_yaw_trial3}')
print(f'Mean Yaw HWA-Eye open: {mean_yaw_trial4}, STD Yaw HWA-Eye open: {std_yaw_trial4}')

print(f'Mean Roll FCT-Eye closed: {mean_roll_trial1}, STD Roll FCT-Eye closed: {std_roll_trial1}')
print(f'Mean Roll FCT-Eye open: {mean_roll_trial2}, STD Roll FCT-Eye open: {std_roll_trial2}')
print(f'Mean Roll HWA-Eye closed: {mean_roll_trial3}, STD Roll HWA-Eye closed: {std_roll_trial3}')
print(f'Mean Roll HWA-Eye open: {mean_roll_trial4}, STD Roll HWA-Eye open: {std_roll_trial4}')

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

# Calculate ICC for Yaw and Roll
yaw_data = np.array([yaw_trial1, yaw_trial2, yaw_trial3, yaw_trial4])
icc_yaw = calculate_icc(yaw_data)
print(f'ICC for Yaw: {icc_yaw}')

roll_data = np.array([roll_trial1, roll_trial2, roll_trial3, roll_trial4])
icc_roll = calculate_icc(roll_data)
print(f'ICC for Roll: {icc_roll}')

# Bland-Altman Plot
def bland_altman_plot(ax, data1, data2, title):
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

# Combined plot for Mean and Standard Deviation, Bland-Altman, Correlation and RMSE
fig, axes = plt.subplots(2, 3, figsize=(18, 24))
fig.suptitle('Yaw and Roll Analysis', fontsize=16)

# # Plot Mean and Standard Deviation for Each Trial (Yaw)
# axes[0, 0].plot(yaw_trial1, label='FCT-Eye closed Yaw', alpha=0.6)
# axes[0, 0].plot(yaw_trial2, label='FCT-Eye open Yaw', alpha=0.6)
# axes[0, 0].plot(yaw_trial3, label='HWA-Eye closed Yaw', alpha=0.6)
# axes[0, 0].plot(yaw_trial4, label='HWA-Eye open Yaw', alpha=0.6)
# axes[0, 0].axhline(mean_yaw_trial1, color='blue', linestyle='--', label='Mean Yaw FCT-Eye closed')
# axes[0, 0].axhline(mean_yaw_trial2, color='orange', linestyle='--', label='Mean Yaw FCT-Eye open')
# axes[0, 0].axhline(mean_yaw_trial3, color='green', linestyle='--', label='Mean Yaw HWA-Eye closed')
# axes[0, 0].axhline(mean_yaw_trial4, color='red', linestyle='--', label='Mean Yaw HWA-Eye open')
# axes[0, 0].fill_between(range(min_length), mean_yaw_trial1-std_yaw_trial1, mean_yaw_trial1+std_yaw_trial1, color='blue', alpha=0.2)
# axes[0, 0].fill_between(range(min_length), mean_yaw_trial2-std_yaw_trial2, mean_yaw_trial2+std_yaw_trial2, color='orange', alpha=0.2)
# axes[0, 0].fill_between(range(min_length), mean_yaw_trial3-std_yaw_trial3, mean_yaw_trial3+std_yaw_trial3, color='green', alpha=0.2)
# axes[0, 0].fill_between(range(min_length), mean_yaw_trial4-std_yaw_trial4, mean_yaw_trial4+std_yaw_trial4, color='red', alpha=0.2)
# axes[0, 0].set_title('Yaw Data with Mean and Standard Deviation')
# axes[0, 0].set_xlabel('Sample')
# axes[0, 0].set_ylabel('Yaw (radians)')
# axes[0, 0].legend()

# # Plot Mean and Standard Deviation for Each Trial (Roll)
# axes[0, 1].plot(roll_trial1, label='FCT-Eye closed Roll', alpha=0.6)
# axes[0, 1].plot(roll_trial2, label='FCT-Eye open Roll', alpha=0.6)
# axes[0, 1].plot(roll_trial3, label='HWA-Eye closed Roll', alpha=0.6)
# axes[0, 1].plot(roll_trial4, label='HWA-Eye open Roll', alpha=0.6)
# axes[0, 1].axhline(mean_roll_trial1, color='blue', linestyle='--', label='Mean Roll FCT-Eye closed')
# axes[0, 1].axhline(mean_roll_trial2, color='orange', linestyle='--', label='Mean Roll FCT-Eye open')
# axes[0, 1].axhline(mean_roll_trial3, color='green', linestyle='--', label='Mean Roll HWA-Eye closed')
# axes[0, 1].axhline(mean_roll_trial4, color='red', linestyle='--', label='Mean Roll HWA-Eye open')
# axes[0, 1].fill_between(range(min_length), mean_roll_trial1-std_roll_trial1, mean_roll_trial1+std_roll_trial1, color='blue', alpha=0.2)
# axes[0, 1].fill_between(range(min_length), mean_roll_trial2-std_roll_trial2, mean_roll_trial2+std_roll_trial2, color='orange', alpha=0.2)
# axes[0, 1].fill_between(range(min_length), mean_roll_trial3-std_roll_trial3, mean_roll_trial3+std_roll_trial3, color='green', alpha=0.2)
# axes[0, 1].fill_between(range(min_length), mean_roll_trial4-std_roll_trial4, mean_roll_trial4+std_roll_trial4, color='red', alpha=0.2)
# axes[0, 1].set_title('Roll Data with Mean and Standard Deviation')
# axes[0, 1].set_xlabel('Sample')
# axes[0, 1].set_ylabel('Roll (radians)')
# axes[0, 1].legend()

# # Bland-Altman Plots for Yaw
# bland_altman_plot(axes[0, 0], yaw_trial1, yaw_trial2, 'Yaw - FCT-Eye closed vs FCT-Eye open')
# bland_altman_plot(axes[0, 1], yaw_trial1, yaw_trial3, 'Yaw - FCT-Eye closed vs HWA-Eye closed')
# bland_altman_plot(axes[0, 2], yaw_trial1, yaw_trial4, 'Yaw - FCT-Eye closed vs HWA-Eye open')
# bland_altman_plot(axes[1, 0], yaw_trial2, yaw_trial3, 'Yaw - FCT-Eye open vs HWA-Eye closed')
# bland_altman_plot(axes[1, 1], yaw_trial2, yaw_trial4, 'Yaw - FCT-Eye open vs HWA-Eye open')
# bland_altman_plot(axes[1, 2], yaw_trial3, yaw_trial4, 'Yaw - HWA-Eye closed vs HWA-Eye open')

# Bland-Altman Plots for Roll
bland_altman_plot(axes[0, 0], roll_trial1, roll_trial2, 'Roll - FCT-Eye closed vs FCT-Eye open')
bland_altman_plot(axes[0, 1], roll_trial1, roll_trial3, 'Roll - FCT-Eye closed vs HWA-Eye closed')
bland_altman_plot(axes[0, 2], roll_trial1, roll_trial4, 'Roll - FCT-Eye closed vs HWA-Eye open')
bland_altman_plot(axes[1, 0], roll_trial2, roll_trial3, 'Roll - FCT-Eye open vs HWA-Eye closed')
bland_altman_plot(axes[1, 1], roll_trial2, roll_trial4, 'Roll - FCT-Eye open vs HWA-Eye open')
bland_altman_plot(axes[1, 2], roll_trial3, roll_trial4, 'Roll - HWA-Eye closed vs HWA-Eye open')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Combined plot for Correlation and RMSE (Yaw)
fig2, axes2 = plt.subplots(2, 3, figsize=(18, 12))
fig2.suptitle('Correlation and RMSE - Yaw', fontsize=16)

def plot_correlation_and_rmse(ax, data1, data2, trial1_label, trial2_label):
    ax.scatter(data1, data2, alpha=0.6, label=f'{trial1_label} vs {trial2_label}')
    correlation = np.corrcoef(data1, data2)[0, 1]
    rmse = np.sqrt(mean_squared_error(data1, data2))
    ax.plot([min(data1), max(data1)], [min(data1), max(data1)], 'r--')
    ax.set_title(f'Correlation: {correlation:.2f}, RMSE: {rmse:.2f}')
    ax.set_xlabel(f'{trial1_label}')
    ax.set_ylabel(f'{trial2_label}')
    return correlation, rmse

corr_12, rmse_12 = plot_correlation_and_rmse(axes2[0, 0], yaw_trial1, yaw_trial2, 'FCT-Eye closed Yaw', 'FCT-Eye open Yaw')
corr_13, rmse_13 = plot_correlation_and_rmse(axes2[0, 1], yaw_trial1, yaw_trial3, 'FCT-Eye closed Yaw', 'HWA-Eye closed Yaw')
corr_14, rmse_14 = plot_correlation_and_rmse(axes2[0, 2], yaw_trial1, yaw_trial4, 'FCT-Eye closed Yaw', 'HWA-Eye open Yaw')
corr_23, rmse_23 = plot_correlation_and_rmse(axes2[1, 0], yaw_trial2, yaw_trial3, 'FCT-Eye open Yaw', 'HWA-Eye closed Yaw')
corr_24, rmse_24 = plot_correlation_and_rmse(axes2[1, 1], yaw_trial2, yaw_trial4, 'FCT-Eye open Yaw', 'HWA-Eye open Yaw')
corr_34, rmse_34 = plot_correlation_and_rmse(axes2[1, 2], yaw_trial3, yaw_trial4, 'HWA-Eye closed Yaw', 'HWA-Eye open Yaw')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Combined plot for Correlation and RMSE (Roll)
fig3, axes3 = plt.subplots(2, 3, figsize=(18, 12))
fig3.suptitle('Correlation and RMSE - Roll', fontsize=16)

corr_12, rmse_12 = plot_correlation_and_rmse(axes3[0, 0], roll_trial1, roll_trial2, 'FCT-Eye closed Roll', 'FCT-Eye open Roll')
corr_13, rmse_13 = plot_correlation_and_rmse(axes3[0, 1], roll_trial1, roll_trial3, 'FCT-Eye closed Roll', 'HWA-Eye closed Roll')
corr_14, rmse_14 = plot_correlation_and_rmse(axes3[0, 2], roll_trial1, roll_trial4, 'FCT-Eye closed Roll', 'HWA-Eye open Roll')
corr_23, rmse_23 = plot_correlation_and_rmse(axes3[1, 0], roll_trial2, roll_trial3, 'FCT-Eye open Roll', 'HWA-Eye closed Roll')
corr_24, rmse_24 = plot_correlation_and_rmse(axes3[1, 1], roll_trial2, roll_trial4, 'FCT-Eye open Roll', 'HWA-Eye open Roll')
corr_34, rmse_34 = plot_correlation_and_rmse(axes3[1, 2], roll_trial3, roll_trial4, 'HWA-Eye closed Roll', 'HWA-Eye open Roll')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.show()

# Print Correlation and RMSE
print(f'FCT-Eye closed vs FCT-Eye open (Yaw) - Correlation: {corr_12:.2f}, RMSE: {rmse_12:.2f}')
print(f'FCT-Eye closed vs HWA-Eye closed (Yaw) - Correlation: {corr_13:.2f}, RMSE: {rmse_13:.2f}')
print(f'FCT-Eye closed vs HWA-Eye open (Yaw) - Correlation: {corr_14:.2f}, RMSE: {rmse_14:.2f}')
print(f'FCT-Eye open vs HWA-Eye closed (Yaw) - Correlation: {corr_23:.2f}, RMSE: {rmse_23:.2f}')
print(f'FCT-Eye open vs HWA-Eye open (Yaw) - Correlation: {corr_24:.2f}, RMSE: {rmse_24:.2f}')
print(f'HWA-Eye closed vs HWA-Eye open (Yaw) - Correlation: {corr_34:.2f}, RMSE: {rmse_34:.2f}')

print(f'FCT-Eye closed vs FCT-Eye open (Roll) - Correlation: {corr_12:.2f}, RMSE: {rmse_12:.2f}')
print(f'FCT-Eye closed vs HWA-Eye closed (Roll) - Correlation: {corr_13:.2f}, RMSE: {rmse_13:.2f}')
print(f'FCT-Eye closed vs HWA-Eye open (Roll) - Correlation: {corr_14:.2f}, RMSE: {rmse_14:.2f}')
print(f'FCT-Eye open vs HWA-Eye closed (Roll) - Correlation: {corr_23:.2f}, RMSE: {rmse_23:.2f}')
print(f'FCT-Eye open vs HWA-Eye open (Roll) - Correlation: {corr_24:.2f}, RMSE: {rmse_24:.2f}')
print(f'HWA-Eye closed vs HWA-Eye open (Roll) - Correlation: {corr_34:.2f}, RMSE: {rmse_34:.2f}')