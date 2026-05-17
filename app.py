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
CHANNEL_ACCESS_TOKEN = "fgLUgkUwXjFD+W4Rw0N4isKahmyfq4iw/6uU4TGoKW+t0TDSiGtFUALuIsB8RrGN6kvoWhgPbxXYw/TpNdV08I5grGmY7mzpeZKITRM/agQmoeXQZtUJSsA8oczCseKWVOewDu9DEZwaNux/gdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "44b024ae1f419f8443292df01c92d504"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

DATA_FILE = "group_account.json"

# 初始化檔案
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 獲取群組資料
def get_group_info(gid):
    all_data = load_data()
    if gid not in all_data:
        all_data[gid] = {
            "name": "預設群組",
            "currency": "台幣",
            "total": 0.0,
            "last_num": 0.0,
            "records": []
        }
        save_data(all_data)
    return all_data[gid]

init_data()

# 建立彈窗卡片
def make_card(title, last_val, now_val, tip, note, currency):
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text=title, size="xl", weight="bold", color="#22c55e"),
                SeparatorComponent(margin="md"),
                BoxComponent(layout="horizontal", contents=[
                    TextComponent(text="上次金額", color="#666"),
                    TextComponent(text=f"{last_val} {currency}", align="end", color="#d2691e")
                ]),
                BoxComponent(layout="horizontal", margin="md", contents=[
                    TextComponent(text="本次金額", color="#666"),
                    TextComponent(text=f"{now_val} {currency}", align="end", color="#d2691e")
                ]),
                SeparatorComponent(margin="md"),
                BoxComponent(layout="horizontal", contents=[
                    TextComponent(text="目前狀態", color="#666"),
                    TextComponent(text=tip.split("：")[-1], align="end", color="#d2691e")
                ]),
                SeparatorComponent(margin="md"),
                BoxComponent(layout="horizontal", contents=[
                    TextComponent(text="備註", color="#666"),
                    TextComponent(text=note, align="end", color="#888")
                ])
            ]
        )
    )
    return FlexSendMessage(alt_text=title, contents=bubble)

# 網址接口
@app.route("/callback", methods=["POST"])
def callback():
    sig = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 訊息監聽
@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    msg = event.message.text.strip()
    reply_token = event.reply_token

    # 判斷群組/個人ID
    if hasattr(event.source, "group_id"):
        talk_id = event.source.group_id
    else:
        talk_id = event.source.user_id

    user_id = event.source.user_id
    group_data = get_group_info(talk_id)
    g_name = group_data["name"]
    g_currency = group_data["currency"]

    # ==============================
    # 指令：設定群組資訊
    # ==============================
    if msg.startswith("/設定群組資訊@"):
        sp = msg.split("@")
        if len(sp) == 3:
            all_d = load_data()
            all_d[talk_id]["name"] = sp[1]
            all_d[talk_id]["currency"] = sp[2]
            save_data(all_d)
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅設定完成\n群組名：{sp[1]}\n幣別：{sp[2]}"))
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="❌格式：/設定群組資訊@名稱@幣別"))
        return

    # ==============================
    # 指令：清帳
    # ==============================
    if msg == "/清帳":
        all_d = load_data()
        all_d[talk_id]["total"] = 0.0
        all_d[talk_id]["last_num"] = 0.0
        all_d[talk_id]["records"] = []
        save_data(all_d)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅【{g_name}】帳務已全部歸零"))
        return

    # ==============================
    # 指令：撤回
    # ==============================
    if msg == "/撤回":
        if not group_data["records"]:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="❌暫無記錄可撤回"))
            return

        last_rec = group_data["records"].pop()
        all_d = load_data()
        all_d[talk_id]["total"] -= last_rec["num"]
        all_d[talk_id]["last_num"] = all_d[talk_id]["records"][-1]["num"] if all_d[talk_id]["records"] else 0.0
        save_data(all_d)

        now_total = all_d[talk_id]["total"]
        if now_total > 0:
            status = f"目前欠{g_name}：{now_total} {g_currency}"
        else:
            status = f"目前{g_name}欠：{abs(now_total)} {g_currency}"

        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"↩️撤回成功\n刪除金額：{last_rec['num']}\n{status}"))
        return

    # ==============================
    # 指令：查帳
    # ==============================
    if msg == "/查帳":
        total_money = group_data["total"]
        if total_money > 0:
            s_txt = f"目前欠{g_name}：{total_money} {g_currency}"
        else:
            s_txt = f"目前{g_name}欠：{abs(total_money)} {g_currency}"

        card = make_card(f"【{g_name}】帳務查詢", group_data["last_num"], 0, s_txt, "無", g_currency)
        line_bot_api.reply_message(reply_token, card)
        return

    # ==============================
    # 記帳 + 運算
    # ==============================
    split_msg = msg.split(" ", 1)
    calc_str = split_msg[0]
    note_text = split_msg[1].strip() if len(split_msg) > 1 else "無"

    if re.match(r"^[+-][\d+\-*/.]+$", calc_str):
        try:
            cal_num = round(eval(calc_str), 2)
            all_d = load_data()
            old_last = all_d[talk_id]["last_num"]

            all_d[talk_id]["last_num"] = cal_num
            all_d[talk_id]["total"] += cal_num
            all_d[talk_id]["records"].append({"num": cal_num, "note": note_text})
            save_data(all_d)

            new_total = all_d[talk_id]["total"]
            if new_total > 0:
                state = f"目前欠{g_name}：{new_total} {g_currency}"
            else:
                state = f"目前{g_name}欠：{abs(new_total)} {g_currency}"

            send_card = make_card("✅記帳成功", old_last, cal_num, state, note_text, g_currency)
            line_bot_api.reply_message(reply_token, send_card)
            return
        except:
            pass

    # ==============================
    # 預設：說明
    # ==============================
    help_info = """📝可用指令
/查詢ID
/設定群組資訊@名稱@幣別
+金額  -金額
支援+ - * /
/查帳  /撤回  /清帳"""
    line_bot_api.reply_message(reply_token, TextSendMessage(text=help_info))
