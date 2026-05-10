import json
import os
import requests
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────────────────────
load_dotenv()

ALERTS_PATH      = "data/anomalies/alerts.json"
SLACK_WEBHOOK    = os.getenv("SLACK_WEBHOOK_URL")

# Only notify for these classes and severities
NOTIFY_CLASSES   = ["TECHNICAL_ERROR"]
NOTIFY_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM"]

# ── Load alerts ────────────────────────────────────────────────────────────────
print("Loading alerts...")
with open(ALERTS_PATH, "r") as f:
    alerts = json.load(f)

# Filter only alerts worth notifying
critical_alerts = [
    a for a in alerts
    if a["alert_class"] in NOTIFY_CLASSES
    and a["severity"] in NOTIFY_SEVERITIES
    and a["is_synthetic_anomaly"] is True  # demo mode: only synthetic
]

print(f"Alerts to notify: {len(critical_alerts)}")

# ── Format Slack message ───────────────────────────────────────────────────────
def build_slack_message(alert: dict) -> dict:
    severity_emoji = {
        "CRITICAL" : "🚨",
        "HIGH"     : "⚠️",
        "MEDIUM"   : "🔶",
        "LOW"      : "🔵"
    }
    emoji = severity_emoji.get(alert["severity"], "❓")

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} SENTRY.mark — {alert['severity']} ALERT"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Anomaly Type:*\n{alert['anomaly_type']}"},
                    {"type": "mrkdwn", "text": f"*Channel:*\n{alert['channel_medium']} / {alert['channel_source']}"},
                    {"type": "mrkdwn", "text": f"*Date:*\n{alert['event_date']}"},
                    {"type": "mrkdwn", "text": f"*Z-Score:*\n{alert['max_z_score']}"},
                    {"type": "mrkdwn", "text": f"*Triggered Metric:*\n{alert['triggered_metric']}"},
                    {"type": "mrkdwn", "text": f"*Protocol:*\n{alert['protocol']}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{alert['description']}"
                }
            },
            {
                "type": "divider"
            }
        ]
    }

# ── Send notifications ─────────────────────────────────────────────────────────
print("Sending Slack notifications...")

sent  = 0
failed = 0

for alert in critical_alerts:
    message  = build_slack_message(alert)
    response = requests.post(SLACK_WEBHOOK, json=message)

    if response.status_code == 200:
        print(f"  ✅ Sent: [{alert['event_date']}] {alert['anomaly_type']} — {alert['channel_medium']}")
        sent += 1
    else:
        print(f"  ❌ Failed: {response.status_code} — {response.text}")
        failed += 1

print(f"\nNotifications complete: {sent} sent, {failed} failed")