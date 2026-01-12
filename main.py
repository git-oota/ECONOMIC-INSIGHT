import os
import json
import re
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
    必ず以下のJSON形式で出力してください。他の説明文やMarkdownの枠(```json)は一切不要です。

    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "English Title" }},
      "contents": {{ "ja": "本文(改行は\\n)", "en": "English content" }},
      "mermaid": {{ "ja": "graph TD;A-->B", "en": "graph TD;A-->B" }},
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
            model='gemini-3-flash-preview', # 最新の安定モデル
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.1
            )
        )
        
        data = json.loads(response.text)
        return data

    except Exception as e:
        print(f"Error: {e}")
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "生成エラー", "en": "Generation Error"},
            "contents": {"ja": f"エラー: {str(e)}", "en": f"Error: {str(e)}"},
            "mermaid": {"ja": "graph TD;Error", "en": "graph TD;Error"},
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
            except:
                history = []
    
    history.insert(0, new_article)
    
    os.makedirs('docs', exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    print(f"✅ Success: {new_article['titles']['ja']}")

if __name__ == "__main__":
    main()
