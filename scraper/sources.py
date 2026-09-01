# -*- coding: utf-8 -*-
"""
新闻源配置（已根据国内网络可达性与实时性实测筛选）。
每个源一个 dict：
  - name:     来源显示名
  - kind:     'rss' | 'baidu_hot'（百度热搜 JSON API）
  - url:      地址
  - category: 默认分类（hot=热点, major=重大事件, trend=行业趋势）
  - max:      最多抓取条数
"""

SOURCES = [
    # ---------- 热点（百度热搜，实时） ----------
    {
        "name": "百度热搜",
        "kind": "baidu_hot",
        "url": "https://top.baidu.com/api/board?platform=wise&tab=realtime",
        "category": "hot",
        "max": 40,
    },
    # ---------- 综合要闻（界面新闻，实时，覆盖财经/宏观/国际） ----------
    {
        "name": "界面新闻",
        "kind": "rss",
        "url": "https://a.jiemian.com/index.php?m=article&a=rss",
        "category": "major",
        "max": 30,
    },
    # ---------- 行业趋势 ----------
    {
        "name": "InfoQ中文",
        "kind": "rss",
        "url": "https://www.infoq.cn/feed",
        "category": "trend",
        "max": 20,
    },
    {
        "name": "爱范儿",
        "kind": "rss",
        "url": "https://www.ifanr.com/feed",
        "category": "trend",
        "max": 20,
    },
]

# 关键词规则：命中标题则覆盖/提升为对应分类
KEYWORD_RULES = {
    "major": [
        "战争", "冲突", "制裁", "选举", "总统", "总理", "峰会", "地震", "疫情",
        "灾难", "空难", "爆炸", "谈判", "协议", "撤军", "政变", "危机", "联合国",
        "美联储", "加息", "降息", "通胀", "关税", "禁令", "核", "导弹", "国际",
        "访华", "会晤", "外交", "恐袭", "袭击", "遇难", "事故", "坠毁",
    ],
    "trend": [
        "AI", "人工智能", "大模型", "芯片", "半导体", "新能源", "电动车", "自动驾驶",
        "机器人", "云计算", "区块链", "元宇宙", "融资", "上市", "IPO", "收购", "并购",
        "科技", "互联网", "数据", "算法", "电池", "光伏", "智能", "5G", "卫星",
        "芯片", "模型", "GPU", "开源",
    ],
    "hot": [
        "热搜", "突发", "最新", "官方", "回应", "通报", "调查", "曝光", "争议",
        "辟谣", "涨价", "降价", "政策", "新规", "发布",
    ],
}

CATEGORY_LABEL = {
    "hot": "热点",
    "major": "重大事件",
    "trend": "行业趋势",
}

# 请求头，模拟浏览器
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://top.baidu.com/",
}
