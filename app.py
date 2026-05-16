from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, SeparatorComponent
)
import json
import os
import re

app = Flask(__name__)

# 你的 LINE Bot 憑證
line_bot_api = LineBotApi('fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('U27c2bccc9e129d9f417ecaa81a2cee14')

DATA_FILE = "group_account.json"

# 已添加兩位管理員
ADMIN_LIST = [
    "U79559883cba75878fca84feebb5f5cf4",
    "U27c2bccc9e129d9f417ecaa81a2cee14"
]

# 定義所有合法指令
CMD_LIST = [
    "/ID",
    "/設定群組資訊",
    "/清帳",
    "/撤回",
    "/查帳"
]

# 初始化數據
def init_total_data():
    if not os.exists(DATA_FILE):
        save_total_data({})

def load_total_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_total_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 取得群組資料
def get_group_data(group_id):
    total_data = load_total_data()
    if group_id not in total_data:
        total_data[group_id] = {
            "group_name": "未命名",
            "currency": "台幣",
            "total_money": 0,
            "last_money": 0,
            "record_list": []
        }
        save_total_data(total_data)
    return total_data[group_id]

def save_group_data(group_id, data):
    total_data = load_total_data()
    total_data[group_id] = data
    save_total_data(total_data)

init_total_data()

# 建立卡片
def build_account_card(title, last_amount, current_amount, status_text, note, currency):
    bubble = BubbleContainer(
        direction='ltr',
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text=title, color='#22C55E', size='xl', weight='bold'),
                SeparatorComponent(margin="md"),
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text='上次金額', color='#555555', size='md'),
                        TextComponent(text=f"{last_amount} {currency}", color='#D2691E', size='md', align='end')
                    ]
                ),
                BoxComponent(
                    layout='horizontal',
                    margin="md",
                    contents=[
                        TextComponent(text='本次', color='#555555', size='md'),
                        TextComponent(text=f"{current_amount} {currency}", color='#D2691E', size='md', align='end')
                    ]
                ),
                SeparatorComponent(margin="md"),
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text=status_text.split("：")[0], color='#555555', size='md'),
                        TextComponent(text=status_text.split("：")[1], color='#D2691E', size='md', align='end')
                    ]
                ),
                SeparatorComponent(margin="md"),
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text='備註', color='#555555', size='md'),
                        TextComponent(text=note, color='#888888', size='md', align='end')
                    ]
                )
            ]
        )
    )
    return FlexSendMessage(alt_text=title, contents=bubble)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 安全計算四則運算
def calc_exp(s):
    s = s.replace("×", "*").replace("÷", "/").replace(" ", "")
    if not re.fullmatch(r'[\d+\-*/.]+', s):
        return None
    try:
        return eval(s, {"__builtins__":None}, {})
    except:
        return None

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    group_id = event.source.group_id if hasattr(event.source, "group_id") else event.source.user_id
    user_id = event.source.user_id
    msg = event.message.text.strip()
    g = get_group_data(group_id)

    is_sys_cmd = any(msg.startswith(c) for c in CMD_LIST)
    is_calc = calc_exp(msg) is not None

    if not is_sys_cmd and not is_calc:
        return

    if msg == "/ID":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"你的LINE UserID：\n{user_id}"))
        return

    if user_id not in ADMIN_LIST:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 僅管理員可操作"))
        return

    if msg.startswith("/設定群組資訊@"):
        parts = msg.split("@")
        if len(parts) == 3:
            g["group_name"] = parts[1]
            g["currency"] = parts[2]
            save_group_data(group_id, g)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(f"✅ 設定成功\n群組：{g['group_name']}"))
        return

    if msg == "/清帳":
        g["total_money"] = 0
        g["last_money"] = 0
        g["record_list"] = []
        save_group_data(group_id, g)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"✅【{g['group_name']}】已歸零"))
        return

    if msg == "/撤回":
        if not g["record_list"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ 無記錄"))
            return
        last = g["record_list"].pop()
        g["total_money"] -= last["money"]
        g["last_money"] = g["record_list"][-1]["money"] if g["record_list"] else 0
        save_group_data(group_id, g)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("↩️ 已撤回"))
        return

    if msg == "/查帳":
        status = f"你欠{g['group_name']}：{g['total_money']}" if g["total_money"]>0 else f"{g['group_name']}欠你：{abs(g['total_money'])}"
        card = build_account_card(f"【{g['group_name']}】查帳", g["last_money"], 0, status, "無", g['currency'])
        line_bot_api.reply_message(event.reply_token, card)
        return

    # 四則運算記帳
    val = calc_exp(msg)
    if val is not None:
        total = round(val, 2)
        old = g["last_money"]
        g["last_money"] = total
        g["total_money"] += total
        g["record_list"].append({"money":total, "note":msg})
        save_group_data(group_id, g)
        status = f"你欠{g['group_name']}：{g['total_money']}" if g["total_money"]>0 else f"{g['group_name']}欠你：{abs(g['total_money'])}"
        card = build_account_card("✅ 記帳成功", old, total, status, msg, g['currency'])
        line_bot_api.reply_message(event.reply_token, card)
        return

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
