import os
import json
import re
from datetime import datetime, timezone, timedelta
import google.generativeai as genai

# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
# 同日更新を可能にするため、IDに「秒」まで含める
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# Gemini設定
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    # Google検索を有効にして、正確なニュースを取得
    model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview',
        tools=[{'google_search_retrieval': {}}]
    )
    
    prompt = f"""
    今日（{TODAY}）の日本の主要ニュース（日経新聞、朝日新聞、読売新聞などで報じられた経済・社会ニュース）を1つ選定し、分析記事を書いてください。
    
    ## 執筆ルール
    1. 「ブルームバーグ」や「エディトリアル・ボード」という言葉は絶対に使わないでください。
    2. 主語は「私達」としてください。
    3. 専門用語（パラダイム、サプライチェーン等）は、中学生でもわかるよう平易な解説を日・英両方で作成してください。
    4. 記事の内容に基づいたMermaid図解（フローチャート等）を作成してください。
    5. 出力は必ず以下のJSON形式のみとしてください。

    ## 出力形式 (JSON)
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "..", "en": ".." }},
      "contents": {{ "ja": "..", "en": ".." }},
      "mermaid": "graph TD; ...",
      "glossary": [
        {{ 
          "term": {{ "ja": "用語名", "en": "Term" }}, 
          "def": {{ "ja": "日本語解説", "en": "English definition" }} 
        }}
      ]
    }}
    """
    
    response = model.generate_content(prompt)
    # JSON部分のみを抽出
    res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
    return json.loads(res_text)

def main():
    try:
        data = generate_content()
        data_path = 'docs/data.json'
        
        # 既存データの読み込み
        history = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # 新しいデータを先頭に追加（同日の重複はIDで識別）
        history.insert(0, data)
        
        # docsフォルダがない場合は作成
        os.makedirs('docs', exist_ok=True)
        
        # 保存（最新50件）
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
            
        print(f"Success: {data['titles']['ja']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
