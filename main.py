import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai  # 新しいライブラリを使用

# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# Geminiクライアントの初期化
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    prompt = f"""
    今日（{TODAY}）の日本の主要ニュース（日経新聞、朝日新聞、読売新聞などで報じられた経済・社会ニュース）を1つ選定し、分析記事を書いてください。
    
    ## 執筆ルール
    1. 「ブルームバーグ」や「エディトリアル・ボート」という言葉は厳禁です。
    2. 主語は「私達」としてください。
    3. 専門用語は中学生にもわかるよう日・英両方で解説。
    4. Mermaid図解を含めてください。
    5. 必ず以下のJSON形式で出力してください。

    ## 出力形式 (JSON)
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "..", "en": ".." }},
      "contents": {{ "ja": "..", "en": ".." }},
      "mermaid": {{ 
        "ja": "graph TD; ...（日本語の図解）", 
        "en": "graph TD; ...（英語の図解）" 
      }},
      "glossary": [...]
    }}
    """
    
    # ツール名を 'google_search' に修正
    response = client.models.generate_content(
        model='gemini-3-flash-preview', # 最新モデルを推奨
        contents=prompt,
        config={
            'tools': [{'google_search': {}}] 
        }
    )
    
    # JSON部分の抽出
    res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
    return json.loads(res_text)

def main():
    data = generate_content()
    data_path = 'docs/data.json'
    
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    # 同日の更新も履歴に残す（IDで識別）
    history.insert(0, data)
    os.makedirs('docs', exist_ok=True)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
            
    print(f"Success: {data['titles']['ja']}")

if __name__ == "__main__":
    main()
