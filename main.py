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
    - 日本は現在インフレ傾向にあります。現金のまま持つリスクと、資産を持つべき理由を解説してください。
    - 特に「車などの価値が下がる物」と「株や不動産など、お金を生む資産」の違いを具体例に出して防衛策を提案してください。
    
    【捏造厳禁】
    - 新しいニュースがない場合は過去48時間以内の情報を採用。
    - 架空のニュースは絶対に書かない。データがない場合は為替動向と学費への影響に絞る。
    - 日経新聞、朝日新聞よりTOPニュースを取得し、著作権に抵触しないようにリライトする

    【Output Format: JSON only】
    必ず以下のJSON形式のオブジェクト1つだけを出力してください。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ 
        "ja": "【ニュース】\\n...\\n\\n【資産防衛のヒント】\\n(ここでお金と資産の持ち方の知恵を入れる)\\n\\n【生活への影響】\\n...", 
        "en": "..." 
      }},
      "mermaid": {{ "ja": "graph TD...", "en": "graph TD..." }},
      "glossary": [ {{ "term": {{"ja":"用語","en":"Term"}}, "def": {{"ja":"意味","en":"Def"}} }} ]
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
