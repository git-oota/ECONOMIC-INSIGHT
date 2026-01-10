import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. 環境設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# 2. クライアント初期化（タイムアウトバグ回避のため設定なし）
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析を開始（2026年モード）...")
    
    prompt = f"""
    今日（{TODAY}）の日本の主要経済ニュースを1つ選び、中学生でもわかる「解説付き」のコラムを書いてください。
    
    【構成】
    1. 事実：今何が起きているか。
    2. 解説：なぜ解散するのか、誰が得するのか（比喩を使って）。
    3. 分析：円安と金利上昇が私達の生活にどう響くか。

    【出力ルール】
    - 出力は必ず以下のJSON形式のみ（前後の説明文やMarkdown枠は禁止）。
    - keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    - タイムアウトを避けるため、1000文字程度で簡潔に回答してください。
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
        
        # --- 堅牢なパース処理 ---
        res_text = response.text.strip()
        
        # 1. 最初の { と 最後の } の間を抽出（余計な文字を排除）
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if match:
            raw_json = match.group()
            data = json.loads(raw_json)
        else:
            # JSONが見つからない場合は例外を投げて except ブロックへ
            raise ValueError("No JSON found in response")

        # 2. もし data が辞書でない（文字列など）場合は辞書へ強制変換
        if not isinstance(data, dict):
            data = {
                "titles": {"ja": str(data), "en": "Analysis Error"},
                "contents": {"ja": "データの形式が正しくありませんでした。", "en": "Data format error."}
            }

        # 3. 必須キーの補完とゆらぎ吸収
        for key in ['titles', 'contents']:
            if key not in data and key[:-1] in data: # title -> titles
                data[key] = data[key[:-1]]
        
        # 4. デフォルト値のセット
        data["id"] = UPDATE_ID
        data["date"] = TODAY
        data.setdefault("titles", {"ja": "無題", "en": "Untitled"})
        data.setdefault("contents", {"ja": "本文なし", "en": "No content"})
        data.setdefault("mermaid", {"ja": "graph TD;Error", "en": "graph TD;Error"})
        data.setdefault("glossary", [])

        return data

    except Exception as e:
        print(f"生成エラー: {e}")
        # 万が一の際も、必ず「辞書」を返す
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "分析レポート生成エラー", "en": "Generation Error"},
            "contents": {"ja": f"エラー: {str(e)}", "en": f"Error: {str(e)}"},
            "mermaid": {"ja": "graph TD;Error", "en": "graph TD;Error"},
            "glossary": []
        }

def main():
    data_path = 'docs/data.json'
    try:
        # generate_content は必ず辞書(dict)を返すよう設計されています
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
        
        # 先頭に追加
        history.insert(0, new_article)
        
        # 保存
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
                
        # 成功ログ（ここでも get を使い安全にアクセス）
        success_title = new_article.get('titles', {}).get('ja', 'Untitled')
        print(f"✅ Success: {success_title}")

    except Exception as e:
        print(f"❌ Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
