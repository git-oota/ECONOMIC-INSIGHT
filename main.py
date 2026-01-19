import os
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 環境設定
JST = timezone(timedelta(hours=+9), 'JST')
NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d")
UPDATE_ID = NOW.strftime("%Y%m%d_%H%M%S")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_content():
    print(f"[{datetime.now()}] SEO強化モードでニュース分析を開始...")
    
    prompt = f"""
    You are a professional economic analyst and SEO specialist for international audiences.
    【Task】
    1. Use Google Search to find real economic news in Japan for today ({TODAY}).
    2. Summarize the news in an engaging way for a global audience.
    
    【SEO Keyword Strategy】
    - Titles & Descriptions の左側に重要語（Japan Economy, Nikkei 225, Yen (JPY), BoJ, Inflation）を配置。
    - 英語タイトルは検索結果でのクリック率（CTR）を意識した魅力的なものに。

    【Required Insights】
    - 日経新聞編集者の視点でリライト（著作権順守）。
    - 投資家への影響と具体的な推奨アクション。
    - 大学生・留学生向けの背景知識（Essential Context）解説。
    - 米・中との報道内容の比較分析。
    
    【Output Format: Strict JSON only】
    {{
      "id": "{UPDATE_ID}",
      "date": "{TODAY}",
      "titles": {{ "ja": "タイトル", "en": "Title" }},
      "descriptions": {{ "ja": "120文字要約", "en": "160 chars SEO summary" }},
      "contents": {{ "ja": "本文", "en": "Body" }},
      "mermaid": {{ "ja": "graph TD...", "en": "graph TD..." }},
      "glossary": [ {{ "term": {{"ja":"用語","en":"Term"}}, "def": {{"ja":"解説","en":"Exp"}} }} ]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                response_mime_type='application/json',
                temperature=0.7 
            )
        )
        content = json.loads(response.text)
        return content[0] if isinstance(content, list) else content
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

def update_sitemap(data_path):
    """sitemap.xmlを自動生成・更新する"""
    base_url = "https://jp-economy.com"
    pages = [
        "index.html",
        "profile.html",
        "privacy.html",
        "contact.html",
        "context/rate.html"
    ]
    
    # XMLの構造を作成
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    for page in pages:
        url_el = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_el, "loc")
        loc.text = f"{base_url}/{page}"
        lastmod = ET.SubElement(url_el, "lastmod")
        lastmod.text = TODAY
        changefreq = ET.SubElement(url_el, "changefreq")
        changefreq.text = "daily" if page == "index.html" else "weekly"
        priority = ET.SubElement(url_el, "priority")
        priority.text = "1.0" if page == "index.html" else "0.8"

    # 保存
    sitemap_path = os.path.join(os.path.dirname(data_path), 'sitemap.xml')
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ", level=0) # 見やすく整形
    tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
    print(f"✅ Sitemap updated: {sitemap_path}")

def main():
    data_path = 'docs/data.json'
    new_article = generate_content()
    
    if new_article is None:
        print("⚠️ 記事生成に失敗しました。")
        return

    history = []
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                if not isinstance(history, list): history = []
            except:
                history = []
    
    history.insert(0, new_article)
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    # 記事データ保存
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)
    
    # サイトマップ更新
    update_sitemap(data_path)
    
    print(f"✅ Success: {new_article.get('titles', {}).get('ja')}")

if __name__ == "__main__":
    main()
