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
    あなたは「世界一わかりやすい経済ニュース」を執筆するシニアアナリストです。
    今日（{TODAY}）の日本の主要ニュース（例：高市首相の衆院解散検討など）を1つ選び、事実の分析と「背景知識の習得」を両立させたコラムを執筆してください。

    【記事の構成指示：contents内に必ず含めること】
    1. 【事実の概要】：今、何が起きているのかを簡潔に。
    2. 【専門的分析】：円安や金利、市場への影響をプロの視点で。
    3. 【徹底解説：なぜ？の背景】：ここが重要です。中学生でもわかるように以下の点を解説してください。
       - 「衆議院の解散」とは何か（例：ゲームのリセットや、国民へのアンケートのような比喩を使って）。
       - 首相はなぜ今、解散したいのか（目的）。
       - それによって誰が、どんな得をする可能性があるのか。
    4. 【私達への影響】：私達の生活（お小遣いや物価）にどう関係するか。

    【執筆ルール】
    - 主語は「私達」とし、親しみやすくも知的なトーンで。
    - 「：」（コロン）の使用は厳禁。
    - 難しい政治・経済用語（解散、信任、財政出動など）は必ずglossaryに含める。

    【出力形式】
    以下のキーを持つJSONのみを出力（JSON Mode）。
    keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    ※mermaidは「解散から総選挙、新政権発足までの流れ」を図解してください。
    """

    # 2. ここから下の try: の位置が prompt と同じ垂直線上にある必要があります
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
