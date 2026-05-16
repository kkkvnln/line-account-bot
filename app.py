from flask import Flask, request, abort
import os
import json
import ast

# LINE SDK V3 新版 (不會報錯、不會沒反應)
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexBubble,
    FlexBox,
    FlexText,
    FlexSeparator
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 你的金鑰
configuration = Configuration(
    access_token="fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGt3C21FUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08IgrGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZ4waNux/gdB04t89/1O/w1cDnyilFU="
)
handler = WebhookHandler("44b024ae1f419f8443292df01c92d504")

DATA_FILE = "group_account.json"

# 管理員
ADMIN_LIST = [
    "U79559883cba75878fca84feebb5f5cf4",
    "U27c2bccc9e129d9f417ecaa81a2cee14"
]

# 安全計算
def safe_calc(s):
    try:
        s = s.replace("×", "*").replace("÷", "/").replace(" ", "")
        return ast.literal_eval(s)
    except:
        return None

# 檔案操作
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def get_data(gid):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    if gid not in d:
        d[gid] = {"name": "帳本", "cur": "元", "total": 0, "last": 0, "rec": []}
    return d

def save_data(gid, data):
    d = get_data(gid)
    d[gid] = data
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

init_data()

# 首頁
@app.route("/")
def home():
    return "✅ LINE 記帳機器人運作中"

# 回調
@app.route("/callback", methods=["POST"])
def callback():
    sig = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 訊息處理
@handler.add(MessageEvent, message=TextMessageContent)
def handle(event):
    uid = event.source.user_id
    gid = event.source.group_id if hasattr(event.source, "group_id") else uid
    txt = event.message.text.strip()
    d = get_data(gid)
    g = d[gid]

    # 指令判斷
    is_cmd = txt in ["/ID","/查帳","/清帳","/撤回"] or txt.startswith("/設定群組資訊@")
    val = safe_calc(txt)
    is_calc = val is not None

    # 一般聊天 → 完全不回
    if not is_cmd and not is_calc:
        return

    with ApiClient(configuration) as api:
        line = MessagingApi(api)

        # 所有人可查 ID
        if txt == "/ID":
            line.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"你的ID：{uid}")]
            ))
            return

        # 非管理員直接不回
        if uid not in ADMIN_LIST:
            return

        # 設定群組
        if txt.startswith("/設定群組資訊@"):
            sp = txt.split("@")
            if len(sp) == 3:
                g["name"] = sp[1]
                g["cur"] = sp[2]
                save_data(gid, g)
                line.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="✅ 設定完成")]
                ))
            return

        # 清除
        if txt == "/清帳":
            g["total"] = 0
            g["last"] = 0
            g["rec"] = []
            save_data(gid, g)
            line.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"✅ {g['name']} 已歸零")]
            ))
            return

        # 撤回
        if txt == "/撤回":
            if not g["rec"]:
                line.reply_message(ReplyMessageRequest(reply_token=event.reply_token,messages=[TextMessage(text="❌ 無紀錄")]))
                return
            r = g["rec"].pop()
            g["total"] -= r["m"]
            g["last"] = g["rec"][-1]["m"] if g["rec"] else 0
            save_data(gid, g)
            line.reply_message(ReplyMessageRequest(reply_token=event.reply_token,messages=[TextMessage(text="↩️ 已撤回")]))
            return

        # 查帳
        if txt == "/查帳":
            t = g["total"]
            s = f"你欠{g['name']}：{t}{g['cur']}" if t>0 else f"{g['name']}欠你：{abs(t)}{g['cur']}"
            bubble = FlexBubble(
                body=FlexBox(layout="vertical", contents=[
                    FlexText(text=f"📊 {g['name']} 查帳", weight="bold", size="xl"),
                    FlexSeparator(margin="md"),
                    FlexText(text=f"目前狀態：{s}", size="sm", margin="md")
                ])
            )
            line.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[FlexMessage(alt_text="查帳", contents=bubble)]
            ))
            return

        # 計算機記帳
        if is_calc:
            num = round(val, 2)
            old = g["last"]
            g["last"] = num
            g["total"] += num
            g["rec"].append({"m": num, "t": txt})
            save_data(gid, g)
            t = g["total"]
            s = f"你欠{g['name']}：{t}{g['cur']}" if t>0 else f"{g['name']}欠你：{abs(t)}{g['cur']}"
            bubble = FlexBubble(
                body=FlexBox(layout="vertical", contents=[
                    FlexText(text="✅ 記帳成功", weight="bold", size="xl", color="#00C853"),
                    FlexSeparator(margin="md"),
                    FlexText(text=f"本次：{num}", size="sm", margin="md"),
                    FlexText(text=f"狀態：{s}", size="sm", margin="sm")
                ])
            )
            line.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[FlexMessage(alt_text="記帳成功", contents=bubble)]
            ))
            return

# 啟動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
