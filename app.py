from flask import Flask, request
from linebot import LineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 你的 Access Token
line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

@app.route("/callback", methods=["POST"])
def callback():
    # 跳過簽名驗證，先確定能收到請求
    data = request.get_json()
    if data and "events" in data:
        for event in data["events"]:
            if event["type"] == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]
                text = event["message"]["text"]
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text=f"✅ 收到訊息：{text}")
                )
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")
