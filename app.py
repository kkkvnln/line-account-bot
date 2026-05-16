from flask import Flask, request
from linebot import LineBotApi
from linebot.models import *

app = Flask(__name__)

line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

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

                    if msg.startswith("+") or msg.startswith("-") or msg == "/清帳" or msg == "/撤回":
                        reply = handle(msg)
                        if reply:
                            line_bot_api.reply_message(token, reply)
    except:
        pass
    return "OK"

def handle(msg):
    global current
    try:
        if msg.startswith("+"):
            num = eval(msg[1:])
            history.append(current)
            current += num
            return card(msg, num, history[-1], current)

        if msg.startswith("-"):
            num = eval(msg[1:])
            history.append(current)
            current -= num
            return card(msg, num, history[-1], current)

        if msg == "/清帳":
            history.append(current)
            current = 0.0
            return TextSendMessage(text="✅ 已清帳")

        if msg == "/撤回" and history:
            current = history.pop()
            return TextSendMessage(text=f"↩️ 已撤回\n目前：{current:.2f}")
    except:
        pass
    return None

def card(exp, change, last, now):
    return FlexSendMessage(
        alt_text="紀錄",
        contents=BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text="計算結果", color="#009944", size="xl", weight="bold"),
                    BoxComponent(layout="horizontal", margin="lg", contents=[
                        SpacerComponent(),
                        TextComponent(text=f"{exp}={change:.2f}", color="#993300", size="lg")
                    ]),
                    SeparatorComponent(margin="lg"),
                    BoxComponent(layout="horizontal", margin="lg", contents=[
                        TextComponent(text="上次金額", size="lg"),
                        SpacerComponent(),
                        TextComponent(text=f"{last:.2f} 台幣", color="#993300", size="lg")
                    ]),
                    BoxComponent(layout="horizontal", margin="lg", contents=[
                        TextComponent(text="本次金額", size="lg"),
                        SpacerComponent(),
                        TextComponent(text=f"{change:.2f} 台幣", color="#993300", size="lg")
                    ]),
                    BoxComponent(layout="horizontal", margin="lg", contents=[
                        TextComponent(text="目前虎爺欠", size="lg"),
                        SpacerComponent(),
                        TextComponent(text=f"{now:.2f} 台幣", color="#993300", size="lg")
                    ]),
                    SeparatorComponent(margin="lg"),
                    BoxComponent(layout="horizontal", margin="lg", contents=[
                        TextComponent(text="備註", size="lg"),
                        SpacerComponent()
                    ])
                ]
            )
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0")
