from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, TextMessage, ReplyMessageRequest, PushMessageRequest
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from api.chatgpt import ChatGPT

import os
import dotenv
import threading

dotenv.load_dotenv()

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default="true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()

@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        line_handler.handle(body, signature)
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        abort(400)
    return 'OK'

def push_ai_reply(user_id, user_message):
    chatgpt.add_msg(f"HUMAN:{user_message}?\n")
    reply_msg = chatgpt.get_response().replace("AI:", "", 1)
    chatgpt.add_msg(f"AI:{reply_msg}\n")
    if not reply_msg or not reply_msg.strip():
        reply_msg = "AI 沒有回應內容，請稍後再試。"
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=reply_msg)]
            )
        )

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    global working_status
    user_message = event.message.text
    user_id = event.source.user_id
    if user_message == "說話":
        working_status = True
        reply = "我可以說話囉，歡迎來跟我互動 ^_^ "
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )
    elif user_message == "閉嘴":
        working_status = False
        reply = "好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )
    elif working_status:
        # 立即回覆「AI正在思考中...」
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="AI正在思考中，請稍候...")]
                )
            )
        # 背景推送 AI 回覆
        threading.Thread(target=push_ai_reply, args=(user_id, user_message)).start()
    else:
        return

if __name__ == "__main__":
    app.run(threaded=True)