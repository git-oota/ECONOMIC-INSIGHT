import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# クライアント初期化（タイムアウト設定を完全に削除してデフォルトに任せる）
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析を開始（JSON Mode）...")
    
    # 1. プロンプトの定義（ここでの字下げは文字列の中身として扱われます）
    prompt = f"""
    【役割】
    あなたは冷静沈着なシニア経済アナリストとして、今日（{TODAY}）の日本の主要経済ニュースを1つ選定し、多角的な分析コラムを執筆してください。

    【分析の深さに関する指示】
    単なる事実の羅列ではなく、以下の「負の連鎖」を深掘りしてください。
    1. 円安による「輸入インフレ（コストプッシュ型）」が家計の購買力を削る構造。
    2. 金利上昇が住宅ローンや中小企業の資金繰りに与える具体的な圧力。
    3. 積極財政への期待と、財政規律への懸念がもたらす市場のジレンマ。
    4. 「家計への二重の圧力」という視点から、読者に危機感と示唆を与える内容にしてください。

    【執筆ルール】
    - 主語は「私達」とし、プロフェッショナルかつ批評的なトーンで執筆。
    - 「：」（コロン）の使用は厳禁。
    - 中学生でも理解できるよう、専門用語は必ずglossaryで解説してください。

    【出力形式】
    必ず以下のキーを持つJSON形式で出力してください（JSON Mode）。
    keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    
    ※titles, contents, mermaid, glossaryは、それぞれ "ja" と "en" の子要素を持つこと。
    "glossary"は、本文で使用した難解な用語を3〜5個含める配列形式とすること。
    """

    # 2. ここから下の try: の位置が prompt と同じ垂直線上にある必要があります
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.1
            )
        )
        
        data = json.loads(response.text)
        data["id"] = UPDATE_ID
        data["date"] = TODAY
        return data

    except Exception as e:
        print(f"[{datetime.now()}] APIエラー詳細: {e}")
        raise e

def main():
    data_path = 'docs/data.json'
    try:
        new_data = generate_content()
        
        # リセット上書き（アーカイブを消して1件目からやり直す）
        history = [new_data]
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
                
        print(f"成功: {new_data['titles']['ja']} を作成しました。")
    except Exception as e:
        print(f"Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
