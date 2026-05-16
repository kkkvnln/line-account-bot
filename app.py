from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os
import ast

app = Flask(__name__)

# 填入你自己的
CHANNEL_ACCESS_TOKEN = "fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "44b024ae1f419f8443292df01c92d504"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
DATA_FILE = "group_account.json"

def default_group_data():
    return {
        "my_name": "虎爺",
        "currency": "台幣",
        "balance": 0,
        "history": []
    }

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(all_data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

all_group_data = load_data()

def get_chat_id(event):
    if event.source.type == "group":
        return event.source.group_id
    elif event.source.type == "room":
        return event.source.room_id
    else:
        return event.source.user_id

def safe_eval(expr):
    try:
        allowed_ops = {ast.Add, ast.Sub, ast.Mult, ast.Div}
        allowed_unary = {ast.USub, ast.UAdd}
        tree = ast.parse(expr, mode="eval")
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and type(node.op) not in allowed_ops:
                return None
            if isinstance(node, ast.UnaryOp) and type(node.op) not in allowed_unary:
                return None
            if isinstance(node, (ast.Name, ast.Call)):
                return None
        return eval(expr, {"__builtins__": None})
    except:
        return None

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
def handle_msg(event):
    global all_group_data
    txt = event.message.text.strip()
    chat_id = get_chat_id(event)

    if chat_id not in all_group_data:
        all_group_data[chat_id] = default_group_data()
    g = all_group_data[chat_id]
    rep = ""

    if txt == "/清帳":
        g["balance"] = 0
        g["history"] = []
        save_data(all_group_data)
        rep = "✅ 已清帳！餘額已歸零"

    elif txt.startswith("/設定群組資訊@"):
        parts = txt.split("@")
        if len(parts) == 3:
            g["my_name"] = parts[1].strip()
            g["currency"] = parts[2].strip()
            save_data(all_group_data)
            rep = f"✅ 設定完成\n名稱：{g['my_name']}\n幣別：{g['currency']}"
        else:
            rep = "❌ 格式：/設定群組資訊@名字@幣別"

    elif any(op in txt for op in ["+", "-", "*", "/"]) and not txt.startswith("/"):
        parts = txt.split(maxsplit=1)
        expr = parts[0]
        note = parts[1] if len(parts) > 1 else ""
        change = safe_eval(expr)
        if change is None:
            rep = "❌ 運算式錯誤"
        else:
            last_bal = g["balance"]
            new_bal = last_bal + change
            g["balance"] = new_bal
            g["history"].append({"last": last_bal, "change": change, "new": new_bal, "note": note})
            save_data(all_group_data)
            status_text = f"{g['my_name']}欠" if new_bal < 0 else f"{g['my_name']}餘額"
            rep = f"""計算結果
{expr}={change}

上次金額    {last_bal} {g['currency']}
本次金額    {change} {g['currency']}
目前{status_text}    {abs(new_bal)} {g['currency']}

備註    {note}
"""
    elif txt == "查帳":
        bal = g["balance"]
        status_text = f"{g['my_name']}欠" if bal < 0 else f"{g['my_name']}餘額"
        rep = f"目前{status_text}：{abs(bal)} {g['currency']}"

    else:
        rep = """📖 指令
/設定群組資訊@名字@幣別
/清帳
算式記帳：-20000*0.91 備註
查帳"""

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=rep))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)