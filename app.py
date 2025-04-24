import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, TextSendMessage, MessageEvent
from dotenv import load_dotenv
from utils.users import save_registered_user, get_registered_users, remove_registered_user

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("Missing LINE channel credentials in .env")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
        return "ไม่สามารถระบุเวลาได้"

def fetch_earthquakes():
    url = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
    response = requests.get(url)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        earthquakes = []

        for quake in root.findall(".//DailyEarthquakes"):
            origin_thai = quake.findtext("OriginThai", default="ไม่ระบุ")
            datetime_thai = quake.findtext("DateTimeThai", default="ไม่ระบุ")
            magnitude = quake.findtext("Magnitude", default="ไม่ระบุ")
            title_thai = quake.findtext("TitleThai", default="ไม่ระบุ")
            depth = quake.findtext("Depth", default="ไม่ระบุ")
            latitude = quake.findtext("Latitude", default="ไม่ระบุ")
            longitude = quake.findtext("Longitude", default="ไม่ระบุ")

            earthquake_data = {
                "OriginThai": origin_thai,
                "DateTimeThai": datetime_thai,
                "Magnitude": magnitude,
                "TitleThai": title_thai,
                "Depth": depth,
                "Latitude": latitude,
                "Longitude": longitude
            }
            earthquakes.append(earthquake_data)

        return earthquakes
    else:
        print(f"Error fetching earthquake data: {response.status_code}")
        return []

def get_recent_earthquakes(earthquakes, limit=3):
    return earthquakes[:limit]

@app.route("/", methods=["GET"])
def index():
    return "LINE Bot Earthquake Alert is running"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print("Invalid signature:", e)
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text in ["สมัคร"]:
        save_registered_user(user_id)
        reply_text = "✅ สมัครรับการแจ้งเตือนแผ่นดินไหวเรียบร้อยแล้ว!"
    elif text in ["ยกเลิกสมัคร"]:
        remove_registered_user(user_id)
        reply_text = "❌ ยกเลิกการรับแจ้งเตือนแผ่นดินไหวเรียบร้อยแล้ว"
    elif "แผ่นดินไหวล่าสุด" in text:
        earthquakes = fetch_earthquakes()
        recent_quakes = get_recent_earthquakes(earthquakes)

        if recent_quakes:
            reply_text = "🌍 แผ่นดินไหวล่าสุด\n\n"
            for i, quake in enumerate(recent_quakes, 1):
                formatted_time = format_datetime_thai(quake['DateTimeThai'])
                reply_text += (
                    f"{i}️⃣ ขนาด: {quake['Magnitude']} แมกนิจูด\n"
                    f"   สถานที่: {quake['OriginThai']}\n"
                    f"   ความลึก: {quake['Depth']} กม\n"
                    f"   พิกัด: {quake['Latitude']}, {quake['Longitude']}\n"
                    f"   เวลา: {formatted_time}\n\n"
                )
        else:
            reply_text = "ไม่พบข้อมูลแผ่นดินไหวล่าสุด."
    else:
        reply_text = (
            "พิมพ์ว่า 'สมัคร' เพื่อรับการแจ้งเตือนแผ่นดินไหวอัตโนมัติ 🌏\n"
            "หรือพิมพ์ว่า 'แผ่นดินไหวล่าสุด' เพื่อดูข้อมูลล่าสุด\n"
            "พิมพ์ว่า 'ยกเลิกสมัคร' หากไม่ต้องการรับการแจ้งเตือน"
        )

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
