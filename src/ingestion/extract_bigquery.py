import os
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Set credentials path from environment
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

# Initialize BigQuery client
client = bigquery.Client(project="luminous-lambda-483816-p2")

# Query the fact table
query = """
    SELECT *
    FROM `luminous-lambda-483816-p2.sentry_mark.fact_daily_metrics`
    ORDER BY event_date, channel_medium
"""

print("Connecting to BigQuery...")
df = client.query(query).to_dataframe()
print(f"Data extracted: {len(df)} rows, {len(df.columns)} columns")

# Save to local CSV
output_path = "data/raw/fact_daily_metrics.csv"
df.to_csv(output_path, index=False)
print(f"File saved to: {output_path}")