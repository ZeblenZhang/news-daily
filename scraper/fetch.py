# -*- coding: utf-8 -*-
"""
抓取主脚本：遍历新闻源 -> 解析 -> 去重 -> 分类 -> 排序 -> 输出 JSON。
支持 RSS 与百度热搜 JSON API 两种来源。
可单独运行：python scraper/fetch.py
"""
import os
import re
import sys
import json
import time
import html as html_lib
from datetime import datetime, timezone, timedelta

try:
    import requests
    import feedparser
    from bs4 import BeautifulSoup
except ImportError:
    print("[warn] 缺少依赖，请先执行: pip install -r scraper/requirements.txt")
    sys.exit(1)

from sources import (
    SOURCES, KEYWORD_RULES, CATEGORY_LABEL, HEADERS,
    TREND_SUBCATEGORY_ORDER, TREND_SUBCATEGORY_LABEL, classify_trend_subcategory,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT = os.path.join(DATA_DIR, "latest.json")

BEIJING = timezone(timedelta(hours=8))

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(s):
    if not s:
        return ""
    s = html_lib.unescape(s)
    s = TAG_RE.sub("", s)
    s = WS_RE.sub(" ", s)
    return s.strip()


def truncate(s, n=120):
    s = clean_text(s)
    return s if len(s) <= n else s[:n] + "…"


def extract_real_url(url):
    """处理新浪等 redirect.php?url=xxx 形式的链接，提取真实地址。"""
    if "redirect" in url and "url=" in url:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(url).query)
        real = qs.get("url", [""])[0]
        if real:
            return real
    return url


def parse_baidu_hot(url, src):
    """解析百度热搜 JSON API。"""
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        cards = data.get("data", {}).get("cards", [])
        for card in cards:
            for block in card.get("content", []):
                # 真正的热搜条目在 block["content"] 里
                entries = block.get("content", []) if isinstance(block, dict) else []
                if not entries:
                    # 兼容某些结构下 block 本身就是条目
                    entries = [block]
                for it in entries:
                    if not isinstance(it, dict):
                        continue
                    word = clean_text(it.get("word", ""))
                    link = it.get("url", "")
                    if not word:
                        continue
                    if not link:
                        link = "https://www.baidu.com/s?wd=" + word
                    items.append(
                        {
                            "title": word,
                            "url": link,
                            "summary": "",
                            "source": src["name"],
                            "category": src["category"],
                            "lang": "zh",
                        }
                    )
                    if len(items) >= src.get("max", 40):
                        return items
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 百度热搜抓取失败: {exc}")
    return items


def parse_rss(url, src):
    """解析 RSS，返回条目列表（带一次重试，应对偶发限流）。"""
    items = []
    max_items = src.get("max", 30)
    feed = None
    for attempt in range(2):
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                break
            time.sleep(2)  # 首次为空则稍候重试
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] RSS 解析失败 {url} (第{attempt+1}次): {exc}")
            time.sleep(2)
    if feed is None or not feed.entries:
        return items
    for e in feed.entries[:max_items]:
        title = clean_text(
            getattr(e, "title", "")
            or getattr(e, "atitle", "")
            or (e.get("title_detail", {}) or {}).get("value", "")
        )
        link = getattr(e, "link", "") or getattr(e, "htmlurl", "") or getattr(e, "url", "")
        summary = truncate(
            getattr(e, "summary", "") or getattr(e, "description", ""), 160
        )
        if not title or not link:
            continue
        lang = src.get("lang", "zh")
        item = {
            "title": title,
            "url": extract_real_url(link),
            "summary": summary,
            "source": src["name"],
            "category": src["category"],
            "lang": lang,
        }
        # 国外源：保留英文原文标题/摘要，并提取完整正文（供页面内阅读模式，规避广告/会员墙）
        if lang == "en":
            item["title_en"] = title
            item["summary_en"] = summary
            full = extract_full_content(e)
            if full:
                item["content_en"] = full
        items.append(item)
    return items


def extract_full_content(entry):
    """从 RSS 条目提取完整正文（优先 content 字段，其次 summary/description）。"""
    # 优先 content（feedparser 里是 list）
    content = entry.get("content")
    if content:
        val = content[0].get("value", "") if isinstance(content, list) and content else ""
        if val:
            cleaned = clean_text(val)
            if len(cleaned) > 120:
                return cleaned
    # 其次 summary/description 的完整原文（非截断版）
    raw = entry.get("summary", "") or entry.get("description", "")
    cleaned = clean_text(raw)
    if len(cleaned) > 200:
        return cleaned
    return ""


def classify(title, default_cat):
    """按关键词规则调整分类。"""
    t = title.lower()
    for cat, kws in KEYWORD_RULES.items():
        if any(k.lower() in t for k in kws):
            return cat
    return default_cat


def dedup(items):
    """按 URL 去重；URL 相同时按标题去重。"""
    seen_url = set()
    seen_title = set()
    result = []
    for it in items:
        u = it["url"]
        if u and u in seen_url:
            continue
        if it["title"] in seen_title:
            continue
        if u:
            seen_url.add(u)
        seen_title.add(it["title"])
        result.append(it)
    return result


def main():
    all_items = []
    for src in SOURCES:
        name = src["name"]
        try:
            if src["kind"] == "baidu_hot":
                items = parse_baidu_hot(src["url"], src)
            elif src["kind"] == "rss":
                items = parse_rss(src["url"], src)
            else:
                items = []
            for it in items:
                it["category"] = classify(it["title"], src["category"])
                # 源显式指定子分类时优先采用（如 The Verge -> digital）
                if src.get("subcategory"):
                    it["subcategory"] = src["subcategory"]
            print(f"[ok] {name}: {len(items)} 条")
            all_items.extend(items)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {name} 抓取失败: {exc}")

    all_items = dedup(all_items)

    # 为行业趋势条目打子分类标签（仅对未指定子分类的条目按关键词兜底）
    for it in all_items:
        if it.get("category") == "trend" and "subcategory" not in it:
            it["subcategory"] = classify_trend_subcategory(it["title"])

    # 排序：重大事件 > 热点 > 行业趋势；行业趋势内按子分类顺序排序
    order = {"major": 0, "hot": 1, "trend": 2}
    suborder = {k: i for i, k in enumerate(TREND_SUBCATEGORY_ORDER)}

    def sort_key(x):
        cat = x.get("category", "hot")
        base = order.get(cat, 3)
        if cat == "trend":
            return (base, suborder.get(x.get("subcategory", "other"), 99))
        return (base, 0)

    all_items.sort(key=sort_key)

    # 截断：重大 20、热点 30；行业趋势按子分类分配名额，且中英文均衡
    limits = {"major": 20, "hot": 30}
    # 每个 trend 子分类的上限
    trend_sub_limits = {
        "science": 8, "robotics": 12, "finance": 6, "digital": 14,
        "industrial": 10, "construction": 8, "other": 12,
    }
    # 每个子分类内英文条目至少保留的条数
    en_floor = {
        "digital": 6, "industrial": 5, "other": 8,
    }
    buckets = {"major": [], "hot": [], "trend": []}
    trend_sub_count = {}
    trend_sub_en_count = {}

    # 先填 major / hot
    for it in all_items:
        cat = it.get("category", "hot")
        if cat != "trend":
            if len(buckets.get(cat, [])) < limits.get(cat, 20):
                buckets.setdefault(cat, []).append(it)

    # 填 trend：英文条目按「源」轮询插入（保证每个英文源都能进入）
    trend_items = [it for it in all_items if it.get("category") == "trend"]
    en_items = [it for it in trend_items if it.get("lang") == "en"]
    zh_items = [it for it in trend_items if it.get("lang") != "en"]

    # 按子分类分组英文条目，组内按源轮询
    from collections import defaultdict
    en_by_sub = defaultdict(list)
    for it in en_items:
        en_by_sub[it.get("subcategory", "other")].append(it)

    def insert(item):
        sub = item.get("subcategory", "other")
        cap = trend_sub_limits.get(sub, 6)
        if trend_sub_count.get(sub, 0) < cap:
            buckets["trend"].append(item)
            trend_sub_count[sub] = trend_sub_count.get(sub, 0) + 1
            return True
        return False

    # 英文：轮询各源，直到每个子类的英文名额用完
    sub_en_sources = {}
    for sub, items in en_by_sub.items():
        sub_en_sources[sub] = defaultdict(list)
        for it in items:
            sub_en_sources[sub][it["source"]].append(it)
    # 轮询插入
    for sub in TREND_SUBCATEGORY_ORDER:
        if sub not in sub_en_sources:
            continue
        floor = en_floor.get(sub, 0)
        source_lists = list(sub_en_sources[sub].values())
        # 轮询：每轮从每个源取一条
        idx = [0] * len(source_lists)
        inserted = 0
        while inserted < floor:
            progressed = False
            for i, sl in enumerate(source_lists):
                if idx[i] < len(sl):
                    if trend_sub_en_count.get(sub, 0) < floor:
                        insert(sl[idx[i]])
                        trend_sub_en_count[sub] = trend_sub_en_count.get(sub, 0) + 1
                        inserted += 1
                        idx[i] += 1
                        progressed = True
            if not progressed:
                break

    # 中文：填充剩余名额
    for it in zh_items:
        insert(it)

    final = buckets["major"] + buckets["hot"] + buckets["trend"]

    now = datetime.now(BEIJING)
    result = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "date_cn": now.strftime("%Y年%m月%d日"),
        "weekday": "星期" + "一二三四五六日"[now.weekday()],
        "total": len(final),
        "categories": CATEGORY_LABEL,
        "trend_subcategories": TREND_SUBCATEGORY_LABEL,
        "trend_subcategory_order": TREND_SUBCATEGORY_ORDER,
        "items": final,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n完成：共 {len(final)} 条 -> {OUTPUT}")


if __name__ == "__main__":
    main()
