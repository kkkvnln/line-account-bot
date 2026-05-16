from flask import Flask, request
from linebot import LineBotApi
from linebot.models import *
import re

app = Flask(__name__)

# 你的金鑰
line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

# 全域變數：上次金額、目前金額
last_money = 0.0
current_money = 0.0

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    try:
        if "events" in data:
            for event in data["events"]:
                if event["type"] == "message" and event["message"]["type"] == "text":
                    token = event["replyToken"]
                    msg = event["message"]["text"].strip()
                    reply = handle_msg(msg)
                    line_bot_api.reply_message(token, reply)
    except:
        pass
    return "OK"

def handle_msg(msg):
    global last_money, current_money

    # 1. 四則運算（同時當作本次金額）
    if re.match(r'^[\d\+\-\*/\s\.]+$', msg):
        try:
            result = eval(msg)
            last_money = current_money
            current_money += result
            return build_flex_card(
                calc_str=msg,
                calc_result=result,
                last=last_money,
                current=current_money
            )
        except:
            return TextSendMessage(text="⚠️ 計算錯誤，請輸入正確的數學式")

    # 2. 查詢目前金額
    if msg in ["餘額", "查餘額", "小金庫欠"]:
        return build_flex_card(
            calc_str="查詢",
            calc_result=0,
            last=last_money,
            current=current_money
        )

    # 3. 重置
    if msg == "重置":
        last_money = 0.0
        current_money = 0.0
        return TextSendMessage(text="🔄 金額已重置為 0")

    # 預設回覆
    return TextSendMessage(text="✅ 收到！\n輸入數學式（例：-2460*2）或「餘額」查詢")

# 建立和你圖中一樣風格的 Flex 卡片
def build_flex_card(calc_str, calc_result, last, current):
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                # 標題
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
                            text=f"{calc_str}={calc_result}",
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
                            text=f"{last:.2f} 台幣",
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
                            text=f"{calc_result:.2f} 台幣",
                            color="#993300",
                            size="lg"
                        )
                    ]
                ),
                # 目前小金庫欠
                BoxComponent(
                    layout="horizontal",
                    margin="lg",
                    contents=[
                        TextComponent(text="目前虎爺欠", size="lg"),
                        SpacerComponent(),
                        TextComponent(
                            text=f"{current:.2f} 台幣",
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
