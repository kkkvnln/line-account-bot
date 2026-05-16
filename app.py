from flask import Flask, request
from linebot import LineBotApi
from linebot.models import *

app = Flask(__name__)

# 你的金鑰
line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

# 記帳資料
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

                    # 只回應指定指令
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
            return build_card(msg, num, history[-1], balance)

        # - 支出
        if msg.startswith("-"):
            num = float(msg[1:])
            history.append(balance)
            balance -= num
            return build_card(msg, num, history[-1], balance)

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

# 建立和你圖中一模一樣的表格卡片
def build_card(expression, change, last_balance, current_balance):
    # 根據餘額正負顯示文字
    if current_balance > 0:
        status_text = "目前欠虎爺"
        display_balance = abs(current_balance)
    elif current_balance < 0:
        status_text = "目前虎爺欠"
        display_balance = abs(current_balance)
    else:
        status_text = "目前金額"
        display_balance = 0

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                # 標題：計算結果
                TextComponent(
                    text="計算結果",
                    color="#009944",
                    size="xl",
                    weight="bold"
                ),
                # 計算式
                BoxComponent(
                    layout="horizontal",
                    margin="lg",
                    contents=[
                        SpacerComponent(),
                        TextComponent(
                            text=f"{expression}={change}",
                            color="#993300",
                            size="lg"
                        )
                    ]
                ),
                SeparatorComponent(margin="lg"),
                # 上次金額
                BoxComponent(
                    layout="horizontal",
                    margin="lg",
                    contents=[
                        TextComponent(text="上次金額", size="lg"),
                        SpacerComponent(),
                        TextComponent(
                            text=f"{last_balance:.2f} 台幣",
                            color="#993300",
                            size="lg"
                        )
                    ]
                ),
                # 本次金額
                BoxComponent(
                    layout="horizontal",
                    margin="lg",
                    contents=[
                        TextComponent(text="本次金額", size="lg"),
                        SpacerComponent(),
                        TextComponent(
                            text=f"{change:.2f} 台幣",
                            color="#993300",
                            size="lg"
                        )
                    ]
                ),
                # 目前虎爺欠/目前欠虎爺
                BoxComponent(
                    layout="horizontal",
                    margin="lg",
                    contents=[
                        TextComponent(text=status_text, size="lg"),
                        SpacerComponent(),
                        TextComponent(
                            text=f"{display_balance:.2f} 台幣",
                            color="#993300",
                            size="lg"
                        )
                    ]
                ),
                SeparatorComponent(margin="lg"),
                # 備註欄
                BoxComponent(
                    layout="horizontal",
                    margin="lg",
                    contents=[
                        TextComponent(text="備註", size="lg"),
                        SpacerComponent()
                    ]
                )
            ]
        )
    )

    return FlexSendMessage(
        alt_text="計算結果卡片",
        contents=bubble
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0")
