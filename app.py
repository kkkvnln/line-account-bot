from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction
import re

app = Flask(__name__)

line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")

money = 0

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    try:
        if data and "events" in data:
            for event in data["events"]:
                if event["type"] == "message" and event["message"]["type"] == "text":
                    token = event["replyToken"]
                    text = event["message"]["text"].strip()
                    reply_msg = handle_msg(text)
                    line_bot_api.reply_message(token, reply_msg)
    except:
        pass
    return "OK"

def handle_msg(text):
    global money

    # 計算機
    if re.match(r'^[\d\+\-\*/\s]+$', text):
        try:
            res = eval(text)
            return TextSendMessage(text=f"🧮 結果：{res}")
        except:
            return TextSendMessage(text="⚠️ 計算錯誤")

    # 記帳
    if text.startswith("+"):
        try:
            num = int(text[1:])
            money += num
            return card_template(f"✅ 記帳成功", f"目前餘額：{money}")
        except:
            return TextSendMessage(text="格式：+100")

    if text.startswith("-"):
        try:
            num = int(text[1:])
            money -= num
            return card_template(f"✅ 記帳成功", f"目前餘額：{money}")
        except:
            return TextSendMessage(text="格式：-50")

    if text in ["餘額","查餘額"]:
        return card_template("💰 目前餘額", str(money))

    if text == "重置":
        money = 0
        return card_template("🔄 已重置", "餘額：0")

    # 選單卡片
    if text in ["選單","功能","菜單","開始"]:
        return menu_card()

    return TextSendMessage(text="✅ 收到訊息！輸入「選單」看功能")

# 卡片訊息
def card_template(title, text):
    return TemplateSendMessage(
        alt_text="記帳卡片",
        template=ButtonsTemplate(
            title=title,
            text=text,
            actions=[
                MessageAction(label="查餘額", text="餘額"),
                MessageAction(label="重置", text="重置")
            ]
        )
    )

# 選單卡片
def menu_card():
    return TemplateSendMessage(
        alt_text="功能選單",
        template=ButtonsTemplate(
            title="📋 記帳計算機",
            text="請選擇功能",
            actions=[
                MessageAction(label="➕ 收入", text="+"),
                MessageAction(label="➖ 支出", text="-"),
                MessageAction(label="💰 查餘額", text="餘額"),
                MessageAction(label="🔄 重置", text="重置")
            ]
        )
    )

if __name__ == "__main__":
    app.run()
