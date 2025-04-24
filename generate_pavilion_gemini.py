import os
import json
import random
from datetime import datetime
from pathlib import Path
import requests
import google.generativeai as genai

# APIキーとSearch Engine ID
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_SEARCH_CX")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# PSE検索実行 + JSON記録
def search_google_pse(country):
    search_terms = ["パビリオン", "食事", "キャラクター", "イベント"]
    combined_results = []
    raw_data = {}

    for term in search_terms:
        query = f"万博2025 {country} {term}"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_SEARCH_CX,
            "q": query,
            "num": 5,
        }
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        data = response.json()
        raw_data[term] = data

        for item in data.get("items", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            combined_results.append(f"- {title}\n  {snippet}\n  {link}")

    # 検索結果のJSON保存
    timestamp = datetime.now().strftime("%Y%m%d%H:%M:%S")
    log_dir = Path(os.getcwd()) / "search_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / f"{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    return combined_results

# Geminiブログ記事生成
def generate_blog_from_results(country, search_results):
    search_summary = "\n".join(search_results)
    prompt = f"""
以下の検索結果に基づいて、2025年大阪・関西万博に出展する「{country}パビリオン」について、SNS上での口コミや文化的魅力、展示の特徴などを3000字程度で紹介するブログ記事をMarkdown形式で作成してください。
引用部分と解説を分け、読者が理解しやすい構成にしてください。

検索結果:
{search_summary}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# 使用済み管理と記事出力
root_dir = Path(os.getcwd())
json_path = root_dir / "used_pavilion_gemini.json"
all_path = root_dir / "all_countries.json"
posts_dir = root_dir / "_posts"
posts_dir.mkdir(parents=True, exist_ok=True)

with open(json_path, "r", encoding="utf-8") as f:
    used_data = json.load(f)
with open(all_path, "r", encoding="utf-8") as f:
    all_data = json.load(f)

all_countries = set(all_data["countries"])
used_countries = set(used_data["used"])
remaining_countries = list(all_countries - used_countries)

if not remaining_countries:
    print("すべての国が処理済みです。")
    exit()

# ランダム国選出と記事生成
country = random.choice(remaining_countries)
safe_title = country.replace("・", "").replace("（", "").replace("）", "").replace(" ", "")
results = search_google_pse(country)
content = generate_blog_from_results(country, results)

# Markdown保存
post_path = posts_dir / f"{datetime.now().strftime('%Y-%m-%d')}-{safe_title}.md"
with open(post_path, "w", encoding="utf-8") as f:
    f.write(content)

# 使用済み国の記録
used_data["used"].append(country)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(used_data, f, ensure_ascii=False, indent=2)

print(f"{country} の記事を生成しました。")
