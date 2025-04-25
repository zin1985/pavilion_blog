
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
        return soup.get_text(separator="\n", strip=True)
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
            "num": 10
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
                summaries.append(f"【{title}】\n{body[:1000]}")

    # HTML本文保存
    os.makedirs("search_logs/html_texts", exist_ok=True)
    with open(f"search_logs/html_texts/{country}.json", "w", encoding="utf-8") as f:
        json.dump(all_html, f, ensure_ascii=False, indent=2)

    return "\n\n".join(summaries)

# Gemini要約
def generate_summary_from_html(text):
    try:
        prompt = f"以下の検索結果に基づいて、2025年大阪・関西万博に出展する「{country}パビリオン」について、SNS上での口コミや文化的魅力、展示の特徴などを3000字程度で紹介するブログ記事をMarkdown形式で作成してください。引用部分と解説を分け、読者が理解しやすい構成にしてください。\n\n{text}"
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
        print(f"$D83D$DFE1 {country} を処理中...")
        body_text = search_google_with_scrape(country)
        summary = generate_summary_from_html(body_text)
        output_data[country] = {
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        time.sleep(2)

    with open("used_pavilion_gemini.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
