---
layout: home
title: 実在した名馬の図鑑ブログ
---

<h1>🏇 名馬図鑑ブログ</h1>
<p>毎日1頭、実在した名馬の魅力をたっぷり紹介します。</p>

<div class="posts">
  {% for post in site.posts %}
    <article style="margin-bottom: 2em; padding: 1em; border: 1px solid #ccc; border-radius: 10px;">
      <h2><a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a></h2>
      <p><small>{{ post.date | date: "%Y年%m月%d日" }}</small></p>
      <p>{{ post.description }}</p>
    </article>
  {% endfor %}
</div>
