from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 請務必確認以下兩個值和 LINE 後台完全一致
CHANNEL_ACCESS_TOKEN = "fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "44b024ae1f419f88443292df01c92d504"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        abort(500)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        text = event.message.text
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"✅ 驗證成功！收到訊息：{text}")
        )
    except Exception as e:
        app.logger.error(f"Message handling error: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
