import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] 分析開始...")
    
    # プロンプト（内容は変えず、最後にフォーマットの念押しを追加）
    prompt = f"""
    【指示】
    今日（{TODAY}）の日本の主要経済ニュース（高市首相の解散検討など）を1つ選び、以下のJSON形式で出力してください。

    【内容】
    1. 事実：ニュースの概要。
    2. 解説：中学生向けに「なぜ解散するのか」「誰が得するのか」を、ゲームや比喩を使ってわかりやすく説明。
    3. 分析：円安と金利上昇が私達の生活に与える影響。

    【出力ルール（厳守）】
    - 出力は必ず以下のJSONのみ。前後の説明文や ```json などの枠は一切禁止。
    - キー名は必ず複数形の "titles", "contents" とすること。
    - keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    - タイムアウトを避けるため、検索は日経新聞などの主要1〜2サイトに絞り、迅速に回答してください。
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
        
        # --- ここから強化：文字列からJSONを抽出して必ず辞書にする ---
        res_text = response.text.strip()
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(res_text)

        # 万が一、結果がリストや文字列だった場合に辞書へ強制変換
        if not isinstance(data, dict):
            print(f"警告: AIが辞書を返しませんでした。型: {type(data)}")
            data = {"titles": {"ja": str(data), "en": "Error"}, "contents": {"ja": str(data), "en": "Error"}}

        # 足りないキーを補完（KeyError対策）
        data["id"] = data.get("id", UPDATE_ID)
        data["date"] = data.get("date", TODAY)
        if "titles" not in data and "title" in data: data["titles"] = data["title"]
        if "glossary" not in data: data["glossary"] = []
        if "mermaid" not in data: data["mermaid"] = {"ja": "graph TD;A-->B", "en": "graph TD;A-->B"}

        return data # 確実に辞書(dict)を返す

    except Exception as e:
        print(f"API解析エラー: {e}")
        # 最低限の構造を持つ辞書を返してmainを落とさない
        return {"titles": {"ja": "分析エラー", "en": "Error"}, "contents": {"ja": str(e), "en": str(e)}, "glossary": []}

def main():
    data_path = 'docs/data.json'
    try:
        # 戻り値が確実に辞書であることを想定
        new_data = generate_content()
        
        if not isinstance(new_data, dict):
            print("Fatal Error: generate_content did not return a dictionary")
            exit(1)

        history = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                except: history = []
        
        history.insert(0, new_data)
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
        
        # 安全なアクセス
        title_ja = new_data.get('titles', {}).get('ja', 'Untitled')
        print(f"✅ Success: {title_ja}")

    except Exception as e:
        print(f"❌ Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
