import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, TextSendMessage, MessageEvent
from dotenv import load_dotenv
from utils.users import save_registered_user, get_registered_users

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def fetch_earthquakes():
    url = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
    response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        earthquakes = []
        
        for quake in root.findall(".//DailyEarthquakes"):
            origin_thai = quake.find("OriginThai").text
            datetime_thai = quake.find("DateTimeThai").text
            magnitude = quake.find("Magnitude").text
            title_thai = quake.find("TitleThai").text

            earthquake_data = {
                "OriginThai": origin_thai,
                "DateTimeThai": datetime_thai,
                "Magnitude": magnitude,
                "TitleThai": title_thai
            }
            earthquakes.append(earthquake_data)
        
        return earthquakes
    return []

def get_recent_earthquakes(earthquakes, limit=3):
    return earthquakes[:limit]

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

    if text == "สมัคร":
        save_registered_user(user_id)
        reply_text = "✅ สมัครรับการแจ้งเตือนแผ่นดินไหวเรียบร้อยแล้ว!"
    elif text == "แผ่นดินไหวล่าสุด":
        earthquakes = fetch_earthquakes()
        recent_quakes = get_recent_earthquakes(earthquakes)
        
        if recent_quakes:
            reply_text = "🌍 แผ่นดินไหวล่าสุด:\n"
            for i, quake in enumerate(recent_quakes, 1):
                reply_text += (f"{i}. ขนาด: {quake['Magnitude']} แมกนิจูด\n"
                               f"   สถานที่: {quake['OriginThai']}\n"
                               f"   วันที่: {quake['DateTimeThai']}\n\n")
        else:
            reply_text = "ไม่พบข้อมูลแผ่นดินไหวล่าสุด."
    else:
        reply_text = "พิมพ์ว่า 'สมัคร' เพื่อเริ่มรับการแจ้งเตือนแผ่นดินไหว 🌏 หรือ 'แผ่นดินไหวล่าสุด' เพื่อดูข้อมูลแผ่นดินไหวล่าสุด"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
