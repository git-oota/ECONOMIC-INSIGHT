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
    
    # プロンプトを極限までシンプルにし、JSON構造を指示
    prompt = f"""
    今日の日本の主要経済ニュースを1つ選び、日本語と英語で分析コラムを書いてください。
    出力は必ず以下のキーを持つJSON形式にしてください。
    keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    
    titlesとcontentsとmermaidとglossaryは、それぞれ "ja" と "en" の子要素を持ってください。
    "glossary"は [{{ "term": {{"ja":..,"en":..}}, "def": {{"ja":..,"en":..}} }}] の配列です。
    """

    try:
        # 1sエラーを避けるため http_options を使わず、1.5-flash で実行
        # response_mime_type を指定することで JSON 形式を強制
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.1
            )
        )
        
        # JSONとして直接ロード（JSON Modeなので response.text がそのままJSONになる）
        data = json.loads(response.text)
        
        # データの整合性チェック
        if 'titles' not in data:
            # 万が一JSON Modeが不完全だった場合の抽出バックアップ
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            data = json.loads(match.group())

        # IDと日付を強制セット
        data["id"] = UPDATE_ID
        data["date"] = TODAY
        
        return data

    except Exception as e:
        print(f"[{datetime.now()}] APIエラー詳細: {e}")
        # 予期せぬエラー時のためのデバッグ出力
        if 'response' in locals():
            print(f"Raw response: {response.text[:500]}")
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
