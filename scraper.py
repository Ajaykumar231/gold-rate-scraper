import re
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

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

soup = BeautifulSoup(response.text, "html.parser")

text = soup.get_text(" ", strip=True)

# Get update time
time_match = re.search(
    r"Last Update Time:\s*([0-9/: ]+[APMapm]{2})",
    text
)

update_time = ""

if time_match:
    update_time = time_match.group(1).strip()

# Get first date row values
gold_match = re.search(
    r"(\d{2}/[A-Za-z]{3}/\d{4})\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)",
    text
)
if gold_match:

    date = gold_match.group(1)

    rate_24k = gold_match.group(2).replace(",", "")
    rate_22k = gold_match.group(4).replace(",", "")

    print("Date:", date)
    print("24K:", rate_24k)
    print("22K:", rate_22k)
    print("Update:", update_time)

    data = {
    "rate_22k": float(rate_22k),
    "rate_24k": float(rate_24k),
    "source": "Live Chennai",
    "update_time": update_time
}

# Delete records older than 7 days
supabase.rpc(
    "cleanup_gold_rates"
).execute()

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

    if (
        float(last_row["rate_22k"]) == float(rate_22k)
        and float(last_row["rate_24k"]) == float(rate_24k)
    ):
        insert_data = False
        print("Rate unchanged. Skipping insert.")

if insert_data:
    result = supabase.table("gold_rates").insert(data).execute()

    print("Inserted Successfully")

