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

# クライアント初期化（タイムアウトをクライアントレベルで設定）
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options={'timeout': 600}
)

def generate_content():
    print(f"[{datetime.now()}] ニュース検索と記事生成を開始します...")
    
    prompt = f"""
    【最優先指示】
    1. Google検索を使用し、今日（{TODAY}）の日本経済新聞、ロイター、ブルームバーグから、最も重要な経済・テクノロジーニュースを1つ選定してください。
    2. 以下のJSON構造のみを出力してください。

    ## 出力JSON形式
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ "ja": "本文(改行は\\n)", "en": "Content" }},
      "mermaid": {{ "ja": "graph TD;...", "en": "graph TD;..." }},
      "glossary": [
        {{ "term": {{ "ja": "用語名", "en": "Term" }}, "def": {{ "ja": "解説", "en": "Definition" }} }}
      ]
    }}

    ## 執筆ルール
    - 主語は「私達」とし、プロフェッショナルなコラムを作成。
    - 「：」（コロン）の使用は一切厳禁。
    - 中学生にもわかる用語解説（glossary）を3〜5個含める。
    """

    try:
        # 1sエラー回避のため、1.5-flashを使用し、明示的にツールを設定
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                temperature=0.1
            )
        )
        
        # API応答のログ（Actionsで確認可能）
        print("--- API Response ---")
        print(response.text)
        print("--------------------")

        # JSON抽出
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if not match:
            raise ValueError("JSON形式のデータが見つかりませんでした。")
        
        data = json.loads(match.group())
        return data

    except Exception as e:
        print(f"生成エラー: {e}")
        raise e

def main():
    data_path = 'docs/data.json'
    try:
        new_article = generate_content()
        
        # 既存データの読み込み（アーカイブ化）
        history = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list): history = []
                except:
                    history = []
        
        # 先頭に追加して最大50件保持
        history.insert(0, new_article)
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
                
        print(f"Success: {new_article['titles']['ja']} を保存しました。")
    except Exception as e:
        print(f"Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
