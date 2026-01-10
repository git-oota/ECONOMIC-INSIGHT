import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai

JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    # プロンプトでJSONのキー名を強調し、構造を強制します
    prompt = f"""
    【最優先指示】
    1. Google検索を使用し、今日（{TODAY}）の日本の主要な経済ニュースを1つ選定してください。
    2. 以下のJSON構造のみを出力してください。挨拶や説明文は一切不要です。

    ## 出力JSON形式
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "日本語タイトル", "en": "English Title" }},
      "contents": {{ "ja": "日本語本文(1000文字程度、改行は\\n)", "en": "English Content" }},
      "mermaid": {{ "ja": "graph TD;...", "en": "graph TD;..." }},
      "glossary": [
        {{ "term": {{ "ja": "用語名", "en": "Term" }}, "def": {{ "ja": "解説", "en": "Definition" }} }}
      ]
    }}

    ## 執筆ルール
    - 主語は「私達」とする。
    - 「：」（コロン）の使用は厳禁。
    - 中学生にもわかる用語解説を3個含める。
    """

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=prompt,
            config={
                'tools': [{'google_search': {}}],
                'temperature': 0.1
            }
        )
        
        # デバッグ用：APIの生の応答をログに出力（Actionsのログで確認可能）
        print("--- Raw API Response ---")
        print(response.text)
        print("------------------------")

        # JSONの抽出ロジックを強化
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if not match:
            raise ValueError("JSON形式のデータが見つかりませんでした。")
        
        res_text = match.group()
        data = json.loads(res_text)

        # 必須キーの存在チェック
        required_keys = ['titles', 'contents', 'mermaid', 'glossary']
        for key in required_keys:
            if key not in data:
                raise KeyError(f"JSONに必須キー '{key}' が不足しています。")
        
        return data

    except Exception as e:
        print(f"解析エラーの詳細: {e}")
        raise e

def main():
    data_path = 'docs/data.json'
    try:
        data = generate_content()
        # リセット上書き
        history = [data]
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
                
        print(f"Success: {data['titles']['ja']}")
    except Exception as e:
        print(f"Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
