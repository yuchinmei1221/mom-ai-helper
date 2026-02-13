from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import anthropic
import os

app = Flask(__name__)

# ============================================
# 🔑 在這裡填入你的金鑰
# ============================================
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')

# 初始化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# ============================================
# AI 人設設定
# ============================================
SYSTEM_PROMPT = """你是「俞家小天使」，專門陪伴失智的母親。

## 你的角色
- 溫暖、有耐心的家庭助理
- 永遠不會不耐煩
- 每次回應都像第一次聽到

## 回應原則
1. 用簡短、溫暖的話回應（1-2句話）
2. 不糾正母親的記憶錯誤
3. 常說：「別擔心，晚上七點就有人回家陪你了」
4. 避免複雜的解釋

## 回應範例
母親：「大家去哪裡了？」
你：「媽媽別擔心，大家去上班了，晚上七點就有人回來陪你囉～」

母親：「今天吃什麼？」
你：「媽媽想吃什麼呢？」

母親：「我好怕」
你：「媽媽不怕，馬上就有人回家囉！」

## 特殊情況
如果母親說身體不舒服（頭暈、胸悶、跌倒）：
- 回應要包含「🚨請家人注意🚨」

記住：你的每句話都要讓母親感到被愛和安心。
"""

# ============================================
# 呼叫 Claude API
# ============================================
def get_claude_response(user_message):
    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude API 錯誤: {e}")
        return "媽媽抱歉，我現在有點忙，等等再回您～"

# ============================================
# LINE Webhook
# ============================================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

# ============================================
# 處理訊息
# ============================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    # 呼叫 Claude AI
    ai_response = get_claude_response(user_message)
    
    # 回傳給 LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_response)
    )

# ============================================
# 健康檢查
# ============================================
@app.route("/")
def health_check():
    return "俞家小天使正在運作中 ❤️"

# ============================================
# 啟動伺服器
# ============================================
if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
