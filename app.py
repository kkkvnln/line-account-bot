from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import MessagingApi, ApiClient, Configuration
from linebot.v3.messaging.models import *
import os

app = Flask(__name__)

# 設定
CHANNEL_ACCESS_TOKEN = "fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "44b024ae1f419f88443292df01c92d504"

# 初始化 LINE SDK v3
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(CHANNEL_SECRET)

# ----------------------
# 這裡才能寫 @handler.add
# ----------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        txt = event.message.text
        reply = TextMessage(text=f"✅ 機器人正常運作！你傳了：{txt}")
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply]
            )
        )
    except Exception as e:
        print(e)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run()
