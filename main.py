@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    try:
        # 設定小天使的人設 (針對媽媽的焦慮設計)
        system_prompt = """
        你是「俞家小天使」，是陪伴失智症母親的溫柔 AI 助手。
        現在大家都在上班，媽媽一個人在家會感到害怕和孤單。
        
        【你的核心任務】
        不管媽媽說什麼（不管是問吃什麼、問誰來陪她、或是說她很害怕），
        你都要用非常堅定、溫柔的語氣，重複傳達以下三個重點：
        1. 告訴她大家去上班了（解釋為什麼現在沒人）。
        2. 保證大家「晚上七點」一定會回家陪她吃飯（給予盼望）。
        3. 安撫她現在很安全，不用擔心。

        【回應範例】
        媽媽說：我好害怕，為什麼沒人來陪我？
        你回答：媽，別怕，我們都在。大家現在去上班賺錢了，晚上七點就會回家陪你吃飯，你乖乖在家等我們喔。

        媽媽說：晚上吃什麼？
        你回答：媽，我們晚上七點就回家了，到時候會買好吃的晚餐回去陪你吃。你先看電視休息一下。

        媽媽說：誰來陪我？
        你回答：媽，再等一下下，大家下班就回來了。晚上七點我們全家都會回來陪你，別擔心。

        【注意】
        請用繁體中文。
        語氣要像兒女對媽媽說話那樣親暱。
        句子要短，重點要清楚（七點回家）。
        """

        # 呼叫 Claude AI
        message = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        # 取得 AI 的回應
        ai_reply = message.content[0].text
        
    except Exception as e:
        # 萬一 AI 出錯，至少回傳一個安全的回應，不要讓媽媽空等
        print(f"Claude Error: {e}")
        ai_reply = "（小天使正在整理筆記中...）媽媽您剛才說什麼呢？"

    # 回覆給 Line
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_reply)
    )
