import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Load the dataset
df = pd.read_csv("data/player_10yr_stats.csv")
print('Dataset loaded. Shape:', df.shape)

# Features: stats from Y1 to Y3
input_cols = ["rookie_age"] + [
                    f"Y{year}_{stat}" 
                    for year in range(1, 4)
                    for stat in ["pts_per_g", "ast_per_g", "trb_per_g", "stl_per_g", "blk_per_g", "mp_per_g"]
            ]

# Target: average points per game in years 4–10
target_cols = [f"Y{year}_pts_per_g" for year in range(4, 11)]
df["avg_pts_future"] = df[target_cols].mean(axis=1)
df_model = df[input_cols + ["avg_pts_future"]].dropna()


# train-test split
X = df_model[input_cols]
y = df_model["avg_pts_future"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=41)

# train regression model

model = RandomForestRegressor(n_estimators=100, random_state=41)
model.fit(X_train, y_train)

# evaluate model
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print('\nResults: ')
print(f"MAE:  {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R²:   {r2:.3f}")

# print some roles for visualisation

# Get index of test set (matches y_test)
test_indices = y_test.index

# Extract player names from original df
player_names = df.loc[test_indices, "name"]

# Build comparison DataFrame
results_df = pd.DataFrame({
    "Player": player_names.values,
    "Actual Avg PPG (Y4–Y10)": y_test.values.round(2),
    "Predicted Avg PPG": y_pred.round(2)
})

# Sort by actual or prediction, optional
results_df = results_df.sort_values("Actual Avg PPG (Y4–Y10)", ascending=False)

# Show top N results
print("\nSample Results:")
print(results_df.head(10).to_string(index=False))