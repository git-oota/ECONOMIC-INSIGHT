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
    # 検索ツールを確実に機能させ、事実に基づかせるための指示
    prompt = f"""
    【最優先指示】
    1. Google検索ツールを使用して、今日（{TODAY}）または直近24時間以内に、日本経済新聞、朝日新聞、読売新聞などの信頼できる日本のメディアが実際に報じた「経済・社会・テクノロジー」に関するニュースを検索してください。
    2. 検索結果に存在しない出来事、架空の数値（「40%の企業が導入」など）、未来予測を「今日起きたニュース」として捏造することは厳禁です。
    3. 複数の検索結果から、最も投資価値や分析価値の高いトピックを1つ選定してください。

    ## 執筆ルール
    - 主語は「私達」とし、プロフェッショナルな経済分析コラムにリライトしてください。
    - 出典元の新聞社名は伏せてください。
    - 構造分析チャート（mermaid）は、日本語と英語の両方で作成してください。

    ## 出力形式 (JSONのみ)
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "日本語タイトル", "en": "English Title" }},
      "contents": {{ "ja": "日本語本文（改行は\\n）", "en": "English Content" }},
      "mermaid": {{ 
        "ja": "graph TD; ...（日本語の図解データ）", 
        "en": "graph TD; ...（英語の図解データ）" 
      }},
      "glossary": [
        {{ 
          "term": {{ "ja": "用語名", "en": "Term" }}, 
          "def": {{ "ja": "日本語解説", "en": "English definition" }} 
        }}
      ]
    }}
    """
    
    # モデル設定（より厳格に事実に基づかせるため、温度パラメーターを低めに設定することもありますが
    # google-genaiのデフォルトでも検索ツールがあれば精度は上がります）
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config={{
            'tools': [{{'google_search': {{}}}}],
            'temperature': 0.1  # 創造性を抑え、事実への忠実度を高める
        }}
    )
    
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
