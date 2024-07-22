import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Load your data
# Assuming `data` is a pandas DataFrame containing your dataset
# X1, X2, X3 are the features (x, y, z) and y is the target variable
data = pd.read_csv('your_data.csv')  # Replace with your actual file path
X = data[['X1', 'X2', 'X3']]  # replace with your actual feature column names
y = data['target']  # replace with your actual target column name

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit a linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Predict on the testing set
y_pred = model.predict(X_test)

# Compute evaluation metrics
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(f'Mean Squared Error: {mse}')
print(f'Root Mean Squared Error: {rmse}')
print(f'R-squared: {r2}')
print(f'Mean Absolute Error: {mae}')

# Plot observed vs. predicted values
plt.scatter(y_test, y_pred)
plt.xlabel('Observed Values')
plt.ylabel('Predicted Values')
plt.title('Observed vs. Predicted Values')
plt.show()

# Residual Analysis
residuals = y_test - y_pred
plt.scatter(y_pred, residuals)
plt.xlabel('Predicted Values')
plt.ylabel('Residuals')
plt.title('Residuals vs. Predicted Values')
plt.axhline(0, color='red', linestyle='--')
plt.show()

# Cross-Validation
cross_val_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
cross_val_rmse = np.sqrt(-cross_val_scores)
print(f'Cross-Validated RMSE: {cross_val_rmse.mean()} ± {cross_val_rmse.std()}')
