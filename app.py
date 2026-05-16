from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# 你的金鑰
line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

# 記帳專用
history = []
balance = 0.0

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    try:
        if "events" in data:
            for event in data["events"]:
                if event["type"] == "message" and event["message"]["type"] == "text":
                    token = event["replyToken"]
                    msg = event["message"]["text"].strip()

                    # 只允許這 4 種指令
                    if not (msg.startswith("+") or msg.startswith("-") or msg == "/清帳" or msg == "/撤回"):
                        continue

                    reply = process(msg)
                    if reply:
                        line_bot_api.reply_message(token, reply)
    except:
        pass
    return "OK"

def process(msg):
    global balance
    try:
        # + 收入
        if msg.startswith("+"):
            num = float(msg[1:])
            history.append(balance)
            balance += num
            status = get_status()
            return TextSendMessage(text=f"本次金額 {msg} 台幣\n{status}")

        # - 支出
        if msg.startswith("-"):
            num = float(msg[1:])
            history.append(balance)
            balance -= num
            status = get_status()
            return TextSendMessage(text=f"本次金額 {msg} 台幣\n{status}")

        # 清帳
        if msg == "/清帳":
            history.append(balance)
            balance = 0.0
            return TextSendMessage(text="✅ 已清帳")

        # 撤回
        if msg == "/撤回" and history:
            balance = history.pop()
            return TextSendMessage(text="✅ 刪除成功")

    except:
        pass
    return None

# 判斷顯示文字（正數 / 負數）
def get_status():
    if balance > 0:
        return f"目前欠虎爺 {abs(balance):.0f} 台幣"
    elif balance < 0:
        return f"目前虎爺欠 {abs(balance):.0f} 台幣"
    else:
        return "目前金額：0 台幣"

if __name__ == "__main__":
    app.run(host="0.0.0.0")
