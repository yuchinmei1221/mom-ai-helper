from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import anthropic
import os

app = Flask(__name__)

# --- 環境變數讀取 ---
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')

# --- 初始化連線 ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# --- 家庭成員 ID 對照表 ---
FAMILY_MEMBERS = {
    'U426d0df0fbe7e6b187545a60c83eb947': '小梅',
    # 之後從 Logs 抓到其他家人的 ID 就加在這裡
    # 'U1234567890abcdef1234567890abcdef': '媽媽',
}

@app.route("/")
def home():
    return "俞家守護系統運作中", 200

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
    user_id = event.source.user_id
    
    print(f"【收到訊息】ID: {user_id} | 內容: {user_message}")
    
    user_name = FAMILY_MEMBERS.get(user_id, "家人")
    
    try:
        system_prompt = f"""
你是俞家的專屬守護者。現在說話的人是：{user_name}。

如果說話的是小梅或其他家人，請簡短回應，讓他們知道系統正常運作。

如果說話的是媽媽，請用溫柔、有耐心的語氣安撫她。
告訴她：「媽，別擔心，大家都在上班，晚上七點一定會準時回家陪妳吃飯喔！」

請用繁體中文，句子簡短親切，最多2-3句話，語氣像家人在說話，不要自稱守護者或小天使。
        """
        
        message = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        ai_reply = message.content[0].text
        print(f"✅ Claude 回應成功 ({user_name}): {ai_reply[:50]}...")
        
    except Exception as e:
        print(f"❌ Claude 錯誤: {type(e).__name__} - {str(e)}")
        ai_reply = "媽，別擔心，我一直都在這呢。大家晚上七點就會回家陪妳喔！"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_reply)
    )

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
