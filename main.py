import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
# typesのインポートを削除し、極力シンプルにします

JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")

# クライアント初期化（タイムアウト設定をあえて空にします）
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    # 検索の負荷を最小限にするため、プロンプトをさらに簡潔に
    prompt = f"今日（{TODAY}）の日本の主要な経済ニュースを1つ選び、日本語と英語でコラムを書いて。JSON形式で出力して。"

    try:
        # 1sエラーを回避するため、configを最小限の辞書形式にします
        # モデルを最も安定している1.5-flashに変更
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=prompt,
            config={
                'tools': [{'google_search': {}}],
                'temperature': 0.1
                # http_options を完全に削除
            }
        )
        
        if not response.text:
            raise ValueError("APIからの応答が空です")

        res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(res_text)

    except Exception as e:
        print(f"API Error: {e}")
        raise e

def main():
    try:
        data = generate_content()
        data_path = 'docs/data.json'
        
        # 常に最新1件で上書き（リセット）
        history = [data]
        
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
                
        print(f"Success: {data['titles']['ja']}")
    except Exception as e:
        print(f"Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
