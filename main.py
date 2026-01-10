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
# タイムアウト設定をクライアントレベルに移動し、確実に600秒（10分）を確保します
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options={'timeout': 600}
)

def generate_content():
    # 検索範囲を具体的に絞り、AIの処理負荷を下げてレスポンスを速めます
    prompt = f"""
    【最優先指示：事実性の徹底と検索プロセス】
    1. Google検索を使用し、今日（{TODAY}）の日本経済新聞、ロイター、ブルームバーグの主要ニュースから「経済・テクノロジー」のトピックを1つ選定してください。
    2. 複数のメディアで報じられている事実のみを扱い、数値の捏造は厳禁です。

    【執筆ルール：独自性と自然な文章】
    - 主語は「私達」とし、プロフェッショナルな経済分析コラムを作成してください。
    - 「：」（コロン）の使用は厳禁です。
    - 中学生には難しい専門用語を3〜5個含めてください。

    【アウトプット形式 (JSONのみ)】
    以下の構造のJSONのみを出力してください。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ "ja": "本文（1000文字程度）", "en": "Content" }},
      "mermaid": {{ "ja": "graph TD;...", "en": "graph TD;..." }},
      "glossary": [
        {{ 
          "term": {{ "ja": "本文中の用語", "en": "Term" }}, 
          "def": {{ "ja": "中学生向け解説（30文字）", "en": "Definition" }} 
        }}
      ]
    }}
    ※重要：glossaryの"term"は、本文(contents)の中の表記と完全一致させてください。
    """
    
    try:
        # モデル名は安定している 'gemini-3-flash-preview' を使用
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                temperature=0.1
            )
        )
        
        # JSON部分を抽出
        res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(res_text)

    except Exception as e:
        print(f"APIエラーまたはタイムアウトが発生しました: {e}")
        raise e

def main():
    try:
        data = generate_content()
        data_path = 'docs/data.json'
        
        history = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # 最新記事を先頭に追加
        history.insert(0, data)
        os.makedirs('docs', exist_ok=True)
        
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
                
        print(f"Success: {data['titles']['ja']}")
    except Exception as e:
        print(f"実行に失敗しました: {e}")
        exit(1)

if __name__ == "__main__":
    main()
