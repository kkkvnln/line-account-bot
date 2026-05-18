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
handler = WebhookHandler('44b024ae1f419f8443292df01c92d504')

DATA_FILE = "group_account.json"

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
            "group_name": "預設名稱",
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
    group_name = g["group_name"]

    # === 查詢ID ===
    if msg == "/查詢ID":
        reply_text = f"🆔 使用者ID：{user_id}\n🆔 群組/對話ID：{group_id}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # === 設定群組資訊 ===
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

    # === 清帳 === 純文字
    if msg == "/清帳":
        g["total_money"] = 0
        g["last_money"] = 0
        g["record_list"] = []
        save_group_data(group_id, g)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅【{group_name}】已全部歸零"))
        return

    # === 撤回 === 純文字
    if msg == "/撤回":
        if not g["record_list"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無記錄可撤回"))
            return
        last = g["record_list"].pop()
        g["total_money"] -= last["money"]
        g["last_money"] = g["record_list"][-1]["money"] if g["record_list"] else 0
        save_group_data(group_id, g)

        if g["total_money"] > 0:
            status = f"目前欠{group_name}：{g['total_money']} {g['currency']}"
        else:
            status = f"目前{group_name}欠：{abs(g['total_money'])} {g['currency']}"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"↩️ 撤回成功\n已刪除：{last['money']} ({last['note']})\n{status}"))
        return

    # === 查帳 === 純文字
    if msg == "/查帳":
        if g["total_money"] > 0:
            status = f"📊【{group_name}】\n目前欠：{g['total_money']} {g['currency']}"
        else:
            status = f"📊【{group_name}】\n對方欠：{abs(g['total_money'])} {g['currency']}"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=status))
        return

    # 運算記帳 僅+ -開頭 後支援加減乘除+備註
    try:
        msg_parts = msg.split(" ", 1)
        expr = msg_parts[0].strip()
        note = msg_parts[1].strip() if len(msg_parts) > 1 else "無"

        if re.fullmatch(r'^[+-][\d+\-*/]+$', expr):
            total = round(eval(expr), 2)

            old_last = g["last_money"]
            g["last_money"] = total
            g["total_money"] += total
            g["record_list"].append({"money": total, "note": note})
            save_group_data(group_id, g)

            if g["total_money"] > 0:
                status = f"目前欠{group_name}：{g['total_money']} {g['currency']}"
            else:
                status = f"目前{group_name}欠：{abs(g['total_money'])} {g['currency']}"

            card = build_account_card(
                title="✅ 記帳成功",
                last_amount=old_last,
                current_amount=total,
                status_text=status,
                note=note,
                currency=g['currency']
            )
            line_bot_api.reply_message(event.reply_token, card)
            return
    except:
        pass

    # 幫助提示
    help_txt = """📝 記帳指令
/查詢ID
/設定群組資訊@名稱@幣別
+100  -50
+100*10  -2640*30
/查帳 /清帳 /撤回"""
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_txt))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
