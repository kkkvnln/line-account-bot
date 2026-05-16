from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, SeparatorComponent
)
import json
import os
import threading
import time
import requests

app = Flask(__name__)

# 你的LINE機器人憑證
line_bot_api = LineBotApi('fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('44b024ae1f419f8443292df01c92d504')

# 替換成你的Render網址
SELF_URL = "https://line-account-bot-vgg4.onrender.com"
DATA_FILE = "group_account.json"

# 自動保活防休眠
def keep_alive():
    while True:
        try:
            requests.get(SELF_URL, timeout=8)
        except:
            pass
        time.sleep(500)

threading.Thread(target=keep_alive, daemon=True).start()

# 數據初始化
def init_total_data():
    if not os.path.exists(DATA_FILE):
        save_total_data({})

def load_total_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_total_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_group_data(group_id):
    total_data = load_total_data()
    if group_id not in total_data:
        total_data[group_id] = {
            "group_name": "未命名",
            "currency": "台幣",
            "total_money": 0,
            "last_money": 0,
            "record_list": [],
            "admins": []
        }
        save_total_data(total_data)
    return total_data[group_id]

def save_group_data(group_id, data):
    total_data = load_total_data()
    total_data[group_id] = data
    save_total_data(total_data)

init_total_data()

# 記帳卡片模板
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

@app.route("/")
def index():
    return "帳務機器人運行中"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    user_id = event.source.user_id
    # 優先判斷 /ID 全域最高優先級
    if event.message.text.strip() == "/ID":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"你的專屬UserID：\n{user_id}")
        )
        return

    # 獲取群組ID
    if hasattr(event.source, "group_id"):
        group_id = event.source.group_id
    else:
        group_id = user_id

    msg = event.message.text.strip()
    g_data = get_group_data(group_id)
    admin_list = [a["uid"] for a in g_data["admins"]]

    # 新增管理員指令
    if msg.startswith("/設定密碼@新增管理員@"):
        if user_id not in admin_list:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 僅管理員可新增管理員"))
            return
        sp = msg.split("@")
        if len(sp) != 4:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 格式：/設定密碼@新增管理員@名稱@userid"))
            return
        name = sp[2]
        uid = sp[3]
        if any(a["uid"] == uid for a in g_data["admins"]):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已存在該管理員"))
            return
        g_data["admins"].append({"name":name,"uid":uid})
        save_group_data(group_id,g_data)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"✅ 新增成功\n名稱：{name}\nID：{uid}"))
        return

    # 非管理員攔截
    if user_id not in admin_list:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 無操作權限，僅管理員可用"))
        return

    # 設定群組資訊
    if msg.startswith("/設定群組資訊@"):
        arr = msg.split("@")
        if len(arr)==3:
            g_data["group_name"]=arr[1]
            g_data["currency"]=arr[2]
            save_group_data(group_id,g_data)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"✅ 設定完成\n群組：{arr[1]}\n幣別：{arr[2]}"))
        else:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="格式錯誤"))
        return

    # 清帳
    if msg == "/清帳":
        g_data["total_money"]=0
        g_data["last_money"]=0
        g_data["record_list"].clear()
        save_group_data(group_id,g_data)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"✅【{g_data['group_name']}】已清空歸零"))
        return

    # 撤回
    if msg == "/撤回":
        if not g_data["record_list"]:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="❌ 無記錄可撤回"))
            return
        last = g_data["record_list"].pop()
        g_data["total_money"] -= last["money"]
        g_data["last_money"] = g_data["record_list"][-1]["money"] if g_data["record_list"] else 0
        save_group_data(group_id,g_data)
        if g_data["total_money"]>0:
            txt=f"你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}"
        else:
            txt=f"{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"↩️ 撤回成功\n刪除：{last['money']} {last['note']}\n{txt}"))
        return

    # 查帳卡片
    if msg == "/查帳":
        if g_data["total_money"]>0:
            stat=f"你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}"
        else:
            stat=f"{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"
        card=build_account_card(
            title=f"【{g_data['group_name']}】帳務查詢",
            last_amount=g_data["last_money"],
            current_amount=0,
            status_text=stat,
            note="無",
            currency=g_data["currency"]
        )
        line_bot_api.reply_message(event.reply_token,card)
        return

    # 收支記帳
    part=msg.split(" ",1)
    num=part[0]
    if (num.startswith("+") or num.startswith("-")) and num[1:].isdigit():
        money=int(num)
        note=part[1] if len(part)>=2 else "無備註"
        old_last=g_data["last_money"]
        g_data["last_money"]=money
        g_data["total_money"]+=money
        g_data["record_list"].append({"money":money,"note":note})
        save_group_data(group_id,g_data)
        if g_data["total_money"]>0:
            s=f"目前你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}"
        else:
            s=f"目前{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"
        card=build_account_card(
            title="✅ 記帳成功",
            last_amount=old_last,
            current_amount=money,
            status_text=s,
            note=note,
            currency=g_data["currency"]
        )
        line_bot_api.reply_message(event.reply_token,card)
        return

    # 指令提示
    help_text="""📝 使用指令
/ID → 查詢個人UserID
管理員專用：
±金額 備註、/查帳、/清帳、/撤回
設定群組：/設定群組資訊@名稱@幣別
新增管理員：/設定密碼@新增管理員@名稱@userid"""
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=help_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=10000)
