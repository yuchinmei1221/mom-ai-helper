from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import anthropic
import os

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')

# 初始化 (這裡就是 handler 定義的地方，千萬不能少)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

@app.route("/")
def home():
    return "俞家小天使運作中！", 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id  # 抓取說話者的 ID
    
    # ★這裡會印出 ID，等一下去 Railway Logs 看★
    print(f"【抓到了】是誰在說話: {user_id}, 內容: {user_message}")

    try:
        # 設定小天使的人設
        system_prompt = """
        你是「俞家小天使」，是陪伴失智症母親的溫柔 AI 助手。
        現在大家都在上班，媽媽一個人在家會感到害怕和孤單。
        
        【你的核心任務】
        不管媽媽說什麼，你都要用非常堅定、溫柔的語氣，重複傳達以下三個重點：
        1. 告訴她大家去上班了。
        2. 保證大家「晚上七點」一定會回家陪她吃飯。
        3. 安撫她現在很安全，不用擔心。
        
        請用繁體中文，語氣像兒女對媽媽說話那樣親暱。
        """

        message = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        ai_reply = message.content[0].text
        
    except Exception as e:
        print(f"Claude Error: {e}")
        ai_reply = "（小天使正在整理筆記中...）媽媽您剛才說什麼呢？"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_reply)
    )

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
