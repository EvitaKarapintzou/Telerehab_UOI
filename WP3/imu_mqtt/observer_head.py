import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np

# Data provided
data_intra = {
    'observer1_first': [28.59, 33.64, 29.85, 31.46, 31.98, 30.64, 30.43, 30.76, 29.51, 31.11],
    'observer1_second': [30.55, 28.47, 30.66, 30.88, 30.28, 30.2, 30.34, 31.25, 30.99, 31.65],
    'observer2_first': [58.06, 57.59, 57.92, 58.24, 58.03, 59.31, 57.81, 57.47, 56.93, 57.13],
    'observer2_second': [57.59, 57.92, 57.8, 57.71, 57.65, 58.04, 56.21, 57.05, 57.25, 56.03]
}

data_inter = {
    'observer1': [17.83,	30.32,	29.95,	29.33,	30.20,	18.39,	17.82,	30.08,	29.63,	28.37,	30.31,	18.73],
    'observer2': [19, 30, 30, 30, 30, 20, 19, 30, 30, 30, 30, 20]
}

# Convert data to DataFrame
df_intra = pd.DataFrame(data_intra)
df_inter = pd.DataFrame(data_inter)

def plot_regression(observer_first, observer_second, title):
    # Perform linear regression
    X = observer_first.values.reshape(-1, 1)
    y = observer_second.values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # Extract regression parameters
    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(X, y)

    # Plot the results
    plt.scatter(X, y, color='blue', label='Data points')
    plt.plot(X, y_pred, color='red', label='Regression line')
    plt.xlabel('Degrees (1st observation)')
    plt.ylabel('Degrees (2nd observation)')
    plt.title(title)
    plt.legend()
    plt.text(0.5, 0.1, f'y = {slope:.4f}x + {intercept:.4f}\n$R^2$ = {r_squared:.4f}',
             ha='center', va='center', transform=plt.gca().transAxes)
    plt.show()

# Plot for Observer 1
plot_regression(df_intra['observer1_first'], df_intra['observer1_second'], 'Intraobserver Variability (Observer 1)')

# Plot for Observer 2
plot_regression(df_intra['observer2_first'], df_intra['observer2_second'], 'Intraobserver Variability (Observer 2)')

# Interobserver Variability
plot_regression(df_inter['observer1'], df_inter['observer2'], 'Interobserver Variability')

# Correlation Plot
def plot_correlation(observer, measured, title):
    # Perform linear regression
    X = observer.values.reshape(-1, 1)
    y = measured.values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # Extract regression parameters
    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(X, y)

    # Plot the results
    plt.scatter(X, y, color='blue', label='Data points')
    plt.plot(X, y_pred, color='red', label='Regression line')
    plt.xlabel('Observed Value (degrees)')
    plt.ylabel('Measured Value (degrees)')
    plt.title(title)
    plt.legend()
    plt.text(0.5, 0.1, f'y = {slope:.4f}x + {intercept:.4f}\n$R^2$ = {r_squared:.4f}',
             ha='center', va='center', transform=plt.gca().transAxes)
    plt.show()

# Assuming measured data is available for correlation plot
observed_values = df_inter['observer1']  # Replace with actual observed values
measured_values = df_inter['observer2']  # Replace with actual measured values

plot_correlation(observed_values, measured_values, 'Correlation between Observed and Measured Values')

# Bland-Altman Plot
def plot_bland_altman(observer, measured, title):
    mean = np.mean([observer, measured], axis=0)
    diff = measured - observer
    md = np.mean(diff)
    sd = np.std(diff)

    plt.scatter(mean, diff, color='blue', s=20)
    plt.axhline(md, color='red', linestyle='--', label=f'Mean Difference: {md:.2f}')
    plt.axhline(md + 1.96*sd, color='green', linestyle='--', label=f'+1.96 SD: {md + 1.96*sd:.2f}')
    plt.axhline(md - 1.96*sd, color='green', linestyle='--', label=f'-1.96 SD: {md - 1.96*sd:.2f}')
    plt.xlabel('Mean of Observed and Measured Values (degrees)')
    plt.ylabel('Difference (Measured - Observed)')
   
