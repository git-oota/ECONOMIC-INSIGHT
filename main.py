import os
import json
import logging
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# ログ設定（エラーの原因を特定しやすくする）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 環境設定 (日本標準時)
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# Gemini クライアント初期化
# 注意: GEMINI_API_KEY が環境変数に設定されている必要があります
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_content():
    print(f"[{datetime.now()}] ニュース分析（検索モード）を開始...")
    
    # 面白さと資産リテラシーを組み込んだプロンプト
    prompt = f"""
    You are a professional economic analyst for international students in Japan.
    【Task】
    1. Use Google Search to find real economic news in Japan for today ({TODAY}).
    2. Summarize the news in an engaging, easy-to-understand way (Target: International students).
    
    【Required Insights (面白さのポイント)】
    - Why is this news a "chance" or "risk" for people holding USD or YEN?
    - Add a specific insight about "Asset Protection (投資) vs Consumption (消費)".
    - Example: Mention that while the Yen is weak, buying assets like stocks is better than buying depreciating goods like cars.

    【捏造厳禁】
    - If no new major economic news is found for today, use the latest significant data from the last 48 hours.
    - DO NOT create fake news. If data is unavailable, focus on the current Yen/Dollar trend and its impact on tuition/living costs.

    【Output Format: JSON only】
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ 
        "ja": "【ニュースの事実】\\n...\\n\\n【資産防衛のヒント】\\n(ここにお金と資産の持ち方の知恵を入れる)\\n\\n【生活への影響】\\n...", 
        "en": "..." 
      }},
      "mermaid": {{ "ja": "graph TD...", "en": "graph TD..." }},
      "glossary": [ {{ "term": {{"ja":"..","en":".."}}, "def": {{"ja":"..","en":".."}} }} ]
    }}
    """

    try:
        # モデル名は 'gemini-2.0-flash-exp' 等、利用可能な最新の安定版を指定してください
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.7 # 少し面白さを出すために0.0から0.7へ調整
            )
        )
        
        # JSONとして解析
        content = json.loads(response.text)
        return content

    except Exception as e:
        logger.error(f"API Error: {e}")
        # 失敗時に既存のデータを消さないよう、Noneを返してメイン処理でハンドリングする
        return None

def main():
    data_path = 'docs/data.json'
    new_article = generate_content()
    
    if new_article is None:
        print("⚠️ 記事生成に失敗したため、更新をスキップします。")
        return

    # 既存データの読み込み
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list): history = []
            except Exception as e:
                logger.error(f"JSON Read Error: {e}")
                history = []
    
    # 最新記事を先頭に追加（重複チェックを入れるとより良い）
    history.insert(0, new_article)
    
    # docsディレクトリがない場合は作成
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    print(f"✅ Success: {new_article.get('titles', {}).get('ja')}")

if __name__ == "__main__":
    main()
