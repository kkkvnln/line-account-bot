@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    try:
        msg = event.message.text
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"收到：{msg}"))
    except:
        pass
