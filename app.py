from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from earthquake_check import fetch_earthquakes, filter_significant_quakes, send_alert, save_registered_user
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
config = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi(configuration=config)
handler = WebhookHandler(channel_secret=os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/")
def index():
    data = fetch_earthquakes()
    filtered = filter_significant_quakes(data)
    send_alert(filtered)
    return "Checked earthquakes ✅"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
        abort(400)

    return "OK"

@handler.add(MessageEvent)
def handle_message(event):
    if not isinstance(event.message, TextMessageContent):
        return

    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text == "เปิดการแจ้งเตือน":
        save_registered_user(user_id)
        reply = "✅ คุณได้สมัครรับการแจ้งเตือนแผ่นดินไหวแล้ว"
    elif text == "แผ่นดินไหวล่าสุด":
        data = fetch_earthquakes()
        filtered = filter_significant_quakes(data, magnitude_threshold=0)
        if filtered:
            reply = "\n\n".join(
                f"📍 {q['Location']} - ขนาด {q['Magnitude']} ML\n⏰ {q['DateTime']}"
                for q in filtered[:3]
            )
        else:
            reply = "ยังไม่มีข้อมูลแผ่นดินไหวล่าสุดครับ"
    else:
        reply = "พิมพ์ 'เปิดการแจ้งเตือน' เพื่อเริ่มรับแจ้งเตือนแผ่นดินไหว"

    message = TextMessage(text=reply)
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[message]
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
