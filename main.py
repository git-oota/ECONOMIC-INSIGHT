import os
import json
import re
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. 環境設定（2026年JST）
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

# 2. クライアント初期化
# 1sエラーを回避するため、クライアント作成時にタイムアウトを10分(600s)に固定
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_content():
    print(f"[{datetime.now()}] ニュース分析を開始（2026年モード）...")
    
    # プロンプト：事実 + 中学生向け解説 + 二重の圧力
    prompt = f"""
    【役割】
    あなたは「世界一わかりやすい経済ニュース」を執筆するシニアアナリストです。
    今日（{TODAY}）の日本の主要ニュース（例：高市首相の衆院解散検討など）を1つ選び、事実の分析と「背景知識の習得」を両立させたコラムを執筆してください。

    【記事の構成（contents内に含める）】
    1. 【事実の概要】：今、何が起きているのかを簡潔に。
    2. 【専門的分析】：円安や金利、市場への影響をプロの視点で。
    3. 【徹底解説：なぜ？の背景】：中学生でもわかるように以下を解説。
       - 「衆議院の解散」とは何か（ゲームのリセットや、クラス替えのような比喩で）。
       - 首相はなぜ今、解散したいのか（目的）。
       - それによって誰が、どんな得をする可能性があるのか。
    4. 【私達への影響】：円安と金利上昇の「二重の圧力」が私達の生活にどう関係するか。

    【ルール】
    - 主語は「私達」。「：」（コロン）は使用厳禁。
    - 難しい用語（解散、信任、財政出動など）は必ずglossaryに含める。
    - タイムアウトを避けるため、1000文字程度で迅速に回答すること。

    【出力形式】
    必ず以下のキーを持つJSONのみを出力（JSON Mode）。
    keys: "id", "date", "titles", "contents", "mermaid", "glossary"
    """

    try:
        # 安定性と速度を重視し 1.5-flash を使用
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
        # Markdownの枠を削除
        res_text = re.sub(r'^```json\s*', '', res_text)
        res_text = re.sub(r'\s*```$', '', res_text)
        
        # JSON部分を抽出
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if not match:
            raise ValueError("JSON形式が見つかりませんでした。")
        
        data = json.loads(match.group())

        # もし戻り値がリストや文字列だった場合のガード
        if not isinstance(data, dict):
            raise ValueError("返却データが辞書形式ではありません。")

        # --- キーのゆらぎ補完ロジック ---
        # AIが単数形(title)で返しても複数形(titles)に変換
        for key in ['titles', 'contents']:
            single_key = key[:-1] # title, content
            if key not in data and single_key in data:
                data[key] = data[single_key]
        
        # 必須キーのデフォルト補完（KeyError防止）
        default_val = {"ja": "データなし", "en": "No Data"}
        data["titles"] = data.get("titles", default_val)
        data["contents"] = data.get("contents", default_val)
        data["mermaid"] = data.get("mermaid", {"ja": "graph TD;A-->B", "en": "graph TD;A-->B"})
        data["glossary"] = data.get("glossary", [])
        
        # 固定値のセット
        data["id"] = UPDATE_ID
        data["date"] = TODAY

        return data

    except Exception as e:
        print(f"生成エラー: {e}")
        # 最終手段：エラー内容を記事として返す（システムを止めない）
        return {
            "id": UPDATE_ID, "date": TODAY,
            "titles": {"ja": "分析レポート生成エラー", "en": "Analysis Generation Error"},
            "contents": {"ja": f"エラーが発生しました：{str(e)}", "en": f"Error occurred: {str(e)}"},
            "mermaid": {"ja": "graph TD;Error", "en": "graph TD;Error"},
            "glossary": []
        }

def main():
    data_path = 'docs/data.json'
    try:
        # 新しい記事を取得
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
        
        # 先頭に追加して最大50件
        history.insert(0, new_article)
        
        # 保存実行（docsフォルダがない場合も考慮）
        os.makedirs('docs', exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=2)
                
        # 成功ログ
        success_title = new_article.get('titles', {}).get('ja', 'Untitled')
        print(f"✅ Success: {success_title}")

    except Exception as e:
        print(f"❌ Main Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
