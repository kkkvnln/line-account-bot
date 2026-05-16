from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

app = Flask(__name__)

# 你的金鑰
line_bot_api = LineBotApi("fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("44b024ae1f419f88443292df01c92d504")

# 記帳資料
history = []
balance = 0.0

# ======================
# 你原本能用的卡片格式
# ======================
def build_account_card(title, last_amount, current_amount, status_text, note, currency):
    bubble = BubbleContainer(
        direction='ltr',
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text=title, color='#22C55E', size='xl', weight='bold'),
                SeparatorComponent(margin="md"),
                BoxComponent(layout='horizontal',contents=[
                    TextComponent(text='上次金額', color='#555555', size='md'),
                    TextComponent(text=f"{last_amount} {currency}", color='#D2691E', size='md', align='end')
                ]),
                BoxComponent(layout='horizontal',margin="md",contents=[
                    TextComponent(text='本次金額', color='#555555', size='md'),
                    TextComponent(text=f"{current_amount} {currency}", color='#D2691E', size='md', align='end')
                ]),
                SeparatorComponent(margin="md"),
                BoxComponent(layout='horizontal',contents=[
                    TextComponent(text=status_text.split("：")[0], color='#555555', size='md'),
                    TextComponent(text=status_text.split("：")[1], color='#D2691E', size='md', align='end')
                ]),
                SeparatorComponent(margin="md"),
                BoxComponent(layout='horizontal',contents=[
                    TextComponent(text='備註', color='#555555', size='md'),
                    TextComponent(text=note, color='#888888', size='md', align='end')
                ])
            ]
        )
    )
    return FlexSendMessage(alt_text=title, contents=bubble)

# ======================
# 路由
# ======================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ======================
# 訊息處理
# ======================
@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    global balance, history

    msg = event.message.text.strip()

    # 只允許指令
    if not (msg.startswith("+") or msg.startswith("-") or msg == "/清帳" or msg == "/撤回"):
        return

    try:
        # + 加法
        if msg.startswith("+"):
            num = float(msg[1:])
            last = balance
            history.append(last)
            balance += num

            status = f"目前欠虎爺：{abs(balance):.0f}" if balance > 0 else f"目前虎爺欠：{abs(balance):.0f}"
            card = build_account_card(
                title="紀錄完成",
                last_amount=f"{last:.0f}",
                current_amount=f"{num:.0f}",
                status_text=status,
                note="",
                currency="台幣"
            )
            line_bot_api.reply_message(event.reply_token, card)
            return

        # - 減法
        if msg.startswith("-"):
            num = float(msg[1:])
            last = balance
            history.append(last)
            balance -= num

            status = f"目前欠虎爺：{abs(balance):.0f}" if balance > 0 else f"目前虎爺欠：{abs(balance):.0f}"
            card = build_account_card(
                title="紀錄完成",
                last_amount=f"{last:.0f}",
                current_amount=f"-{num:.0f}",
                status_text=status,
                note="",
                currency="台幣"
            )
            line_bot_api.reply_message(event.reply_token, card)
            return

        # 清帳
        if msg == "/清帳":
            history.append(balance)
            balance = 0.0
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已清帳"))
            return

        # 撤回
        if msg == "/撤回" and history:
            balance = history.pop()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 刪除成功"))
            return

    except:
        return

if __name__ == "__main__":
    app.run(host="0.0.0.0")
