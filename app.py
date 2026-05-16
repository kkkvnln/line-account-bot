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

app = Flask(__name__)

# 你的 LINE Bot 憑證
line_bot_api = LineBotApi('fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('44b024ae1f419f8443292df01c92d504')

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
    if not os.path.exists(DATA_FILE):
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
                        TextComponent(text='本次金額', color='#555555', size='md'),
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

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    group_id = event.source.group_id if hasattr(event.source, "group_id") else event.source.user_id
    user_id = event.source.user_id
    msg = event.message.text.strip()
    g = get_group_data(group_id)

    # 判斷收支記帳格式
    is_money_cmd = (msg.startswith("+") or msg.startswith("-")) and len(msg.split(" ",1)[0])>1 and msg.split(" ",1)[0][1:].isdigit()
    # 判斷系統指令
    is_sys_cmd = any(msg.startswith(c) for c in CMD_LIST)

    # 日常聊天閒聊直接忽略不回覆
    if not is_sys_cmd and not is_money_cmd:
        return

    # 所有人可查詢ID
    if msg == "/ID":
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"你的LINE UserID：\n{user_id}"))
        return

    # 非管理員禁止使用功能
    if user_id not in ADMIN_LIST:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="❌ 僅管理員可操作本機器人"))
        return

    # 設定群組資訊
    if msg.startswith("/設定群組資訊@"):
        parts = msg.split("@")
        if len(parts) == 3:
            g["group_name"] = parts[1]
            g["currency"] = parts[2]
            save_group_data(group_id, g)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 設定成功\n群組：{g['group_name']}\n幣別：{g['currency']}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 格式：/設定群組資訊@小金庫@台幣"))
        return

    # 清帳歸零
    if msg == "/清帳":
        g["total_money"] = 0
        g["last_money"] = 0
        g["record_list"] = []
        save_group_data(group_id, g)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"✅【{g['group_name']}】已歸零"))
        return

    # 撤回上一筆記錄
    if msg == "/撤回":
        if not g["record_list"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無記錄可撤回"))
            return
        last = g["record_list"].pop()
        g["total_money"] -= last["money"]
        g["last_money"] = g["record_list"][-1]["money"] if g["record_list"] else 0
        save_group_data(group_id, g)

        if g["total_money"] > 0:
            status = f"你欠{g['group_name']}：{g['total_money']} {g['currency']}"
        else:
            status = f"{g['group_name']}欠你：{abs(g['total_money'])} {g['currency']}"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"↩️ 撤回成功\n已刪除：{last['money']} ({last['note']})\n{status}"))
        return

    # 查帳
    if msg == "/查帳":
        if g["total_money"] > 0:
            status = f"你欠{g['group_name']}：{g['total_money']} {g['currency']}"
        else:
            status = f"{g['group_name']}欠你：{abs(g['total_money'])} {g['currency']}"

        card = build_account_card(
            title=f"【{g['group_name']}】帳務查詢",
            last_amount=g["last_money"],
            current_amount=0,
            status_text=status,
            note="無",
            currency=g['currency']
        )
        line_bot_api.reply_message(event.reply_token, card)
        return

    # 收支記帳
    parts = msg.split(" ", 1)
    money_str = parts[0]
    if (money_str.startswith("+") or money_str.startswith("-")) and money_str[1:].isdigit():
        amount = int(money_str)
        note = parts[1] if len(parts) >= 2 else "無備註"

        old_last = g["last_money"]
        g["last_money"] = amount
        g["total_money"] += amount
        g["record_list"].append({"money": amount, "note": note})
        save_group_data(group_id, g)

        if g["total_money"] > 0:
            status = f"目前你欠{g['group_name']}：{g['total_money']} {g['currency']}"
        else:
            status = f"目前{g['group_name']}欠你：{abs(g['total_money'])} {g['currency']}"

        card = build_account_card(
            title="✅ 記帳成功",
            last_amount=old_last,
            current_amount=amount,
            status_text=status,
            note=note,
            currency=g['currency']
        )
        line_bot_api.reply_message(event.reply_token, card)
        return

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
