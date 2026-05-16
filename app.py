from flask import Flask, request
from linebot import LineBotApi
from linebot.models import *
import re

app = Flask(__name__)

line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

# 資料
history = []
current = 0.0

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    try:
        if "events" in data:
            for event in data["events"]:
                if event["type"] == "message" and event["message"]["type"] == "text":
                    token = event["replyToken"]
                    msg = event["message"]["text"].strip()

                    # 只允許這四種，其他完全不回
                    if not (
                        msg.startswith("+") or
                        msg.startswith("-") or
                        msg == "/清帳" or
                        msg == "/撤回"
                    ):
                        continue

                    reply = process(msg)
                    if reply:
                        line_bot_api.reply_message(token, reply)
    except:
        pass
    return "OK"

def process(msg):
    global current

    try:
        # + 加法
        if msg.startswith("+"):
            num = float(msg[1:])
            history.append(current)
            current += num
            return make_card(msg, num, history[-1], current)

        # - 減法
        if msg.startswith("-"):
            num = float(msg[1:])
            history.append(current)
            current -= num
            return make_card(msg, num, history[-1], current)

        # 清帳
        if msg == "/清帳":
            history.append(current)
            current = 0.0
            return TextSendMessage(text="✅ 已清帳")

        # 撤回
        if msg == "/撤回" and len(history) > 0:
            current = history.pop()
            return TextSendMessage(text=f"↩️ 已撤回\n目前：{current:.2f}")

    except:
        pass

    return None

# 卡片格式
def make_card(exp, change, last, now):
    return FlexSendMessage(
        alt_text="紀錄",
        contents=BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text="紀錄完成", color="#1E40AF", size="xl", weight="bold"),
                    BoxComponent(layout="horizontal", margin="md", contents=[
                        TextComponent(text=exp),
                        SpacerComponent(),
                        TextComponent(text=f"{change:.2f}")
                    ]),
                    SeparatorComponent(margin="md"),
                    BoxComponent(layout="horizontal", margin="md", contents=[
                        TextComponent(text="上次金額"), SpacerComponent(),
                        TextComponent(text=f"{last:.2f}")
                    ]),
                    BoxComponent(layout="horizontal", margin="md", contents=[
                        TextComponent(text="目前餘額"), SpacerComponent(),
                        TextComponent(text=f"{now:.2f}", color="#EAB308")
                    ])
                ]
            )
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0")
