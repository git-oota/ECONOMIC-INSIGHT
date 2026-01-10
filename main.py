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
    
    # プロンプトは変更なし（そのまま使用）
    prompt = f"""
    （ここにあなたの現在のプロンプトをそのまま入れてください）
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
        
        # --- ここから修正：解析を堅牢にする ---
        res_text = response.text.strip()
        
        # もしMarkdownのコードブロック（```json）が含まれていたら削除
        res_text = re.sub(r'^```json\s*', '', res_text)
        res_text = re.sub(r'\s*```$', '', res_text)
        
        # 正規表現で最初と最後の { } を探し、その中身だけを抽出
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            # それでもダメな場合は、文字列そのものを評価
            data = json.loads(res_text)

        # IDと日付をここで確実にセット（AI側の欠落対策）
        data["id"] = UPDATE_ID
        data["date"] = TODAY
        
        return data

    except Exception as e:
        print(f"[{datetime.now()}] 解析エラー発生。返却されたテキスト：")
        print(response.text[:500]) # ログに冒頭500文字を出力して原因特定
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
