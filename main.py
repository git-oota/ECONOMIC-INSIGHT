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
# タイムアウトをここではなく、個別のリクエスト時に設定します
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    prompt = f"""
    【最優先指示：事実性の徹底と検索プロセス】
    1. Google検索を使用し、今日（{TODAY}）の日本経済新聞、ロイター、ブルームバーグから主要な経済ニュースを1つ選定してください。
    2. 複数のメディアで報じられている事実のみを扱い、数値の捏造は厳禁です。

    【執筆ルール】
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
          "term": {{ "ja": "用語名", "en": "Term" }}, 
          "def": {{ "ja": "解説", "en": "Definition" }} 
        }}
      ]
    }}
    """
    
    try:
        # 1sエラーを回避するため、リクエスト時にhttp_optionsを指定
        # モデル名も安定版の 'gemini-2.0-flash' に固定します
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                temperature=0.1,
                http_options={'timeout': 600} # ここで10分(600s)を確実に確保
            )
        )
        
        # レスポンスからJSONを抽出
        res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(res_text)

    except Exception as e:
        print(f"APIエラー: {e}")
        raise e

def main():
    try:
        data = generate_content()
        data_path = 'docs/data.json'
        
        # 「既存の記事を消して再作成」するため、履歴を読み込まず新規リストを作成
        # ※蓄積したい場合は、一度実行した後にこの部分を「読み込み式」に戻します
        history = [data] 
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
                
        print(f"Success: {data['titles']['ja']} を新規作成しました。")
    except Exception as e:
        print(f"実行失敗: {e}")
        exit(1)

if __name__ == "__main__":
    main()
