import os
import json
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. 環境設定 (日本標準時)
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# Gemini クライアント初期化
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析（検索モード）を開始...")
    
    # フェイク防止を徹底したプロンプト
    prompt = f"""
    【絶対守守事項: 創作の禁止】
    1. Google Searchを使用して、今日（{TODAY}）の日本の経済ニュースを検索してください。
    2. 信頼できるソース（日本経済新聞、Bloomberg、ロイター、読売新聞、朝日新聞）の情報を優先してください。
    3. 【捏造厳禁】: もし今日（祝日など）で新しいニュースがない場合は、過去48時間以内の重要な経済ニュースを採用してください。
    4. それでも具体的な事実が見つからない場合は、架空のニュースを絶対に書かず、タイトルを「【経済指標】直近の市場動向」とし、既知の指標（株価や為替の傾向）について述べてください。
    5. 著作権に配慮し、元の文章を丸写しせず、必ずあなた自身の言葉で中学生向けに再構成してください。特定の社名は出さないでください。

    【出力形式: JSON】
    必ず以下のJSON形式のみを出力してください（Markdownの枠は不要）。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ 
        "ja": "【ニュースの事実】\\n(検索結果に基づく事実)\\n\\n【中学生への解説】\\n(学校や身近な生活に例えた解説)\\n\\n【生活への影響】\\n(将来や家計への影響)", 
        "en": "English Summary" 
      }},
      "mermaid": {{ "ja": "graph TD\\nA[事実]-->B[変化]\\nB-->C[結果]", "en": "graph TD\\nA-->B" }},
      "glossary": [
        {{
          "term": {{ "ja": "専門用語", "en": "Term" }},
          "def": {{ "ja": "簡単な意味", "en": "Definition" }}
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
                temperature=0.0  # 創作（嘘）を排除し、事実を優先
            )
        )
        
        # レスポンスのパース
        return json.loads(response.text)

    except Exception as e:
        print(f"Error: {e}")
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "データ更新中", "en": "Updating Data"},
            "contents": {"ja": "現在、最新の信頼できるニュースを精査中です。しばらくしてから再度ご確認ください。", "en": "Checking latest reliable news."},
            "mermaid": {"ja": "graph TD\nWait", "en": "graph TD\nWait"},
            "glossary": []
        }

def main():
    data_path = 'docs/data.json'
    new_article = generate_content()
    
    # 既存データの読み込み
    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list): history = []
            except:
                history = []
    
    # 最新記事を先頭に追加（最大50件保持）
    history.insert(0, new_article)
    
    os.makedirs('docs', exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    print(f"✅ Success: {new_article.get('titles', {}).get('ja')}")

if __name__ == "__main__":
    main()
