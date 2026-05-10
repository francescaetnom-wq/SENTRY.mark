import pandas as pd
import json
from datetime import datetime, timezone


# ── Configuration ──────────────────────────────────────────────────────────────
INPUT_PATH  = "data/processed/anomalies_detected.csv"
OUTPUT_PATH = "data/anomalies/alerts.json"

# ── Classification rules ───────────────────────────────────────────────────────
# Technical errors require immediate action
# Market fluctuations go into the weekly report
TECHNICAL_ERROR_CONDITIONS = {
    "tracking_break"     : "sessions dropped to near zero — tracking likely broken",
    "ghost_404"          : "zero revenue on active traffic — landing page returning 404",
    "bot_attack"         : "sessions spike with zero conversions and 100% bounce — bot traffic detected",
    "currency_tax_glitch": "revenue anomaly inconsistent with purchase volume — data integrity issue"
}

MARKET_FLUCTUATION_CONDITIONS = {
    "ppc_spike": "traffic spike without proportional revenue increase — bid strategy review needed"
}

# Z-Score severity bands
def get_severity(z_score: float) -> str:
    if z_score >= 4.0:
        return "CRITICAL"
    elif z_score >= 3.0:
        return "HIGH"
    elif z_score >= 1.96:
        return "MEDIUM"
    else:
        return "LOW"

# ── Load anomalies ─────────────────────────────────────────────────────────────
print("Loading detected anomalies...")
df = pd.read_csv(INPUT_PATH)
df["event_date"] = pd.to_datetime(df["event_date"])

# Focus on synthetic anomalies for classification demo
# In production this runs on all anomalies
synthetic = df[df["is_synthetic_anomaly"] == True].copy()
real      = df[df["is_synthetic_anomaly"] == False].copy()

print(f"Synthetic anomalies to classify : {len(synthetic)}")
print(f"Real anomalies to classify      : {len(real)}")

# ── Classify anomalies ─────────────────────────────────────────────────────────
alerts = []

for _, row in df.iterrows():
    anomaly_type = row.get("anomaly_type", "none")

    if anomaly_type in TECHNICAL_ERROR_CONDITIONS:
        alert_class   = "TECHNICAL_ERROR"
        protocol      = "IMMEDIATE_ACTION"
        description   = TECHNICAL_ERROR_CONDITIONS[anomaly_type]
    elif anomaly_type in MARKET_FLUCTUATION_CONDITIONS:
        alert_class   = "MARKET_FLUCTUATION"
        protocol      = "WEEKLY_REPORT"
        description   = MARKET_FLUCTUATION_CONDITIONS[anomaly_type]
    else:
        alert_class   = "STATISTICAL_OUTLIER"
        protocol      = "MONITOR"
        description   = f"metric '{row['triggered_metric']}' deviated beyond threshold"

    alerts.append({
        "timestamp" : datetime.now(tz=timezone.utc).isoformat(),
        "event_date"           : str(row["event_date"].date()),
        "channel_medium"       : row["channel_medium"],
        "channel_source"       : row["channel_source"],
        "anomaly_type"         : anomaly_type,
        "triggered_metric"     : row["triggered_metric"],
        "max_z_score"          : round(float(row["max_z_score"]), 4),
        "severity"             : get_severity(row["max_z_score"]),
        "alert_class"          : alert_class,
        "protocol"             : protocol,
        "description"          : description,
        "is_synthetic_anomaly" : bool(row["is_synthetic_anomaly"])
    })

# ── Save output ────────────────────────────────────────────────────────────────
with open(OUTPUT_PATH, "w") as f:
    json.dump(alerts, f, indent=2)

print(f"\nClassification complete:")
print(f"  Total alerts generated : {len(alerts)}")
print(f"  TECHNICAL_ERROR        : {sum(1 for a in alerts if a['alert_class'] == 'TECHNICAL_ERROR')}")
print(f"  MARKET_FLUCTUATION     : {sum(1 for a in alerts if a['alert_class'] == 'MARKET_FLUCTUATION')}")
print(f"  STATISTICAL_OUTLIER    : {sum(1 for a in alerts if a['alert_class'] == 'STATISTICAL_OUTLIER')}")
print(f"\nAlerts saved to: {OUTPUT_PATH}")