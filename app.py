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

# 填入你的LINE機器人憑證
line_bot_api = LineBotApi('fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('44b024ae1f419f8443292df01c92d504')

DATA_FILE = "group_account.json"

# 你的初始管理員ID（就是你自己的）
INIT_ADMINS = ["U79559883cba75878fca84feebb5f5cf4", "U27c2bccc9e129d9f417ecaa81a2cee14"]

# 初始化整體數據
def init_total_data():
    if not os.path.exists(DATA_FILE):
        save_total_data({})

def load_total_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_total_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化單一群組資料（加入初始管理員）
def get_group_data(group_id):
    total_data = load_total_data()
    if group_id not in total_data:
        total_data[group_id] = {
            "group_name": "未命名",
            "currency": "台幣",
            "total_money": 0,
            "last_money": 0,
            "record_list": [],
            "admins": [{"name": "初始管理員", "uid": uid} for uid in INIT_ADMINS]
        }
        save_total_data(total_data)
    return total_data[group_id]

def save_group_data(group_id, data):
    total_data = load_total_data()
    total_data[group_id] = data
    save_total_data(total_data)

init_total_data()

# 記帳專用卡片模板
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
    user_id = event.source.user_id
    group_id = event.source.group_id if hasattr(event.source, "group_id") else "private"
    msg = event.message.text.strip()
    g_data = get_group_data(group_id)
    admin_uid_list = [adm["uid"] for adm in g_data["admins"]]

    # 所有人通用：查詢自己USER ID
    if msg == "/ID":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"你的LINE UserID：\n{user_id}"))
        return

    # ========== 非管理員直接攔截所有功能（加上 try-except 避免崩潰） ==========
    if user_id not in admin_uid_list:
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 您無使用權限，僅本群組管理員可操作"))
        except:
            pass
        return

    # ========== 以下全部為管理員專用功能 ==========
    # 設定群組資訊
    if msg.startswith("/設定群組資訊@"):
        parts = msg.split("@")
        if len(parts) == 3:
            g_data["group_name"] = parts[1]
            g_data["currency"] = parts[2]
            save_group_data(group_id, g_data)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 群組資訊設定完成\n群組名：{g_data['group_name']}\n幣別：{g_data['currency']}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 格式：/設定群組資訊@小金庫@台幣"))
        return

    # 清帳歸零
    if msg == "/清帳":
        g_data["total_money"] = 0
        g_data["last_money"] = 0
        g_data["record_list"].clear()
        save_group_data(group_id, g_data)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅【{g_data['group_name']}】所有帳目已清空歸零"))
        return

    # 撤回最後一筆記帳
    if msg == "/撤回":
        if not g_data["record_list"]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 暫無任何記錄可撤回"))
            return
        last_log = g_data["record_list"].pop()
        g_data["total_money"] -= last_log["money"]
        g_data["last_money"] = g_data["record_list"][-1]["money"] if g_data["record_list"] else 0
        save_group_data(group_id, g_data)

        if g_data["total_money"] > 0:
            tip = f"你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}"
        else:
            tip = f"{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"↩️ 撤回成功\n刪除項目：{last_log['money']}（{last_log['note']}）\n{tip}"))
        return

    # 查帳卡片
    if msg == "/查帳":
        if g_data["total_money"] > 0:
            status_str = f"你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}"
        else:
            status_str = f"{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"

        card = build_account_card(
            title=f"【{g_data['group_name']}】帳務查詢",
            last_amount=g_data["last_money"],
            current_amount=0,
            status_text=status_str,
            note="無",
            currency=g_data["currency"]
        )
        line_bot_api.reply_message(event.reply_token, card)
        return

    # 收支記帳 +金額 -金額 支援備註
    split_msg = msg.split(" ", 1)
    num_str = split_msg[0]
    if (num_str.startswith("+") or num_str.startswith("-")) and num_str[1:].isdigit():
        money = int(num_str)
        remark = split_msg[1] if len(split_msg) >= 2 else "無備註"
        old_last = g_data["last_money"]

        g_data["last_money"] = money
        g_data["total_money"] += money
        g_data["record_list"].append({"money": money, "note": remark})
        save_group_data(group_id, g_data)

        if g_data["total_money"] > 0:
            res_status = f"目前你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}"
        else:
            res_status = f"目前{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"

        card = build_account_card(
            title="✅ 記帳成功",
            last_amount=old_last,
            current_amount=money,
            status_text=res_status,
            note=remark,
            currency=g_data["currency"]
        )
        line_bot_api.reply_message(event.reply_token, card)
        return

    # 管理員使用提示
    help_info = """📝 指令說明
/ID → 查詢自身LINE UserID
管理員專用：
+金額 備註 / -金額 備註
/查帳 /清帳 /撤回
/設定群組資訊@名稱@幣別
新增管理員：/設定密碼@新增管理員@名稱@userid"""
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_info))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
