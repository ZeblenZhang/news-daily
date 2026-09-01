# -*- coding: utf-8 -*-
"""
组装脚本：调用抓取（可选）-> 读取 latest.json -> 注入模板 -> 生成 index.html。
用法：
  python build.py          # 抓取 + 生成
  python build.py --no-fetch  # 仅用现有 data/latest.json 生成
"""
import os
import sys
import json
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "latest.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "template", "index.html")
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")
BRIEF_TEMPLATE = (
    "今日为您精选 {total} 条要闻：{major} 条重大事件、{hot} 条热点、{trend} 条行业趋势，"
    "点击标题即可跳转原文阅读。"
)


def run_fetch():
    print(">> 抓取新闻源 ...")
    r = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "scraper", "fetch.py")],
        cwd=BASE_DIR,
    )
    if r.returncode != 0:
        print("[error] 抓取失败，退出")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true", help="跳过抓取，仅用现有数据生成")
    args = parser.parse_args()

    if not args.no_fetch:
        run_fetch()

    if not os.path.exists(DATA_FILE):
        print(f"[error] 找不到 {DATA_FILE}，请先运行抓取")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 生成导读摘要
    counts = {"major": 0, "hot": 0, "trend": 0}
    for it in data.get("items", []):
        counts[it.get("category", "hot")] = counts.get(it.get("category", "hot"), 0) + 1
    data["brief"] = BRIEF_TEMPLATE.format(
        total=data.get("total", len(data.get("items", []))),
        major=counts["major"],
        hot=counts["hot"],
        trend=counts["trend"],
    )

    # 抓取背景图（自然风光 + 宇宙星空）
    try:
        sys.path.insert(0, os.path.join(BASE_DIR, "scraper"))
        from background import get_backgrounds
        data["backgrounds"] = get_backgrounds()
        print(f">> 背景图：白天 {len(data['backgrounds']['day'])} 张 / 夜晚 {len(data['backgrounds']['night'])} 张")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 背景图抓取失败（不影响主流程）: {exc}")
        data["backgrounds"] = {"day": [], "night": []}

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    data_json = json.dumps(data, ensure_ascii=False)
    html = template.replace("__DATA__", data_json)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f">> 生成完成 -> {OUTPUT_FILE}  (共 {data['total']} 条)")


if __name__ == "__main__":
    main()
