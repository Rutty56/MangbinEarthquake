import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessage as TextMessageContent
from dotenv import load_dotenv
from earthquake_check import fetch_earthquakes, get_recent_earthquakes, save_registered_user, get_registered_users

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error handling request:", e)
        abort(400)
    return "OK"

@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
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
                    reply_text += (f"{i}. ขนาด: {quake.get('Magnitude')} ML\n"
                                   f"   สถานที่: {quake.get('Location')}\n"
                                   f"   วันที่: {quake.get('DateTime')}\n\n")
            else:
                reply_text = "ไม่พบข้อมูลแผ่นดินไหวล่าสุด."
        else:
            reply_text = "พิมพ์ว่า 'สมัคร' เพื่อเริ่มรับการแจ้งเตือนแผ่นดินไหว 🌏 หรือ 'แผ่นดินไหวล่าสุด' เพื่อดูข้อมูลแผ่นดินไหวล่าสุด"

        reply_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        messaging_api.reply_message(reply_request)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
