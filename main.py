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

# タイムアウト回避のため、接続設定をあえて空にしてデフォルトの挙動に任せます
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] 分析開始（タイムアウト対策実行中）...")
    
    # プロンプトの内容（中学生向け解説など）はそのまま維持
    # 最後に1行だけ「迅速に」という指示を追加して、検索の深追いによる切断を防ぎます
    prompt = f"""
    【役割】
    あなたは「世界一わかりやすい経済ニュース」を執筆するシニアアナリストです。
    今日（{TODAY}）の日本の主要ニュース（例：高市首相の衆院解散検討など）を1つ選び、事実の分析と「背景知識の習得」を両立させたコラムを執筆してください。

    【記事の構成指示：contents内に必ず含めること】
    1. 【事実の概要】：今、何が起きているのかを簡潔に。
    2. 【専門的分析】：円安や金利、市場への影響をプロの視点で。
    3. 【徹底解説：なぜ？の背景】：中学生でもわかるように以下の点を解説してください。
       - 「衆議院の解散」とは何か（例：ゲームのリセットや、比喩を使って）。
       - 首相はなぜ今、解散したいのか（目的）。
       - それによって誰が、どんな得をする可能性があるのか。
    4. 【私達への影響】：私達の生活（お小遣いや物価）にどう関係するか。

    【執筆ルール】
    - 主語は「私達」とし、親しみやすくも知的なトーンで。
    - 「：」（コロン）の使用は厳禁。
    - 難しい政治・経済用語は必ずglossaryに含める。
    - タイムアウトを避けるため、検索結果を素早くまとめ、1000文字程度で簡潔に回答してください。

    【出力形式】
    以下のキーを持つJSONのみを出力（JSON Mode）。
    keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    """

    try:
        # ツール呼び出しの設定を最小限にします
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.1
                # http_options をあえて設定せず、システムのデフォルトに委ねます
            )
        )
        
        # JSON解析（前回追加した補完ロジックを維持）
        res_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        data = json.loads(res_text)

        # キーの補完
        if 'titles' not in data and 'title' in data:
            data['titles'] = data['title']

        data["id"] = UPDATE_ID
        data["date"] = TODAY
        return data

    except Exception as e:
        print(f"[{datetime.now()}] エラー発生: {e}")
        # 切断された場合、検索ツールをオフにして再試行するロジック（オプション）
        raise e

def main():
    data_path = 'docs/data.json'
    try:
        new_data = generate_content()
        # 以下、保存処理は変更なし
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
        print(f"Success: {new_data.get('titles', {}).get('ja', 'Untitled')}")
    except Exception as e:
        print(f"Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
