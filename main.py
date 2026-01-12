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
    【重要ミッション】
    1. Google Searchを使用して、今日（{TODAY}）の日本の主要経済ニュースを「日本経済新聞」「Bloomberg」「朝日新聞」「読売新聞」などの信頼できる情報源からリサーチしてください。
    2. その中から、特に中学生の生活や将来に関係がありそうな「事実に基づいたニュース」を1つ選んでください。
    3. 著作権法を遵守するため、元の記事の文章をそのまま使わず、必ず「あなた自身の言葉」で以下の構成でコラムを作成してください。
       - 事実概要：何が起きたか（客観的な事実のみ）
       - 中学生向け解説：難しい用語を身近な例え話（学校やゲームなど）で説明
       - 私たちの生活への影響：将来の仕事や、お小遣い、物価にどう響くか
    4. 掲載元の社名（「日経新聞によると」など）は一切出さないでください。

    【出力形式】
    必ず以下のJSON形式のみを出力してください。Markdownの枠や説明文は不要です。
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "目を引くキャッチーなタイトル", "en": "English Title" }},
      "contents": {{ 
        "ja": "【ニュースの事実】\\n(ここに事実)\\n\\n【中学生への解説】\\n(ここに例え話)\\n\\n【生活への影響】\\n(ここに影響)", 
        "en": "English content summary" 
      }},
      "mermaid": {{ 
        "ja": "graph TD\\nA[事象]-->B[変化]\\nB-->C[結果]", 
        "en": "graph TD\\nA[Event]-->B[Change]\\nB-->C[Result]" 
      }},
      "glossary": [
        {{
          "term": {{ "ja": "専門用語", "en": "Term" }},
          "def": {{ "ja": "その用語の簡単な説明", "en": "Definition" }}
        }}
      ]
    }}
    ※JSONのパースエラーを防ぐため、ダブルクォーテーションの扱いに注意し、改行は \\n を使用してください。
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
