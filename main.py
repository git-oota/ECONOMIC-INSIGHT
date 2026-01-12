import os
import json
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. 環境設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析を開始...")
    
    prompt = f"""
    【検索と事実確認の厳命】
    1. Google Searchを使用して、今日（{TODAY}）の日本の経済・ビジネスニュースを検索してください。
    2. 信頼できるソース（日本経済新聞、Bloomberg、ロイター、時事通信、読売新聞、朝日新聞）から情報を得てください。
    3. 【禁止事項】: 検索結果に存在しないイベントを絶対に捏造しないでください。もし今日（{TODAY}）が祝日で新しいニュースが極めて少ない場合は、直近24〜48時間以内の重要なニュースを採用してください。
    4. それでも具体的なニュースが見つからない場合は、架空のニュースを書かず、タイトルを「【休刊日】本日の重要ニュースはありません」とし、内容は「経済の大きな動きは報告されていません」と出力してください。

    【ライティングガイドライン】
    - 事実：ソース元の情報を正確に要約してください。
    - 著作権保護：記事を丸写しせず、必ず「あなた（AI）」の言葉で解説コラムとして再構成してください。
    - 匿名性：特定の新聞社名（「〇〇新聞によると」等）は本文に出さないでください。
    - 中学生向け解説：専門用語を「学校」「ゲーム」「お小遣い」などの比喩で説明してください。

    【出力形式】
    必ず以下のJSON形式のみを出力してください。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "contents": {{ 
        "ja": "【ニュースの事実】\\n(ここに検索結果に基づいた事実)\\n\\n【中学生への解説】\\n(ここに比喩解説)\\n\\n【生活への影響】\\n(ここに将来への影響)", 
        "en": "English Summary" 
      }},
      "mermaid": {{ "ja": "graph TD\\nA-->B", "en": "graph TD\\nA-->B" }},
      "glossary": [
        {{
          "term": {{ "ja": "用語", "en": "Term" }},
          "def": {{ "ja": "解説", "en": "Definition" }}
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
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"API Error: {e}")
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "分析エラー", "en": "Error"},
            "contents": {"ja": "現在データを生成できません。", "en": "Error."},
            "mermaid": {"ja": "graph TD\nError", "en": "graph TD\nError"},
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
    
    # 新しい記事を追加して保存（最大50件）
    history.insert(0, new_article)
    os.makedirs('docs', exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    print(f"✅ Success: {new_article.get('titles', {}).get('ja', 'No Title')}")

if __name__ == "__main__":
    main()
