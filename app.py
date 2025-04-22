from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from earthquake_check import fetch_earthquakes, filter_significant_quakes, send_alert, save_registered_user
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/")
def index():
    data = fetch_earthquakes()
    filtered = filter_significant_quakes(data)
    send_alert(filtered)
    return "Checked earthquakes ✅"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if text == "เปิดการแจ้งเตือน":
        save_registered_user(user_id)  # บันทึก user_id ด้วยการเข้ารหัส
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ คุณได้สมัครรับการแจ้งเตือนแผ่นดินไหวแล้ว")
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
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="พิมพ์ 'เปิดการแจ้งเตือน' เพื่อเริ่มรับแจ้งเตือนแผ่นดินไหว"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
