from flask import Flask, request, abort
import os
import json
import ast

# 使用 LINE SDK V3 新版
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 你的 LINE Bot 憑證
LINE_ACCESS_TOKEN = "fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08IgrGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "44b024ae1f419f8443292df01c92d504"

configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

DATA_FILE = "group_account.json"
ADMIN_LIST = ["U79559883cba75878fca84feebb5f5cf4", "U27c2bccc9e129d9f417ecaa81a2cee14"]

# 初始化數據檔
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def get_group_data(gid):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    if gid not in d:
        d[gid] = {"group_name": "小金庫", "currency": "台幣", "total_money": 0, "last_money": 0, "record_list": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    return d[gid]

def save_group_data(gid, data):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    d[gid] = data
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

init_data()

# 健康檢查路由（Render 必須）
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is alive!"

# LINE Webhook 回調
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    group_id = event.source.group_id if hasattr(event.source, "group_id") else user_id
    msg = event.message.text.strip()

    # 所有人可使用的指令：/ID
    if msg.upper() == "/ID":
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"你的UserID：\n{user_id}")]
                )
            )
        return

    # 非管理員直接忽略
    if user_id not in ADMIN_LIST:
        return

    g_data = get_group_data(group_id)

    # 測試用指令，確認機器人正常回覆
    if msg == "/test":
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="✅ 機器人正常運作！")]
                )
            )
        return

    # 設定群組資訊
    if msg.startswith("/設定群組資訊@"):
        parts = msg.split("@")
        if len(parts) == 3:
            g_data["group_name"] = parts[1]
            g_data["currency"] = parts[2]
            save_group_data(group_id, g_data)
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=f"✅ 設定完成\n群組：{g_data['group_name']}\n幣別：{g_data['currency']}")]
                    )
                )
        return

    # 記帳指令（支援 ±金額 格式）
    parts = msg.split(" ", 1)
    if len(parts) > 0:
        money_str = parts[0]
        if (money_str.startswith("+") or money_str.startswith("-")) and money_str[1:].isdigit():
            amount = int(money_str)
            note = parts[1] if len(parts) >= 2 else "無備註"
            old_last = g_data["last_money"]
            g_data["last_money"] = amount
            g_data["total_money"] += amount
            g_data["record_list"].append({"money": amount, "note": note})
            save_group_data(group_id, g_data)

            status = f"目前你欠{g_data['group_name']}：{g_data['total_money']} {g_data['currency']}" if g_data["total_money"] > 0 else f"目前{g_data['group_name']}欠你：{abs(g_data['total_money'])} {g_data['currency']}"
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=f"✅ 記帳成功\n本次：{amount}\n備註：{note}\n{status}")]
                    )
                )
            return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
