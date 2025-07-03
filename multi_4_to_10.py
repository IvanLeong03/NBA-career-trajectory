import pandas as pd
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Load the dataset
df = pd.read_csv("data/player_10yr_stats.csv")
print('Dataset loaded. Shape:', df.shape)

# add points/36
for year in range(1, 4):
    df[f"Y{year}_pts_per_36"] = (df[f"Y{year}_pts_per_g"] / df[f"Y{year}_mp_per_g"]) * 36


df["pts_growth"] = df["Y3_pts_per_g"] - df["Y1_pts_per_g"]
df["pp36_growth"] = df["Y3_pts_per_36"] - df["Y1_pts_per_36"]
# Features: stats from Y1 to Y3
input_cols = ["rookie_age", "pts_growth", "pp36_growth"] + [
                    f"Y{year}_{stat}" 
                    for year in range(1, 4)
                    for stat in ["pts_per_g", "ast_per_g", "trb_per_g", "stl_per_g", "blk_per_g", "mp_per_g"]
            ]

# Target: average points per game in years 4–10
df["avg_pts_future"] = df[[f"Y{y}_pts_per_g" for y in range(4, 11)]].mean(axis=1)
df["avg_ast_future"] = df[[f"Y{y}_ast_per_g" for y in range(4, 11)]].mean(axis=1)
df["avg_trb_future"] = df[[f"Y{y}_trb_per_g" for y in range(4, 11)]].mean(axis=1)
df["avg_stl_future"] = df[[f"Y{y}_stl_per_g" for y in range(4, 11)]].mean(axis=1)
df["avg_blk_future"] = df[[f"Y{y}_blk_per_g" for y in range(4, 11)]].mean(axis=1)
target_cols = ["avg_pts_future", "avg_ast_future", "avg_trb_future", "avg_stl_future", "avg_blk_future"]

df_model = df[input_cols + target_cols].dropna()

X = df_model[input_cols]
y = df_model[target_cols]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# train regression model

model = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, random_state=42))
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
    "Player": df.loc[y_test.index, "name"].values,
    "Actual PPG": y_test["avg_pts_future"].values.round(2),
    "Predicted PPG": y_pred[:, 0].round(2),
    "Actual AST": y_test["avg_ast_future"].values.round(2),
    "Predicted AST": y_pred[:, 1].round(2),
    "Actual REB": y_test["avg_trb_future"].values.round(2),
    "Predicted REB": y_pred[:, 2].round(2),
    "Actual STL": y_test["avg_stl_future"].values.round(2),
    "Predicted STL": y_pred[:, 3].round(2),
    "Actual BLK": y_test["avg_blk_future"].values.round(2),
    "Predicted BLK": y_pred[:, 4].round(2)
})

results_df.sort_values(by="Actual PPG", ascending=False, inplace=True)

# Show top N results
print("\nSample Results\n")
print(results_df.head(12).to_string(index=False))