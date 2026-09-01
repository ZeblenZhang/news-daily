# -*- coding: utf-8 -*-
"""
新闻源配置（已根据国内网络可达性与实时性实测筛选）。
每个源一个 dict：
  - name:     来源显示名
  - kind:     'rss' | 'html' | 'baidu_hot'
  - url:      地址
  - category: 默认分类（hot=热点, major=重大事件, trend=行业趋势）
  - subcategory: 行业趋势子分类（science/robotics/digital/industrial/construction/other）
  - lang:     'zh' | 'en'（en 保留英文原文并进入页面内阅读模式）
  - ua:       可选，自定义 User-Agent（如量子位需 Googlebot UA）
  - link_contains: 可选，仅 'html' 类使用，命中才采集（str 或 list）
  - max:      最多抓取条数

说明（用户指定的科技源中，以下 3 个暂无法自动抓取，原因见下）：
  - 中国科技网 stdaily.com  —— 首页有 JS 反爬（fec_wrapper），且无 RSS
  - 科技部   most.gov.cn    —— 首页 JS 渲染返回空壳，且无 RSS
  - 机器之心 jiqizhixin.com —— 前端 SPA 渲染，RSS 已下线，graphql API 需 token
如需补充，可另接 RSSHub 或自建抓取。
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
    # ---------- 行业趋势：科学技术（官方科研 + 学术前沿） ----------
    {
        "name": "科学网",
        "kind": "rss",
        "url": "https://www.sciencenet.cn/xml/news-0.aspx?di=1",
        "category": "trend",
        "subcategory": "science",
        "lang": "zh",
        "max": 15,
    },
    {
        "name": "中科院之声",
        "kind": "html",
        "url": "https://www.cas.cn/",
        "category": "trend",
        "subcategory": "science",
        "lang": "zh",
        # 只取科研进展(/syky/)与成果(/cg/)两类硬核科研新闻，排除导航/平台链接
        "link_contains": ["/syky/", "/cg/"],
        "max": 15,
    },
    {
        "name": "Nature",
        "kind": "rss",
        "url": "https://www.nature.com/nature.rss",
        "category": "trend",
        "subcategory": "science",
        "lang": "en",
        "max": 10,
    },
    {
        "name": "Science News",
        "kind": "rss",
        "url": "https://www.sciencenews.org/feed/",
        "category": "trend",
        "subcategory": "science",
        "lang": "en",
        "max": 10,
    },
    {
        "name": "ScienceDaily",
        "kind": "rss",
        "url": "https://www.sciencedaily.com/rss/all.xml",
        "category": "trend",
        "subcategory": "science",
        "lang": "en",
        "max": 10,
    },
    {
        "name": "arXiv·机器人学",
        "kind": "rss",
        "url": "https://rss.arxiv.org/rss/cs.RO",
        "category": "trend",
        "subcategory": "science",
        "lang": "en",
        "max": 10,
    },
    # ---------- 行业趋势：机器人AI（产业硬科技媒体） ----------
    {
        "name": "量子位",
        "kind": "rss",
        "url": "https://www.qbitai.com/feed",
        "category": "trend",
        "subcategory": "robotics",
        "lang": "zh",
        # 量子位对普通 UA 返回 403，需用 Googlebot 抓取
        "ua": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "max": 15,
    },
    {
        "name": "InfoQ中文",
        "kind": "rss",
        "url": "https://www.infoq.cn/feed",
        "category": "trend",
        "subcategory": "robotics",
        "lang": "zh",
        "max": 15,
    },
    {
        "name": "arXiv·人工智能",
        "kind": "rss",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "category": "trend",
        "subcategory": "robotics",
        "lang": "en",
        "max": 10,
    },
    {
        "name": "MIT科技评论",
        "kind": "rss",
        "url": "https://www.technologyreview.com/feed/",
        "category": "trend",
        "subcategory": "robotics",
        "lang": "en",
        "max": 10,
    },
    {
        "name": "TechCrunch",
        "kind": "rss",
        "url": "https://techcrunch.com/feed/",
        "category": "trend",
        "subcategory": "robotics",
        "lang": "en",
        "max": 10,
    },
    # ---------- 数码电子（国外主流，附英文原文） ----------
    {
        "name": "The Verge",
        "kind": "rss",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "trend",
        "subcategory": "digital",
        "lang": "en",
        "max": 15,
    },
    {
        "name": "9to5Mac",
        "kind": "rss",
        "url": "https://9to5mac.com/feed/",
        "category": "trend",
        "subcategory": "digital",
        "lang": "en",
        "max": 15,
    },
    {
        "name": "Engadget",
        "kind": "rss",
        "url": "https://www.engadget.com/rss.xml",
        "category": "trend",
        "subcategory": "digital",
        "lang": "en",
        "max": 15,
    },
    {
        "name": "CNET",
        "kind": "rss",
        "url": "https://www.cnet.com/rss/news/",
        "category": "trend",
        "subcategory": "digital",
        "lang": "en",
        "max": 15,
    },
    {
        "name": "Ars Technica",
        "kind": "rss",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "category": "trend",
        "subcategory": "digital",
        "lang": "en",
        "max": 15,
    },
    # ---------- 工业制造（国外主流，附英文原文） ----------
    {
        "name": "IEEE Spectrum",
        "kind": "rss",
        "url": "https://spectrum.ieee.org/feeds/topic/robotics.rss",
        "category": "trend",
        "subcategory": "industrial",
        "lang": "en",
        "max": 15,
    },
    # ---------- 建筑施工（国内政策/法规，优先政府源） ----------
    {
        "name": "新华网时政",
        "kind": "rss",
        "url": "http://www.xinhuanet.com/politics/news_politics.xml",
        "category": "trend",
        "subcategory": "construction",
        "lang": "zh",
        "max": 20,
    },
    # ---------- 其他：教育/趣闻（国外主流，附英文原文） ----------
    {
        "name": "Atlas Obscura",
        "kind": "rss",
        "url": "https://www.atlasobscura.com/feeds/latest",
        "category": "trend",
        "subcategory": "other",
        "lang": "en",
        "max": 10,
    },
    {
        "name": "NASA",
        "kind": "rss",
        "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "category": "trend",
        "subcategory": "other",
        "lang": "en",
        "max": 10,
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

# 行业趋势子分类（按指定顺序展示：科学技术、机器人AI、金融、数码电子、工业制造、建筑施工、其他）
TREND_SUBCATEGORY_ORDER = [
    "science",   # 科学技术
    "robotics",  # 机器人AI
    "finance",   # 金融
    "digital",   # 数码电子
    "industrial",# 工业制造
    "construction",  # 建筑施工
    "other",     # 其他
]

TREND_SUBCATEGORY_LABEL = {
    "science": "科学技术",
    "robotics": "机器人AI",
    "finance": "金融",
    "digital": "数码电子",
    "industrial": "工业制造",
    "construction": "建筑施工",
    "other": "其他",
}

# 子分类关键词规则：命中标题则归入对应子类（按顺序匹配，先命中先得）
TREND_SUBCATEGORY_RULES = [
    ("science", [
        "科学", "科研", "实验室", "太空", "航天", "天文", "量子", "核聚变",
        "基因", "生物", "医学", "物理", "化学", "材料", "论文", "研究", "突破",
        "火星", "卫星", "火箭", "望远镜",
    ]),
    ("robotics", [
        "机器人", "AI", "人工智能", "大模型", "算法", "机器学习", "深度学习",
        "自动驾驶", "人形", "具身智能", "神经网络", "chatgpt", "gpt", "llm",
        "智能体", "agent", "agi", "aigc", "生成式", "开源模型", "算力", "gpu",
    ]),
    ("finance", [
        "金融", "银行", "证券", "股票", "股市", "基金", "ETF", "债券", "期货",
        "期权", "保险", "贷款", "利率", "汇率", "投资", "融资", "IPO",
        "收购", "并购", "估值", "市值", "股价", "行情", "涨停", "跌停",
        "A股", "港股", "美股", "央行", "美联储", "加息", "降息", "通胀",
        "钱包", "支付", "信用卡", "数字货币", "区块链", "比特币",
    ]),
    ("digital", [
        "手机", "数码", "消费电子", "笔记本", "耳机", "平板", "相机", "电视",
        "智能穿戴", "手表", "芯片", "半导体", "处理器", "骁龙", "苹果", "华为",
        "小米", "三星", "显示器", "屏幕", "摄像头", "游戏", "电竞",
    ]),
    ("industrial", [
        "工业", "制造", "工厂", "机床", "自动化", "智能制造", "机械", "设备",
        "汽车", "新能源", "电池", "光伏", "风电", "储能", "供应链", "电机",
        "产线", "零部件", "钢铁", "重工", "船舶",
    ]),
    ("construction", [
        "建筑", "施工", "工程", "基建", "房地产", "楼盘", "建材", "水泥",
        "桥梁", "隧道", "公路", "高铁", "地铁", "工地", "装修", "混凝土",
        "装配式", "城市更新", "土木",
    ]),
    # "other" 为兜底，无需关键词
]


def classify_trend_subcategory(title):
    """为行业趋势条目判断子分类。"""
    t = title.lower()
    # 娱乐类泛 AI 内容优先归入「其他」，避免误入「机器人AI」
    for k in ("短剧", "综艺", "明星", "演员", "导演", "电影", "电视剧"):
        if k in t:
            return "other"
    for key, kws in TREND_SUBCATEGORY_RULES:
        if any(k.lower() in t for k in kws):
            return key
    return "other"

# 请求头，模拟浏览器
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://top.baidu.com/",
}
