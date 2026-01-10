import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")

# クライアント初期化
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース検索と記事生成を開始します...")
    
    prompt = f"今日（{TODAY}）の主要な経済ニュースを1つ選び、日本語と英語でプロフェッショナルなコラムを執筆してください。構造分析チャート(mermaid)と中学生向けの用語解説(glossary)も含めて、指定のJSON形式で出力してください。"

    try:
        # タイムアウトを辞書形式で、かつ長めに設定
        # 'timeout' の値を 600 (秒) と明確に指定します
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                temperature=0.1,
                http_options={'timeout': 600.0} # floatで指定
            )
        )
        
        print(f"[{datetime.now()}] APIからの応答を受信しました。")
        res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(res_text)

    except Exception as e:
        print(f"[{datetime.now()}] エラー発生: {e}")
        raise e

def main():
    data_path = 'docs/data.json'
    try:
        data = generate_content()
        # リセットをかけるため、新規リストを作成
        history = [data]
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
                
        print(f"成功: {data['titles']['ja']} を保存しました。")
    except Exception as e:
        # 失敗した場合、data.jsonが[]だと画面が止まるので、エラー内容を書き込むか検討
        print(f"最終エラー: {e}")
        exit(1)

if __name__ == "__main__":
    main()
