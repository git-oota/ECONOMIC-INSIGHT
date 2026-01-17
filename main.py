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
    
    【Required Insights (重要)】
    - あなたは日経新聞社のシニア編集者です。日経新聞よりTOPニュースを取得し、著作権に抵触しないようにリライトしてください。
    - 経済関連のニュースの場合は、投資家目線で、投資家にどのような影響があるか、投資家はどう動くべきかを記載して。
    - 大学生でもわかるように、ニュースを読むために必要な背景知識について詳しく説明してください。
    - 国際的なニュースの場合は、アメリカ、中国でのニュースの報道のされ方を探し、日本での解釈と比較して。
    
    【Glossary Generation Rule】
    - 本文（contents）の中で使用した専門用語や難しい経済単語を3〜5個抽出してください。
    - "term" に入れる文字列は、必ず本文中で使用している表記と完全に一致させてください（HTMLでの自動置換に使用するため）。

    【捏造厳禁】
    - 新しいニュースがない場合は過去48時間以内の情報を採用。
    - 架空のニュースは絶対に書かない。データがない場合は為替動向と学費への影響に絞る。

    【Output Format: Strict JSON only】
    必ず以下のJSON形式のオブジェクト1つだけを出力してください。
    JSONの構文エラー（閉じカッコの不足、カンマのミスなど）は絶対に避けてください。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ 
        "ja": "【ニュース】\\n...\\n\\n【資産防衛のヒント】\\n...\\n\\n【生活への影響】\\n...", 
        "en": "..." 
      }},
      "mermaid": {{ "ja": "graph TD...", "en": "graph TD..." }},
      "glossary": [
        {{
          "term": {{ "ja": "本文中の用語1", "en": "Term1" }},
          "def": {{ "ja": "用語1の簡潔な解説", "en": "Explanation1" }}
        }}
      ]
    }}
    """

    try:
        # モデルをより安定した gemini-3-flash-preview に変更
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
        
        # ★エラー対策：もしリストで返ってきたら最初の要素を取り出す
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
        print("⚠️ 記事生成に失敗しました。更新をスキップします。")
        return

    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list): history = []
            except Exception as e:
                history = []
    
    # 記事を先頭に追加
    history.insert(0, new_article)
    
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    # 安全な取得方法に変更
    title_ja = new_article.get('titles', {}).get('ja', 'No Title')
    print(f"✅ Success: {title_ja}")

if __name__ == "__main__":
    main()
