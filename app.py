from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os

app = Flask(__name__)

# 你的 LINE Bot 憑證
CHANNEL_ACCESS_TOKEN = "fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGtFUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZwaNux/gdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "44b024ae1f419f8443292df01c92d504"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

DATA_FILE = "data.json"

# 初始化
def init():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)

init()

# 伺服器測試
@app.route("/")
def index():
    return "Bot is running!"

# 回覆 LINE
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle(event):
    try:
        text = event.message.text.strip()
        reply_token = event.reply_token

        # 取得 ID
        if hasattr(event.source, "group_id"):
            gid = event.source.group_id
        else:
            gid = event.source.user_id

        # 讀資料
        all_data = load()
        if gid not in all_data:
            all_data[gid] = {"total": 0, "records": []}
        
        data = all_data[gid]

        # ========== 指令 ==========
        if text == "/測試":
            line_bot_api.reply_message(reply_token, TextSendMessage(text="✅ 機器人正常運作！"))
            return

        if text == "/清帳":
            data["total"] = 0
            data["records"] = []
            all_data[gid] = data
            save(all_data)
            line_bot_api.reply_message(reply_token, TextSendMessage(text="✅ 已清帳！"))
            return

        if text == "/撤回":
            if not data["records"]:
                line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ 無紀錄"))
                return
            num = data["records"].pop()
            data["total"] -= num
            all_data[gid] = data
            save(all_data)
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"↩️ 撤回成功：{num}\n目前：{data['total']}"))
            return

        if text == "/查帳":
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"📊 目前總額：{data['total']}"))
            return

        # 記帳 +100 -50
        if text.startswith("+") or text.startswith("-"):
            num = float(eval(text))
            data["total"] += num
            data["records"].append(num)
            all_data[gid] = data
            save(all_data)
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ 記帳：{num}\n目前：{data['total']}"))
            return

        # 預設回覆
        line_bot_api.reply_message(reply_token, TextSendMessage(text="📝 指令：/測試 /查帳 /清帳 /撤回 +100 -50"))

    except Exception as e:
        print("錯誤：", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
