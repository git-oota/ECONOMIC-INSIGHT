import os
import json
import logging
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 環境設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_content():
    print(f"[{datetime.now()}] ニュース分析（検索モード）を開始...")
    
    prompt = f"""
    You are a professional economic analyst for international students in Japan.
    【Task】
    1. Use Google Search to find real economic news in Japan for today ({TODAY}).
    2. Summarize the news in an engaging, easy-to-understand way.
    
    【Required Insights】
    - あなたは日経新聞社のシニア編集者です。日経新聞よりTOPニュースを取得し、著作権に抵触しないようにリライトしてください。
    - 経済関連のニュースの場合は、投資家目線で、投資家への影響と推奨アクションを記載して。
    - 大学生でもわかるように、ニュースを読むために必要な背景知識（Essential Context）を詳しく説明してください。
    - 国際的なニュースの場合は、アメリカ、中国での報道のされ方を探し、日本での解釈と比較して。
    
    【SEO & Glossary Rule】
    - descriptions: 検索エンジン（Google）の結果に表示されるための要約です。 jaは120文字以内、enは160文字以内で、思わずクリックしたくなる内容にしてください。
    - glossary: 本文中の専門用語を3〜5個抽出。termは本文の表記と完全に一致させてください。

    【捏造厳禁】
    - 過去48時間以内の情報を採用。架空のニュースは絶対に書かない。
    - データ不足時は朝日新聞、読売新聞、産経新聞から収集。

    【Output Format: Strict JSON only】
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "descriptions": {{ 
        "ja": "検索結果に表示される120文字程度の要約", 
        "en": "SEO-friendly summary for search results" 
      }},
      "contents": {{ 
        "ja": "【ニュース】\\n...\\n\\n【資産防衛のヒント】\\n...", 
        "en": "..." 
      }},
      "mermaid": {{ "ja": "graph TD...", "en": "graph TD..." }},
      "glossary": [
        {{
          "term": {{ "ja": "用語", "en": "Term" }},
          "def": {{ "ja": "解説", "en": "Explanation" }}
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
                temperature=0.7 
            )
        )
        
        content = json.loads(response.text)
        if isinstance(content, list):
            content = content[0]
            
        return content

    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

def main():
    data_path = 'docs/data.json'
    new_article = generate_content()
    
    if new_article is None:
        print("⚠️ 記事生成に失敗しました。")
        return

    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list): history = []
            except:
                history = []
    
    history.insert(0, new_article)
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    title_ja = new_article.get('titles', {}).get('ja', 'No Title')
    print(f"✅ Success: {title_ja}")

if __name__ == "__main__":
    main()
