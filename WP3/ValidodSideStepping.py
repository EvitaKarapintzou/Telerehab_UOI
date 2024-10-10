import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np

# Example data
# Replace these lists with your actual data
measured_steps = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
algorithm_steps = [8, 10, 9, 9, 15, 6, 7, 9, 10, 10]

# Create DataFrame
data = {
    'measured': measured_steps,
    'algorithm': algorithm_steps
}

df = pd.DataFrame(data)

# Correlation Analysis
def plot_correlation(measured, algorithm, title):
    # Perform linear regression
    X = measured.values.reshape(-1, 1)
    y = algorithm.values

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
    plt.xlabel('Measured Steps')
    plt.ylabel('Algorithm Steps')
    plt.title(title)
    plt.legend()
    plt.text(0.5, 0.1, f'y = {slope:.4f}x + {intercept:.4f}\n$R^2$ = {r_squared:.4f}',
             ha='center', va='center', transform=plt.gca().transAxes)
    plt.show()

# Bland-Altman Analysis
def plot_bland_altman(measured, algorithm, title):
    mean = np.mean([measured, algorithm], axis=0)
    diff = algorithm - measured
    md = np.mean(diff)
    sd = np.std(diff)

    plt.scatter(mean, diff, color='blue', s=20)
    plt.axhline(md, color='red', linestyle='--', label=f'Mean Difference: {md:.2f}')
    plt.axhline(md + 1.96*sd, color='green', linestyle='--', label=f'+1.96 SD: {md + 1.96*sd:.2f}')
    plt.axhline(md - 1.96*sd, color='green', linestyle='--', label=f'-1.96 SD: {md - 1.96*sd:.2f}')
    plt.xlabel('Measured and Algorithm Steps')
    plt.ylabel('Difference (Algorithm - Measured)')
    plt.title(title)
    plt.legend()
    plt.show()

# Perform analysis
plot_correlation(df['measured'], df['algorithm'], 'Correlation between Measured and Algorithm Steps')
plot_bland_altman(df['measured'], df['algorithm'], 'Bland-Altman Plot for Measured vs Algorithm Steps')

# Correlation Analysis
def plot_correlation_with_r2(measured, algorithm, title):
    # Perform linear regression
    X = measured.values.reshape(-1, 1)
    y = algorithm.values

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
    plt.xlabel('Measured Steps')
    plt.ylabel('Algorithm Steps')
    plt.title(title)
    plt.legend()
    plt.text(0.1, 0.9, f'y = {slope:.4f}x + {intercept:.4f}\n$R^2$ = {r_squared:.4f}',
             ha='left', va='center', transform=plt.gca().transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.5))
    plt.show()

# Perform analysis
plot_correlation_with_r2(df['measured'], df['algorithm'], 'Correlation between Measured and Algorithm Steps')