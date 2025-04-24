import os
import json
from datetime import datetime
from pathlib import Path
import random
import google.generativeai as genai

# Gemini APIキーの読み込み
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# モデルの初期化
model = genai.GenerativeModel("gemini-1.5-flash")

def get_twitter_comments(country):
    prompt = f"""
次の条件でTwitterから情報を集めてください。

・2025年大阪・関西万博に出展している「{country}パビリオン」について実際に言及しているTwitter投稿を検索し、そのまま日本語で5件引用してください。
・引用元が不明な場合は想定ではなく実際にありそうな自然な文体で、Twitter風に仕立ててください。
・出力形式は「- コメント内容（@ユーザー名）」としてください。
"""
    response = model.generate_content(prompt)
    return [line.strip() for line in response.text.strip().split("\n") if line.strip().startswith("-")]

def generate_blog_content(country, comments):
    comment_section = "\n".join(comments)
    prompt = f"""
以下のTwitterコメントを引用して、2025年大阪・関西万博の「{country}パビリオン」について、魅力や文化的背景、注目の体験、建築デザイン、展示内容などを紹介するブログ記事をMarkdown形式で作成してください。

# コメント一覧
{comment_section}

# 出力形式
・見出し付きMarkdown
・3000字程度
・コメントはそのまま引用として掲載し、それを踏まえた構成としてください
"""
    response = model.generate_content(prompt)
    return response.text.strip()


# 使用済みリストの読み込みと更新
json_path = Path(__file__).parent / "used_pavilion_gemini.json"
with open(json_path, "r", encoding="utf-8") as f:
    used_data = json.load(f)

# 全国家リストの読み込み（別ファイルとして管理）
with open(Path(__file__).parent / "all_countries.json", "r", encoding="utf-8") as f:
    all_data = json.load(f)
all_countries = set(all_data["countries"])
used_countries = set(used_data["used"])
remaining_countries = list(all_countries - used_countries)

if not remaining_countries:
    print("すべての国のパビリオンが生成済みです。")
    exit()

# 国を1つ選んで記事生成
country = random.choice(remaining_countries)
safe_title = country.replace("・", "").replace("（", "").replace("）", "")
comments = get_twitter_comments(country)
content = generate_blog_content(country, comments)

root_dir = Path(os.getcwd())  # 実行時カレントディレクトリに合わせる
posts_dir = root_dir / "_posts"
posts_dir.mkdir(parents=True, exist_ok=True)

# ファイル書き出し
post_path = posts_dir / f"{datetime.now().strftime('%Y-%m-%d')}-{safe_title}.md"
with open(post_path, "w", encoding="utf-8") as f:
    f.write(content)

# 使用履歴を更新
used_data["used"].append(country)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(used_data, f, ensure_ascii=False, indent=2)

print(f"{country} の記事を生成しました。")
