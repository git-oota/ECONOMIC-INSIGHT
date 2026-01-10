import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types # タイムアウト設定に必要

# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# Geminiクライアントの初期化
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    prompt = f"""
    【最優先指示：事実性の徹底と検索プロセス】
    1. Google検索を使用し、今日（{TODAY}）または直近24時間以内に、日本経済新聞、朝日新聞、読売新聞、ロイター、ブルームバーグ等の信頼できるメディアが実際に報じた「経済・社会・テクノロジー」のニュースを複数検索してください。
    2. 検索されたニュースが「複数のメディアで共通して報じられている事実」であることを確認してください。
    3. 存在しない数値や未来予測を「既成事実」として扱うことは厳禁です。

    【執筆ルール：独自性と自然な文章】
    - 主語は「私達」とし、プロフェッショナルな経済分析コラムを作成してください。
    - 「：」（コロン）の使用を一切禁止します。
    - 中学生には難しい専門用語を本文中に含めてください。

    【アウトプット形式 (JSONのみ)】
    以下の構造のJSONのみを出力してください。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ "ja": "本文", "en": "Content" }},
      "mermaid": {{ "ja": "graph TD;...", "en": "graph TD;..." }},
      "glossary": [
        {{ 
          "term": {{ "ja": "本文中の用語", "en": "Term" }}, 
          "def": {{ "ja": "日本語解説", "en": "Definition" }} 
        }}
      ]
    }}
    ※重要：glossaryの"term"は、本文(contents)の中の表記と完全一致させてください。
    """
    
    # 検索を伴う重い処理のため、タイムアウトを10分(600s)に設定
    config = {
        'tools': [{'google_search': {}}],
        'temperature': 0.1,
        'http_options': {'timeout': 600} 
    }

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', # 安定版の名称に変更
            contents=prompt,
            config=config
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
