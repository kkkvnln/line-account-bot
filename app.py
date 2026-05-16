from flask import Flask, request
from linebot import LineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import re

app = Flask(__name__)

# 你的 Access Token（不用改）
line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

# 記帳用
money = 0

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    try:
        if data and "events" in data:
            for event in data["events"]:
                if event["type"] == "message" and event["message"]["type"] == "text":
                    reply_token = event["replyToken"]
                    text = event["message"]["text"].strip()
                    reply = handle_text(text)
                    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply))
    except:
        pass
    return "OK", 200

def handle_text(text):
    global money

    # 1. 四則運算（自動偵測 + - * /）
    if re.match(r'^[\d\+\-\*/\s]+$', text):
        try:
            result = eval(text)
            return f"🧮 計算結果：{result}"
        except:
            return "⚠️ 計算錯誤"

    # 2. 記帳功能 +100 / -50
    if text.startswith("+"):
        try:
            num = int(text[1:])
            money += num
            return f"✅ 記帳成功\n目前餘額：{money}"
        except:
            return "⚠️ 格式：+數字（例：+100）"

    if text.startswith("-"):
        try:
            num = int(text[1:])
            money -= num
            return f"✅ 記帳成功\n目前餘額：{money}"
        except:
            return "⚠️ 格式：-數字（例：-50）"

    # 3. 查餘額
    if text in ["餘額", "查餘額", "錢"]:
        return f"💰 目前餘額：{money}"

    # 4. 重置記帳
    if text == "重置":
        money = 0
        return "🔄 餘額已重置為 0"

    # 5. 預設回覆
    return f"✅ 收到：{text}\n\n👉 可使用：\n+100、-50、餘額、重置、1+1、2*3"

if __name__ == "__main__":
    app.run(host="0.0.0.0")
