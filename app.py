import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.models import TextMessage
from earthquake_check import fetch_earthquakes, get_recent_earthquakes, save_registered_user, get_registered_users

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
messaging_api = MessagingApi(configuration)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error handling request:", e)
        abort(400)
    return "OK"

@handler.add(MessageEvent)
def handle_message(event):
    if not isinstance(event.message, TextMessageContent):
        return

    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text == "สมัคร":
        save_registered_user(user_id)
        reply_text = "✅ สมัครรับการแจ้งเตือนแผ่นดินไหวเรียบร้อยแล้ว!"
    elif text == "แผ่นดินไหวล่าสุด":
        earthquakes = fetch_earthquakes()
        recent_quakes = get_recent_earthquakes(earthquakes, limit=3)
        if recent_quakes:
            reply_text = "🌍 แผ่นดินไหวล่าสุด 3 เหตุการณ์:\n\n"
            for i, quake in enumerate(recent_quakes, 1):
                reply_text += (f"{i}. {quake['TitleThai']}\n"
                               f"   ขนาด: {quake['Magnitude']} ML\n"
                               f"   ลึก: {quake['Depth']} กม.\n"
                               f"   เวลา: {quake['DateTimeThai']}\n\n")
        else:
            reply_text = "ไม่พบข้อมูลแผ่นดินไหวล่าสุด"
    else:
        reply_text = (
            "📌 พิมพ์ว่า:\n"
            "- 'สมัคร' เพื่อรับการแจ้งเตือนแผ่นดินไหวอัตโนมัติ\n"
            "- 'แผ่นดินไหวล่าสุด' เพื่อดูเหตุการณ์ล่าสุด 3 เหตุการณ์"
        )

    messaging_api.reply_message(
        event.reply_token,
        [TextMessage(text=reply_text)]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
