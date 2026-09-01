# -*- coding: utf-8 -*-
"""
背景图抓取：从 Bing 每日壁纸获取自然风光图；星空图从 Bing 筛选 + 固定太空图兜底。
供 build.py 调用，生成 background 数据注入前端。
"""
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

# 星空类关键词（用于从 Bing 标题/版权里筛出宇宙星空图）
SPACE_KW = [
    "极光", "星空", "银河", "星云", "星系", "宇宙", "星轨", "流星",
    "彗星", "日食", "月食", "月球", "aurora", "galaxy", "nebula",
    "milky way", "starry", "夜空", "star", "astron",
]

# 固定太空图兜底（NASA / 公共图库，确保夜晚星空类永远有图）
SPACE_FALLBACK = [
    "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1920&q=80",
    "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920&q=80",
    "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?w=1920&q=80",
    "https://images.unsplash.com/photo-1465101162946-4377e57745c3?w=1920&q=80",
    "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1920&q=80",
    "https://images.unsplash.com/photo-1470813740244-df37b8c1edcb?w=1920&q=80",
]


def fetch_bing_images(n_days=3):
    """从 Bing 每日壁纸抓取自然风光 + 星空图，返回 (nature, space) 两个列表。"""
    nature = []
    space = []
    for idx in range(n_days):
        url = (
            "https://www.bing.com/HPImageArchive.aspx"
            f"?format=js&idx={idx * 8}&n=8&mkt=zh-CN"
        )
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            data = r.json()
        except Exception:
            continue
        for img in data.get("images", []):
            base = img.get("urlbase", "")
            if not base:
                continue
            full = "https://www.bing.com" + base + "_1920x1080.jpg"
            title = img.get("title", "")
            copyright_ = img.get("copyright", "")
            text = title + " " + copyright_
            is_space = any(k.lower() in text.lower() for k in SPACE_KW)
            if is_space:
                space.append(full)
            else:
                nature.append(full)
    return nature, space


def get_backgrounds():
    """获取背景图数据，返回 dict：{ 'day': [url...], 'night': [url...] }。"""
    nature, space = fetch_bing_images()
    # 去重
    nature = list(dict.fromkeys(nature))
    space = list(dict.fromkeys(space))
    # 星空图太少时用兜底图补足
    if len(space) < 4:
        for u in SPACE_FALLBACK:
            if u not in space:
                space.append(u)
            if len(space) >= 8:
                break
    # 自然图太少时也用兜底（复用自然风光图）
    if len(nature) < 4:
        nature.extend([
            "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1920&q=80",
            "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920&q=80",
            "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920&q=80",
        ])
    return {
        "day": nature[:12],
        "night": space[:12],
    }
