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
【最優先指示：事実性の徹底と検索プロセス】
    1. Google検索を使用し、今日（{TODAY}）または直近24時間以内に、日本経済新聞、朝日新聞、読売新聞、ロイター、ブルームバーグ等の信頼できるメディアが報じた「経済・社会・テクノロジー」のニュースを複数検索してください。
    2. **重要：** 検索されたニュースが「複数のメディアで共通して報じられている事実」であることを確認してください。単一のブログや出所不明なSNS情報は除外してください。
    3. 存在しない数値や、確定していない未来の予測を「既成事実」として扱うことを厳禁します。

    【執筆ルール：独自性と自然な文章】
    - **主語：** 「私達（The Japan Insight編集部）」の視点で執筆してください。
    - **構成：** 単なる要約ではなく、以下の3点を軸に「プロフェッショナルな経済分析コラム」として作成してください。
        1. 事実の概要（何が起きたか）
        2. 背景と分析（なぜ起きたか、市場の反応はどう変化したか）
        3. 今後の展望と示唆（今後の影響、独自の洞察）
    - **禁止事項：** **「：」（コロン）の使用を一切禁止します。** 項目を説明する際は、コロンを使わずに「〜は以下の通りです」と繋げるか、見出し（###）や太字（**）を適切に使い、AIが生成した箇条書きのような機械的な印象を避けてください。
    - **著作権への配慮：** 特定の記事をそのままリライトするのではなく、複数の情報源から得た「事実」を元に、独自の論理構成と言葉で執筆してください。
    - **出典の扱い：** 特定の社名は避け、「主要各紙の報道を総合すると」や「複数のメディアが伝えるところによれば」という表現を用いてください。

    【アウトプット】
    - 記事タイトル（目を引く専門的なもの）
    - 本文（1000文字程度）
    - 構造分析チャート（mermaid形式）：日本語版と英語版をそれぞれ作成

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
        model='gemini-3-flash-preview',
        contents=prompt,
        config={
            'tools': [{'google_search': {}}], # 波括弧を1つずつにする
            'temperature': 0.1
        }
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
