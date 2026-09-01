# 今日世界要闻 · Daily News Briefing

一个每天**北京时间 10 点前**自动更新的新闻页面。浏览器打开即读，内容覆盖**热点、重大事件、行业趋势**三类，排版精美简洁。

_A news page that updates automatically before 10:00 AM Beijing time every day. Open it in a browser and read instantly, covering **hot topics, major events, and industry trends**, with a clean and elegant layout._

## 效果 / Features

- 顶部显示日期 + 今日导读摘要 — _Date + daily briefing summary at the top_
- 标签页筛选：`全部 / 热点 / 重大事件 / 行业趋势` — _Tab filtering: `All / Hot / Major Events / Industry Trends`_
- 卡片式新闻块，标题 + 摘要 + 原文链接（点击跳转原站）— _Card-based news blocks with title + summary + source link (click to open the original article)_
- 响应式设计，手机 / 桌面自适应 — _Responsive design, adapts to mobile / desktop_

## 本地运行 / Run Locally

```bash
# 1. 安装依赖 / Install dependencies
pip install -r scraper/requirements.txt

# 2. 抓取 + 生成页面 / Fetch + build the page
python build.py

# 3. 打开生成的 index.html 即可浏览 / Open the generated index.html to browse
```

> 若网络抓取受限，可先运行 `python build.py --no-fetch` 用已有缓存生成页面。
> _If network fetching is restricted, run `python build.py --no-fetch` to build the page from the existing cache._

## 部署到 GitHub Pages（纯网页操作，最简单）/ Deploy to GitHub Pages (Web-only, Simplest)

> 全程无需命令行。假设你的代码已经上传到 GitHub 仓库，只需做下面两步。

### 第一步：把 Source 设为 GitHub Actions（最关键，最容易出错）

1. 打开你的仓库页面，点顶部菜单 **Settings**。
2. 左侧栏找到并点击 **Pages**。
3. 在 **Build and deployment** 区域，找到 **Source** 下拉框。
4. **务必选择 `GitHub Actions`**（不是 `Deploy from a branch`！选错会导致网址打不开 404）。
5. 选择后页面会自动保存，无需点别的按钮。

### 第二步：手动跑一次工作流

1. 点仓库顶部菜单 **Actions**。
2. 左侧列表找到 **Daily News Update**。
3. 右侧点 **Run workflow**（下拉里保持默认 `main` 分支，再点绿色的 **Run workflow** 按钮确认）。
4. 等待约 1~2 分钟，圆点变绿 ✓ 即成功。

### 第三步：访问

- 地址是：`https://<你的用户名>.github.io/<仓库名>/`
- 仓库名是 `news-daily`，就是 `https://<你的用户名>.github.io/news-daily/`

---

### ⚠️ 网址还是打不开？对照排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 显示 404 | Source 选了分支而非 Actions | 回 Settings → Pages，把 Source 改成 **GitHub Actions** |
| 显示 404 | 仓库名带大写字母/特殊字符 | 网址里的仓库名要和实际完全一致（区分大小写），或用 Settings → Pages 页面顶部显示的绿色网址 |
| Actions 变红 ✗ | 抓取或构建失败 | 点开失败的工作流，看具体哪一步报错，把截图/报错发给我 |
| 页面空白 | 首次部署还没完成 | 等 1~2 分钟再刷新，或去 Actions 确认绿 ✓ 后再访问 |

> 最可靠的办法：到 **Settings → Pages** 页面顶部，GitHub 会显示一个**绿色的「Your site is live at ...」**网址，直接点那个网址就是对的。

### 之后每天自动更新

工作流已配置每天北京时间 09:30 自动运行（UTC 01:30），无需再手动操作。想立即更新就重复「第二步」手动跑一次。

## 手动触发 / Manual Trigger

仓库 `Actions` 页 → 选择 `Daily News Update` → `Run workflow`。
_On the repository's `Actions` page → select `Daily News Update` → `Run workflow`._

## 目录结构 / Directory Structure

```
news-daily/
├── scraper/
│   ├── fetch.py          # 抓取主脚本（RSS/HTML、去重、分类）/ Main scraper (RSS/HTML, dedup, classification)
│   ├── sources.py        # 新闻源与关键词分类规则 / News sources and keyword classification rules
│   └── requirements.txt
├── template/index.html   # 页面模板 / Page template
├── build.py              # 组装数据 → 生成 index.html / Assemble data → generate index.html
├── data/latest.json      # 抓取结果缓存 / Fetched result cache
├── .github/workflows/daily.yml  # 定时任务 / Scheduled job
└── index.html            # 最终产物 / Final output
```

## 自定义 / Customization

- **增删新闻源**：编辑 `scraper/sources.py` 的 `SOURCES` 列表（支持 RSS 与 HTML 两种）。
  **Add/remove sources**: edit the `SOURCES` list in `scraper/sources.py` (supports both RSS and HTML).
- **调整分类**：编辑 `sources.py` 的 `KEYWORD_RULES` 关键词。
  **Adjust classification**: edit the `KEYWORD_RULES` keywords in `sources.py`.
- **修改版式**：编辑 `template/index.html` 中的 CSS。
  **Modify layout**: edit the CSS in `template/index.html`.
