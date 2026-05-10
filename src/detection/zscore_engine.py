import pandas as pd
import numpy as np
from scipy import stats

# ── Configuration ──────────────────────────────────────────────────────────────
INPUT_PATH = "data/raw/fact_daily_metrics.csv"
OUTPUT_PATH = "data/processed/anomalies_detected.csv"

# Z-Score threshold: 1.96 = 95% confidence interval
Z_THRESHOLD = 1.96

# Rolling window in days for mean and std calculation
ROLLING_WINDOW = 7

# Metrics to monitor
METRICS = [
    "sessions",
    "users",
    "purchases",
    "revenue",
    "conversion_rate_pct",
    "bounce_rate_pct",
    "revenue_per_session"
]

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(INPUT_PATH)
df["event_date"] = pd.to_datetime(df["event_date"], format="%Y%m%d")
df = df.sort_values(["channel_medium", "channel_source", "event_date"])

print(f"Loaded {len(df)} rows across {df['channel_medium'].nunique()} channels")

# ── Z-Score calculation ────────────────────────────────────────────────────────
print("Calculating Z-Scores...")

results = []

# Calculate Z-Score per channel (medium + source) to avoid mixing traffic sources
for (medium, source), group in df.groupby(["channel_medium", "channel_source"]):
    group = group.copy()

    for metric in METRICS:
        # Rolling mean and standard deviation over the last 7 days
        rolling_mean = group[metric].rolling(window=ROLLING_WINDOW, min_periods=3).mean()
        rolling_std  = group[metric].rolling(window=ROLLING_WINDOW, min_periods=3).std()

        # Avoid division by zero: if std is 0, Z-Score is 0
        group[f"z_{metric}"] = np.where(
            rolling_std == 0,
            0,
            (group[metric] - rolling_mean) / rolling_std
        )

    # Flag rows where ANY metric exceeds the threshold
    z_columns = [f"z_{m}" for m in METRICS]
    group["max_z_score"] = group[z_columns].abs().max(axis=1)
    group["triggered_metric"] = group[z_columns].abs().idxmax(axis=1, skipna=True).str.replace("z_", "")
    group["is_anomaly"] = group["max_z_score"] > Z_THRESHOLD

    results.append(group)

df_scored = pd.concat(results).reset_index(drop=True)

# ── Filter anomalies only ──────────────────────────────────────────────────────
anomalies = df_scored[df_scored["is_anomaly"] == True].copy()

print(f"\nAnomaly detection complete:")
print(f"  Total rows analyzed : {len(df_scored)}")
print(f"  Anomalies detected  : {len(anomalies)}")
print(f"  Synthetic anomalies caught: {anomalies['is_synthetic_anomaly'].sum()}")

# ── Save output ────────────────────────────────────────────────────────────────
anomalies.to_csv(OUTPUT_PATH, index=False)
print(f"\nAnomalies saved to: {OUTPUT_PATH}")
print("\nSample of detected anomalies:")
print(anomalies[["event_date", "channel_medium", "triggered_metric", 
                  "max_z_score", "anomaly_type", "is_synthetic_anomaly"]].head(10).to_string())
