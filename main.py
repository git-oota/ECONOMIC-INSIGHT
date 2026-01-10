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

# 2. クライアント初期化
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析を開始...")
    
    prompt = f"""
    今日（{TODAY}）の日本の主要経済ニュースを1つ選び、中学生でもわかる解説付きのコラムを書いてください。
    【構成】事実概要、中学生向け解説（解散の比喩など）、生活への影響
    【出力】必ず以下のキーを持つJSONのみを出力（Markdown枠は禁止）
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
        
        # --- 堅牢なパースロジック ---
        res_text = response.text.strip()
        # 最初の { と 最後の } を抽出
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        
        if match:
            data = json.loads(match.group())
        else:
            # 文字列しか返ってこなかった場合、ここで辞書に無理やり入れる
            raise ValueError(f"JSON not found in response: {res_text[:100]}")

        # 万が一 data がリストや文字列だった場合に辞書へ強制変換
        if not isinstance(data, dict):
            data = {"titles": {"ja": str(data)}}

        # キーの補完（KeyError防止）
        data["id"] = UPDATE_ID
        data["date"] = TODAY
        if "titles" not in data and "title" in data: data["titles"] = data["title"]
        if "contents" not in data and "content" in data: data["contents"] = data["content"]
        
        # 必須構造の保証
        data.setdefault("titles", {"ja": "分析レポート", "en": "Analysis Report"})
        data.setdefault("contents", {"ja": "本文なし", "en": "No content"})
        data.setdefault("mermaid", {"ja": "graph TD;A-->B", "en": "graph TD;A-->B"})
        data.setdefault("glossary", [])

        return data # 必ず辞書を返す

    except Exception as e:
        print(f"API解析エラー: {e}")
        # 【重要】エラー時も「辞書」を返すことで、main()での 'str' エラーを物理的に防ぐ
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "生成エラー", "en": "Generation Error"},
            "contents": {"ja": f"エラー内容: {str(e)}", "en": f"Error: {str(e)}"},
            "mermaid": {"ja": "graph TD;Error", "en": "graph TD;Error"},
            "glossary": []
        }

def main():
    data_path = 'docs/data.json'
    try:
        # 1. 記事生成（この時点で new_article は確実に辞書であることが保証される）
        new_article = generate_content()
        
        # 2. 既存データの読み込み
        history = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list): history = []
                except:
                    history = []
        
        # 3. 先頭に追加
        history.insert(0, new_article)
        
        # 4. 保存
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
                
        # 5. 安全な表示（.get() を使用）
        title_ja = new_article.get('titles', {}).get('ja', 'Untitled')
        print(f"✅ Success: {title_ja}")

    except Exception as e:
        print(f"❌ Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
