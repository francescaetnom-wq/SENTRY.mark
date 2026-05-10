import json
import pandas as pd
from datetime import datetime
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────────
ALERTS_PATH  = "data/anomalies/alerts.json"
OUTPUT_PATH  = "data/anomalies/kill_switch_log.json"

# Conditions that trigger an automatic spending stop
KILL_SWITCH_TRIGGERS = [
    "tracking_break",
    "ghost_404",
    "bot_attack"
]

# Minimum Z-Score to activate kill switch (only act on severe anomalies)
KILL_SWITCH_Z_THRESHOLD = 3.0

# ── Load alerts ────────────────────────────────────────────────────────────────
print("Loading alerts...")
with open(ALERTS_PATH, "r") as f:
    alerts = json.load(f)

print(f"Total alerts loaded: {len(alerts)}")

# ── Kill-Switch logic ──────────────────────────────────────────────────────────
def evaluate_kill_switch(alert: dict) -> dict:
    """
    Evaluates whether an alert should trigger a spending stop.
    Returns a decision object with action, reason, and affected channel.
    """
    anomaly_type = alert.get("anomaly_type", "none")
    z_score      = alert.get("max_z_score", 0)
    severity     = alert.get("severity", "LOW")

    # Condition 1: anomaly type is in kill switch triggers
    type_triggered = anomaly_type in KILL_SWITCH_TRIGGERS

    # Condition 2: Z-Score is severe enough to act
    z_triggered = z_score >= KILL_SWITCH_Z_THRESHOLD

    if type_triggered and z_triggered:
        action = "STOP_SPENDING"
        reason = (
            f"Anomaly type '{anomaly_type}' detected on channel "
            f"'{alert['channel_medium']}' with Z-Score {z_score:.2f} "
            f"(severity: {severity}). Automatic spending halt activated."
        )
    elif type_triggered and not z_triggered:
        action = "FLAG_FOR_REVIEW"
        reason = (
            f"Anomaly type '{anomaly_type}' detected but Z-Score {z_score:.2f} "
            f"below kill switch threshold {KILL_SWITCH_Z_THRESHOLD}. "
            f"Flagged for manual review."
        )
    else:
        action = "NO_ACTION"
        reason = "Anomaly does not meet kill switch criteria."

    return {
        "timestamp" : datetime.now(tz=timezone.utc).isoformat(),
        "event_date"      : alert["event_date"],
        "channel_medium"  : alert["channel_medium"],
        "channel_source"  : alert["channel_source"],
        "anomaly_type"    : anomaly_type,
        "max_z_score"     : z_score,
        "severity"        : severity,
        "action"          : action,
        "reason"          : reason
    }

# ── Run evaluation ─────────────────────────────────────────────────────────────
print("Running kill switch evaluation...")

decisions = [evaluate_kill_switch(alert) for alert in alerts]

# Summary
stop_count   = sum(1 for d in decisions if d["action"] == "STOP_SPENDING")
flag_count   = sum(1 for d in decisions if d["action"] == "FLAG_FOR_REVIEW")
no_action    = sum(1 for d in decisions if d["action"] == "NO_ACTION")

print(f"\nKill Switch Evaluation complete:")
print(f"  STOP_SPENDING    : {stop_count}")
print(f"  FLAG_FOR_REVIEW  : {flag_count}")
print(f"  NO_ACTION        : {no_action}")

# Print STOP_SPENDING decisions
critical = [d for d in decisions if d["action"] == "STOP_SPENDING"]
if critical:
    print(f"\n⚠️  CRITICAL — Spending halt triggered on {len(critical)} alert(s):")
    for d in critical:
        print(f"  [{d['event_date']}] {d['channel_medium']} / {d['channel_source']}")
        print(f"  → {d['reason']}\n")
else:
    print("\n✅ No spending halts triggered.")

# ── Save log ───────────────────────────────────────────────────────────────────
with open(OUTPUT_PATH, "w") as f:
    json.dump(decisions, f, indent=2)

print(f"Kill switch log saved to: {OUTPUT_PATH}")