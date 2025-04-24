import os
import json
import random
from datetime import datetime
from pathlib import Path
import requests
import google.generativeai as genai

# APIキー取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# 検索実行（SerpAPI）
def search_twitter_comments(country):
    query = f"site:twitter.com 万博2025 {country} パビリオン"
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "num": 10,
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()
    results = []

    for res in data.get("organic_results", []):
        title = res.get("title", "")
        snippet = res.get("snippet", "")
        link = res.get("link", "")
        results.append(f"- {title}\n  {snippet}\n  {link}")

    return results

# Gemini記事生成
def generate_blog_from_results(country, search_results):
    search_summary = "\n".join(search_results)
    prompt = f"""
以下の検索結果に基づいて、2025年大阪・関西万博に出展する「{country}パビリオン」について、SNS上での口コミや文化的魅力を3000字程度のブログ記事にまとめてください。
Markdown形式で、コメント引用部分と解説を分けて見やすく構成してください。
・WEBに公開されている写真があればリンクを埋め込んでください。
・まだ公開されてない場合はWEBから予想図の写真をリンク貼り付けしてください。
検索結果:
{search_summary}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# 使用済み管理
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

# ランダム国処理
country = random.choice(remaining_countries)
safe_title = country.replace("・", "").replace("（", "").replace("）", "").replace(" ", "")
results = search_twitter_comments(country)
content = generate_blog_from_results(country, results)

# 保存
post_path = posts_dir / f"{datetime.now().strftime('%Y-%m-%d')}-{safe_title}.md"
with open(post_path, "w", encoding="utf-8") as f:
    f.write(content)

# 使用済み記録
used_data["used"].append(country)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(used_data, f, ensure_ascii=False, indent=2)

print(f"{country} の記事を生成しました。")
