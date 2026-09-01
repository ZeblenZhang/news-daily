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


def clean_arxiv_meta(s):
    """去除 arXiv RSS 摘要/正文里的元数据前缀（arXiv 编号、Announce Type、Abstract 标签）。"""
    if not s:
        return ""
    s = re.sub(r"arXiv:\S+\s*", "", s)
    s = re.sub(r"Announce Type:\s*\S+\s*", "", s)
    s = re.sub(r"^Abstract:\s*", "", s.strip())
    return s.strip()


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


def normalize_link(base_url, href):
    """把相对/协议相对/含 ../ 的链接规范化为绝对 URL。"""
    from urllib.parse import urljoin, urlparse
    import posixpath
    href = (href or "").strip()
    if not href or href.startswith("javascript:"):
        return ""
    if href.startswith("//"):
        href = "https:" + href
    joined = urljoin(base_url, href)
    parsed = urlparse(joined)
    path = posixpath.normpath(parsed.path)
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def parse_html_list(url, src):
    """通用 HTML 列表抓取：提取含指定特征（link_contains）的链接及其标题。
    用于无 RSS 的站点（如中科院官网），标题优先取 title 属性，其次取锚文本。
    link_contains 可为字符串（命中即采）或字符串列表（命中任一即采）。"""
    items = []
    link_contains = src.get("link_contains", "")
    if isinstance(link_contains, str):
        link_contains = [link_contains]
    link_contains = [c for c in link_contains if c]
    max_items = src.get("max", 15)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if not (resp.encoding and resp.encoding.lower().startswith("utf")):
            resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if link_contains and not any(c in href for c in link_contains):
                continue
            title = clean_text(a.get("title", "") or a.get_text(strip=True))
            if not title or len(title) < 6:
                continue
            link = normalize_link(url, href)
            if not link or link in seen:
                continue
            seen.add(link)
            items.append(
                {
                    "title": title,
                    "url": link,
                    "summary": "",
                    "source": src["name"],
                    "category": src["category"],
                    "lang": src.get("lang", "zh"),
                }
            )
            if len(items) >= max_items:
                break
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] HTML 抓取失败 {url}: {exc}")
    return items


def _feed_to_parse(url, src):
    """获取 feed 内容：源指定了自定义 UA 时用 requests 抓取后交给 feedparser，否则直接解析。"""
    custom_ua = src.get("ua")
    if not custom_ua:
        return url
    headers = dict(HEADERS)
    headers["User-Agent"] = custom_ua
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        return resp.content
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 自定义 UA 抓取失败 {url}: {exc}")
        return url


def parse_rss(url, src):
    """解析 RSS，返回条目列表（带一次重试，应对偶发限流）。"""
    items = []
    max_items = src.get("max", 30)
    feed = None
    feed_input = _feed_to_parse(url, src)
    for attempt in range(2):
        try:
            feed = feedparser.parse(feed_input)
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
        # arXiv：去除摘要/正文里的元数据前缀（如 "arXiv:2608.28656v1 Announce Type: new Abstract:"）
        if src["name"].startswith("arXiv"):
            summary = clean_text(clean_arxiv_meta(summary))
            summary = truncate(summary, 160)
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
            if src["name"].startswith("arXiv") and full:
                full = clean_arxiv_meta(full)
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
            elif src["kind"] == "html":
                items = parse_html_list(src["url"], src)
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
        "science": 12, "robotics": 14, "finance": 6, "digital": 14,
        "industrial": 8, "construction": 8, "other": 10,
    }
    # 每个子分类内英文条目至少保留的条数
    en_floor = {
        "science": 5, "robotics": 6, "digital": 6, "industrial": 4, "other": 6,
    }
    # 每个子分类内中文条目至少保留的条数（保证官方中文源如科学网/中科院有稳定曝光）
    zh_floor = {
        "science": 5, "robotics": 5,
    }
    buckets = {"major": [], "hot": [], "trend": []}
    trend_sub_count = {}

    # 先填 major / hot
    for it in all_items:
        cat = it.get("category", "hot")
        if cat != "trend":
            if len(buckets.get(cat, [])) < limits.get(cat, 20):
                buckets.setdefault(cat, []).append(it)

    # 填 trend：中英文均按「源」轮询插入，保证每个源都能进入且语言均衡
    trend_items = [it for it in all_items if it.get("category") == "trend"]

    # 过滤纯行政/公示类噪声（如基金资助公示、论坛通知），保留真正的科技进展
    ADMIN_NOISE = ("公示", "名单", "拟资助", "双清论坛")
    trend_items = [it for it in trend_items if not any(k in it["title"] for k in ADMIN_NOISE)]

    from collections import defaultdict

    def insert(item):
        sub = item.get("subcategory", "other")
        cap = trend_sub_limits.get(sub, 6)
        if trend_sub_count.get(sub, 0) < cap:
            buckets["trend"].append(item)
            trend_sub_count[sub] = trend_sub_count.get(sub, 0) + 1
            return True
        return False

    # 按子分类 -> 语言 -> 源 分组
    by_sub = defaultdict(lambda: {"en": defaultdict(list), "zh": defaultdict(list)})
    for it in trend_items:
        sub = it.get("subcategory", "other")
        lang = "en" if it.get("lang") == "en" else "zh"
        by_sub[sub][lang][it["source"]].append(it)

    for sub in TREND_SUBCATEGORY_ORDER:
        if sub not in by_sub:
            continue
        en_floor_n = en_floor.get(sub, 0)
        zh_floor_n = zh_floor.get(sub, 0)
        en_src = list(by_sub[sub]["en"].values())  # 每个元素是一个源的条目列表
        zh_src = list(by_sub[sub]["zh"].values())

        # 1) 英文保底：轮询英文源直到满足 en_floor
        en_idx = [0] * len(en_src)
        en_count = 0
        while en_count < en_floor_n:
            progressed = False
            for i, sl in enumerate(en_src):
                if en_idx[i] < len(sl) and en_count < en_floor_n:
                    insert(sl[en_idx[i]])
                    en_idx[i] += 1
                    en_count += 1
                    progressed = True
            if not progressed:
                break

        # 2) 中文保底：轮询中文源直到满足 zh_floor
        zh_idx = [0] * len(zh_src)
        zh_count = 0
        while zh_count < zh_floor_n:
            progressed = False
            for i, sl in enumerate(zh_src):
                if zh_idx[i] < len(sl) and zh_count < zh_floor_n:
                    insert(sl[zh_idx[i]])
                    zh_idx[i] += 1
                    zh_count += 1
                    progressed = True
            if not progressed:
                break

        # 3) 剩余名额：中文源与英文源（接续）一起轮询
        all_src = zh_src + en_src
        all_idx = [0] * len(all_src)
        for i in range(len(zh_src), len(all_src)):
            all_idx[i] = en_idx[i - len(zh_src)]
        for i in range(len(zh_src)):
            all_idx[i] = zh_idx[i]
        while True:
            progressed = False
            for i, sl in enumerate(all_src):
                if all_idx[i] < len(sl):
                    insert(sl[all_idx[i]])
                    all_idx[i] += 1
                    progressed = True
            if not progressed:
                break

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
