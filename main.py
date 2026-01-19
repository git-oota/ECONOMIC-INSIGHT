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
    print(f"[{datetime.now()}] SEO強化モードでニュース分析を開始...")
    
    prompt = f"""
    You are a professional economic analyst and SEO specialist for international audiences.
    【Task】
    1. Use Google Search to find real economic news in Japan for today ({TODAY}).
    2. Summarize the news in an engaging, easy-to-understand way.
    
    【SEO & Target Keyword Strategy (最重要)】
    - 以下のターゲットキーワードを、自然な形でタイトル(titles)と要約(descriptions)の冒頭（左側）に含めてください。
    - 英語キーワード: "Japan Economy", "Nikkei 225", "Yen (JPY)", "Bank of Japan (BoJ)", "Investing in Japan", "Inflation".
    - 日本語キーワード: "日本経済", "日経平均", "円安", "金利", "投資", "ニュース要約".
    - 検索エンジンは文章の先頭に近い単語を重視します。重要な単語を必ず左側に配置してください。

    【Required Insights】
    - あなたは日経新聞社のシニア編集者です。日経新聞よりTOPニュースを取得し、著作権に配慮してリライトしてください。
    - 経済関連のニュースの場合は、投資家目線で、マーケットへの影響と推奨アクションを具体的に記載して。
    - 大学生でもわかるように、ニュースを読むために必要な背景知識（Essential Context）を詳しく説明してください。
    - 国際比較：アメリカ（WSJ）や中国での報道のされ方を探し、日本での解釈と比較分析して。
    
    【Metadata & Glossary Rule】
    - descriptions: 検索結果(SERPs)のクリック率を最大化するための要約です。
        - ja: 120文字以内。読者が「答えを知りたくなる」フックを作ってください。
        - en: 160文字以内。キーワードを盛り込みつつ、プロフェッショナルなトーンで。
    - glossary: 本文中の専門用語を3〜5個抽出。termは本文の表記と完全に一致させてください。

    【捏造厳禁】
    - 過去48時間以内の情報を採用。架空のニュースは絶対に書かない。
    - データ不足時は朝日新聞、読売新聞、産経新聞から収集。

    【Output Format: Strict JSON only】
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "SEOキーワードを含むタイトル", "en": "Keyword-rich Engaging Title" }},
      "descriptions": {{ 
        "ja": "前半に重要単語を配置した要約", 
        "en": "Search-optimized summary starting with target keywords" 
      }},
      "contents": {{ 
        "ja": "【今日のニュース】\\n...\\n\\n【投資家へのインサイト】\\n...\\n\\n【Essential Context】\\n...", 
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
    
    # 記事を先頭に追加
    history.insert(0, new_article)
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    title_ja = new_article.get('titles', {}).get('ja', 'No Title')
    print(f"✅ Success: {title_ja}")

if __name__ == "__main__":
    main()
