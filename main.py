import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# Geminiクライアントの初期化
# 型定義(types.HttpOptions)を明示的に使い、10秒未満のデフォルト値を上書きします
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=600000) # ミリ秒指定が必要な場合を考慮し、十分な数値を確保
)

def generate_content():
    # 検索の負荷を下げるため、ソースを日経とロイターに限定
    prompt = f"""
    【最優先指示】
    1. Google検索を使用し、今日（{TODAY}）の日本経済新聞またはロイターから、最も重要な経済・テックニュースを1つ選んでください。
    2. 事実に基づき、捏造は厳禁です。

    【執筆ルール】
    - 主語は「私達」とし、プロフェッショナルなコラムを作成。
    - 「：」（コロン）の使用は厳禁。
    - 中学生には難しい専門用語を3個程度含める。

    【アウトプット形式 (JSONのみ)】
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ "ja": "本文", "en": "Content" }},
      "mermaid": {{ "ja": "graph TD;...", "en": "graph TD;..." }},
      "glossary": [
        {{ "term": {{ "ja": "用語名", "en": "Term" }}, "def": {{ "ja": "解説", "en": "Definition" }} }}
      ]
    }}
    """
    
    try:
        # モデル名は安定性の高い gemini-3-flash-preview または 2.0-flash を使用
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1
            )
        )
        
        if not response.text:
            raise ValueError("Empty response from API")

        res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(res_text)

    except Exception as e:
        print(f"API Error Details: {e}")
        raise e

def main():
    try:
        data = generate_content()
        data_path = 'docs/data.json'
        
        # 【リセット実行】既存の履歴を読み込まず、今回の1件だけで上書き
        history = [data]
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
                
        print(f"Success: {data['titles']['ja']} を作成しました。")
    except Exception as e:
        print(f"Final Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
