import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
from utils.users import get_registered_users

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def format_datetime_thai(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        month = thai_months[dt.month - 1]
        return f"{dt.day} {month} {dt.year} เวลา {dt.strftime('%H:%M')} น."
    except Exception:
        return dt_str

def fetch_earthquakes():
    url = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching earthquake data: {e}")
        return []

    earthquakes = []
    root = ET.fromstring(response.text)
    for quake in root.findall(".//DailyEarthquakes"):
        try:
            magnitude = float(quake.find("Magnitude").text)
        except (TypeError, ValueError):
            continue

        if magnitude >= 5.0:
            earthquakes.append({
                "Magnitude": quake.find("Magnitude").text or "ไม่ระบุ",
                "OriginThai": quake.find("OriginThai").text or "ไม่ระบุ",
                "DateTimeThai": quake.find("DateTimeThai").text or "ไม่ระบุ",
                "Depth": quake.find("Depth").text or "ไม่ระบุ",
                "Latitude": quake.find("Latitude").text or "ไม่ระบุ",
                "Longitude": quake.find("Longitude").text or "ไม่ระบุ"
            })

    return earthquakes

def send_alerts():
    earthquakes = fetch_earthquakes()
    if not earthquakes:
        print("No significant earthquakes.")
        return

    users = get_registered_users()
    if not users:
        print("No registered users.")
        return

    for quake in earthquakes:
        message = (
            f"🚨 แผ่นดินไหวรุนแรง!\n"
            f"ขนาด: {quake['Magnitude']} แมกนิจูด\n"
            f"สถานที่: {quake['OriginThai']}\n"
            f"ความลึก: {quake['Depth']} กม.\n"
            f"พิกัด: {quake['Latitude']}, {quake['Longitude']}\n"
            f"เวลา: {format_datetime_thai(quake['DateTimeThai'])}"
        )
        for user_id in users:
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=message))
                print(f"✅ Sent alert to {user_id}")
            except Exception as e:
                print(f"❌ Error sending to {user_id}: {e}")

if __name__ == "__main__":
    send_alerts()
