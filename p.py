import requests
import csv
import re
from datetime import datetime
from time import sleep

# ============================
# 🔑 PUT YOUR API KEY HERE
# ============================
API_KEY = ""

INPUT_FILE = "s.txt"
OUTPUT_FILE = "short.csv"

# ============================
# Helpers
# ============================

def extract_video_id(url):
    match = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None

def iso_duration_to_seconds(duration):
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s

def extract_hashtags(description):
    return " ".join(re.findall(r"#\w+", description or ""))

# ============================
# Read URLs → Video IDs
# ============================

video_ids = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        vid = extract_video_id(line.strip())
        if vid:
            video_ids.append(vid)

video_ids = list(dict.fromkeys(video_ids))  # remove duplicates

if not video_ids:
    print("❌ No valid video IDs found.")
    exit()

# ============================
# Fetch Data (batch of 50)
# ============================

all_rows = []

for i in range(0, len(video_ids), 50):
    batch = video_ids[i:i+50]
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(batch),
        "key": API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("❌ API error:", response.text)
        exit()

    data = response.json()

    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        duration_seconds = iso_duration_to_seconds(content.get("duration", "PT0S"))
        is_short = duration_seconds <= 60

        row = {
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "published_at": snippet.get("publishedAt"),
            "views": stats.get("viewCount"),
            "likes": stats.get("likeCount"),
            "comments": stats.get("commentCount"),
            "duration_seconds": duration_seconds,
            "is_short": is_short,
            "hashtags": extract_hashtags(snippet.get("description")),
            "video_url": f"https://www.youtube.com/shorts/{item.get('id')}"
        }

        all_rows.append(row)

    sleep(0.3)  # polite delay

# ============================
# Write CSV
# ============================

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = [
        "video_id",
        "title",
        "published_at",
        "views",
        "likes",
        "comments",
        "duration_seconds",
        "is_short",
        "hashtags",
        "video_url"
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"✅ Done! {len(all_rows)} Shorts saved to {OUTPUT_FILE}")

