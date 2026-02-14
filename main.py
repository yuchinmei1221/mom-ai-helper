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

# --- 初始化連線 (這部分千萬不能少) ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# --- 家庭成員 ID 對照表 (等抓到 ID 後再回來填) ---
FAMILY_MEMBERS = {
    'U1234567890abcdef1234567890abcdef': '媽媽',
    # '這裡放亂碼ID': '家人名字',
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
    
    # 在 Railway Logs 印出 ID，方便我們收集大家的「身分證」
    print(f"【抓到 ID】: {user_id} | 內容: {user_message}")

    # 查表看是誰在說話，沒查到就暫稱「家人」
    user_name = FAMILY_MEMBERS.get(user_id, "家人")

    try:
        # 設定給 Claude 的指令 (System Prompt)
        system_prompt = f"""
        你是俞家的專屬守護者。現在說話的人是：{user_name}。
        如果說話的是媽媽，請務必用最溫柔、有耐心的語氣安撫。
        請告訴她：「媽，別擔心，大家都在上班，晚上七點一定會準時回家陪妳吃飯喔！」
        請用繁體中文，句子簡短，語氣親切，不要自稱小天使，也不要說多餘的廢話。
        """

        # 呼叫 Claude API
        message = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        ai_reply = message.content[0].text
        
    except Exception as e:
        # 萬一 Claude API 失敗 (例如點數沒了或 Key 錯)，會跑這句自然的回答
        print(f"Claude Error: {e}")
        ai_reply = "媽，別擔心，我一直都在這呢。大家晚上七點就會回家陪妳喔！"

    # 回覆訊息給 LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_reply)
    )

if __name__ == "__main__":
    # 這裡依照 Railway 的 Port 8000 設定
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
