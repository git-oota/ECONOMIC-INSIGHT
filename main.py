import os
import json
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. 環境設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析を開始...")
    
    prompt = f"""
    今日（{TODAY}）の日本の主要経済ニュースを1つ選び、中学生向け解説コラムを書いてください。
    必ず以下のJSON形式のみで出力してください。

    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ "ja": "本文", "en": "Content" }},
      "mermaid": {{ "ja": "graph TD\\nA-->B", "en": "graph TD\\nA-->B" }},
      "glossary": [
        {{
          "term": {{ "ja": "用語", "en": "Term" }},
          "def": {{ "ja": "解説", "en": "Definition" }}
        }}
      ]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"API Error: {e}")
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "分析エラー", "en": "Error"},
            "contents": {"ja": "現在データを生成できません。", "en": "Error."},
            "mermaid": {"ja": "graph TD\nError", "en": "graph TD\nError"},
            "glossary": []
        }

def main():
    data_path = 'docs/data.json'
    new_article = generate_content()
    
    # 既存データの読み込み
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list): history = []
            except:
                history = []
    
    # 新しい記事を追加して保存（最大50件）
    history.insert(0, new_article)
    os.makedirs('docs', exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    print(f"✅ Success: {new_article.get('titles', {}).get('ja', 'No Title')}")

if __name__ == "__main__":
    main()
