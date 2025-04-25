import os
import json
import random
import time
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import google.generativeai as genai

# APIキー設定
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_SEARCH_CX")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# HTML本文取得
def fetch_webpage_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\\n", strip=True)
    except Exception as e:
        return f"[本文取得失敗: {e}]"

# Google検索 + スクレイピング
def search_google_with_scrape(country):
    search_terms = ["パビリオン", "食事", "キャラクター", "イベント"]
    all_html = {}
    summaries = []

    for term in search_terms:
        query = f"万博2025 {country} {term}"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_SEARCH_CX,
            "q": query,
            "num": 3
        }
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        print(f"[検索] {query} | Status: {response.status_code}")
        if response.status_code != 200:
            continue
        results = response.json().get("items", [])
        for item in results:
            url = item.get("link")
            title = item.get("title")
            body = fetch_webpage_text(url)
            if len(body) > 100:
                all_html[title] = {
                    "url": url,
                    "text": body[:3000]
                }
                summaries.append(f"【{title}】\\n{body[:1000]}")

    # HTML本文保存
    os.makedirs("search_logs/html_texts", exist_ok=True)
    with open(f"search_logs/html_texts/{country}.json", "w", encoding="utf-8") as f:
        json.dump(all_html, f, ensure_ascii=False, indent=2)

    return "\\n\\n".join(summaries)

# Gemini要約
def generate_summary_from_html(text):
    try:
        prompt = f"以下は複数のWebページ本文です。万博2025における各国パビリオンの特徴を要約してください。\\n\\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Gemini要約失敗: {e}]"

# メイン実行
def main():
    with open("all_countries.json", "r", encoding="utf-8") as f:
        countries = json.load(f)

    output_data = {}
    for country in countries:
        print(f"🟡 {country} を処理中...")
        body_text = search_google_with_scrape(country)
        summary = generate_summary_from_html(body_text)

        # Markdown 出力（ここが正しいインデント）
        md_dir = "_posts"
        os.makedirs(md_dir, exist_ok=True)
        md_filename = os.path.join(md_dir, f"{datetime.now().strftime('%Y-%m-%d')}-{country}.md")
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(f"# {country}のパビリオン要約\\n\\n")
            f.write(f"**生成日時：** {datetime.now().isoformat()}\\n\\n")
            f.write(summary)

        output_data[country] = {
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        time.sleep(2)

    with open("used_pavilion_gemini.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
