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
    今日（{TODAY}）の日本の主要ニュース（例：高市首相の衆院解散検討など）を1つ選び、事実の分析と「背景知識の習得」を両立させたコラムを書いてください。
    
    【構成】事実概要、専門的分析、中学生向け解説（なぜ解散？誰が得？）、私達への影響
    【ルール】主語は「私達」、「：」は禁止、難しい用語はglossaryへ
    【出力】必ず以下のキーを持つJSONのみを出力してください
    keys: "id", "date", "titles", "contents", "mermaid", "glossary"
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
