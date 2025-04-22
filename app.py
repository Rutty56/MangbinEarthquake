from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from earthquake_check import fetch_earthquakes, filter_significant_quakes, send_alert, save_registered_user

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

config = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_bot_api = MessagingApi.from_config(config)
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
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text == "เปิดการแจ้งเตือน":
        save_registered_user(user_id)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="✅ คุณได้สมัครรับการแจ้งเตือนแผ่นดินไหวแล้ว")]
            )
        )
    elif text == "แผ่นดินไหวล่าสุด":
        data = fetch_earthquakes()
        filtered = filter_significant_quakes(data, magnitude_threshold=0)
        if filtered:
            msg = "\n\n".join(
                f"📍 {q['Location']} - ขนาด {q['Magnitude']} ML\n⏰ {q['DateTime']}"
                for q in filtered[:3]
            )
        else:
            msg = "ยังไม่มีข้อมูลแผ่นดินไหวล่าสุดครับ"
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=msg)]
            )
        )
    else:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="พิมพ์ 'เปิดการแจ้งเตือน' เพื่อเริ่มรับแจ้งเตือนแผ่นดินไหว")]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
