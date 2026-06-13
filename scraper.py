import re
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from datetime import datetime, timezone

# =========================
# DEBUG TIME
# =========================

print("================================")
print("UTC Time:", datetime.now(timezone.utc))
print("================================")

# =========================
# SUPABASE CONFIG
# =========================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# =========================
# SCRAPE WEBSITE
# =========================

url = "https://www.livechennai.com/gold_silverrate.asp"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    print("Failed to fetch website")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

text = soup.get_text(" ", strip=True)

# =========================
# GET UPDATE TIME
# =========================

time_match = re.search(
    r"Last Update Time:\s*([0-9/: ]+[APMapm]{2})",
    text
)

update_time = ""

if time_match:
    update_time = time_match.group(1).strip()

# =========================
# GET GOLD RATES
# =========================

gold_match = re.search(
    r"(\d{2}/[A-Za-z]{3}/\d{4})\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)",
    text
)

if not gold_match:
    print("Gold rate data not found")
    exit()

date = gold_match.group(1)

rate_24k = gold_match.group(2).replace(",", "")
rate_22k = gold_match.group(4).replace(",", "")

print("Date:", date)
print("24K:", rate_24k)
print("22K:", rate_22k)
print("Update Time:", update_time)

# =========================
# PREPARE DATA
# =========================

data = {
    "rate_22k": float(rate_22k),
    "rate_24k": float(rate_24k),
    "source": "Live Chennai",
    "update_time": update_time
}

# =========================
# CLEANUP OLD RECORDS
# =========================

try:
    supabase.rpc(
        "cleanup_gold_rates"
    ).execute()

    print("Old records cleaned")
except Exception as e:
    print("Cleanup Error:", e)

# =========================
# GET LATEST RECORD
# =========================

latest = (
    supabase.table("gold_rates")
    .select("*")
    .order("id", desc=True)
    .limit(1)
    .execute()
)

insert_data = True

if latest.data:

    last_row = latest.data[0]

    print("Previous 22K:", last_row["rate_22k"])
    print("Previous 24K:", last_row["rate_24k"])

    if (
        float(last_row["rate_22k"]) == float(rate_22k)
        and float(last_row["rate_24k"]) == float(rate_24k)
    ):
        insert_data = False
        print("Rate unchanged. Skipping insert.")

# =========================
# INSERT NEW DATA
# =========================

if insert_data:
    try:
        result = (
            supabase.table("gold_rates")
            .insert(data)
            .execute()
        )

        print("Inserted Successfully")

    except Exception as e:
        print("Insert Error:", e)

print("Scraper Finished Successfully")
if insert_data:
    result = supabase.table("gold_rates").insert(data).execute()

    print("Inserted Successfully")

