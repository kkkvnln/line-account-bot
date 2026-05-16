from flask import Flask, request
import os

# LINE SDK V3 最簡版本
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 你的憑證
configuration = Configuration(
    access_token="fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08IgrGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU="
)
handler = WebhookHandler("44b024ae1f419f8443292df01c92d504")

# ----------------------
# 最簡單路由
# ----------------------
@app.route("/")
def index():
    return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    sig  = request.headers.get("X-Line-Signature")

    try:
        handler.handle(body, sig)
    except:
        pass

    return "OK"

# ----------------------
# 「任何訊息」都回覆
# ----------------------
@handler.add(MessageEvent, message=TextMessageContent)
def handle(event):
    try:
        with ApiClient(configuration) as api:
            MessagingApi(api).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="✅ 我收到了！")]
                )
            )
    except:
        pass

# ----------------------
# 啟動
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
