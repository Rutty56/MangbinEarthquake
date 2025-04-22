import requests
import xml.etree.ElementTree as ET
from datetime import datetime

URL = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
USERS_FILE = "registered_users.txt"

def fetch_earthquakes():
    try:
        response = requests.get(URL, timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        earthquakes = []
        for elem in root.findall("DailyEarthquakes"):
            earthquakes.append({
                "TitleThai": elem.findtext("TitleThai"),
                "OriginThai": elem.findtext("OriginThai"),
                "DateTimeThai": elem.findtext("DateTimeThai"),
                "Magnitude": elem.findtext("Magnitude"),
                "Depth": elem.findtext("Depth"),
                "Latitude": elem.findtext("Latitude"),
                "Longitude": elem.findtext("Longitude"),
            })
        return earthquakes
    except Exception as e:
        print("Error fetching data:", e)
        return []

def get_recent_earthquakes(earthquakes, limit=3):
    try:
        earthquakes.sort(key=lambda x: datetime.strptime(x["DateTimeThai"], "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
        return earthquakes[:limit]
    except Exception as e:
        print("Error sorting earthquakes:", e)
        return []

def save_registered_user(user_id):
    users = get_registered_users()
    if user_id not in users:
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(user_id + "\n")

def get_registered_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []
