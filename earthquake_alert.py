import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage
from utils.users import get_registered_users

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def fetch_earthquakes():
    url = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
    response = requests.get(url)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        earthquakes = []
        for quake in root.findall(".//DailyEarthquakes"):
            magnitude = float(quake.find("Magnitude").text)
            if magnitude >= 5.0:
                earthquakes.append({
                    "Magnitude": quake.find("Magnitude").text,
                    "OriginThai": quake.find("OriginThai").text,
                    "DateTimeThai": quake.find("DateTimeThai").text,
                    "Depth": quake.find("Depth").text or "ไม่ระบุ",
                    "Latitude": quake.find("Latitude").text or "ไม่ระบุ",
                    "Longitude": quake.find("Longitude").text or "ไม่ระบุ"
                })
        return earthquakes
    return []

def send_alerts():
    earthquakes = fetch_earthquakes()
    if not earthquakes:
        print("No significant earthquakes.")
        return

    users = get_registered_users()
    for quake in earthquakes:
        message = (
            f"🚨 แผ่นดินไหวรุนแรง!\n"
            f"ขนาด: {quake['Magnitude']} แมกนิจูด\n"
            f"สถานที่: {quake['OriginThai']}\n"
            f"ความลึก: {quake['Depth']} กม\n"
            f"พิกัด: {quake['Latitude']}, {quake['Longitude']}\n"
            f"เวลา: {quake['DateTimeThai']}"
        )
        for user_id in users:
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=message))
            except Exception as e:
                print(f"❌ Error sending to {user_id}: {e}")

if __name__ == "__main__":
    send_alerts(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
