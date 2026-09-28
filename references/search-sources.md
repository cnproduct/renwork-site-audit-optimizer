# 官方来源与时效

核对基准日期：2026-09-28。下列来源是可更新的依据；使用时重新查看页面修订时间和适用性，把检查日期/链接/结论写入本次证据。账号功能以实际可见界面为准，不从旧报告名称推测新能力。

| 来源 | 用于本 Skill 的判断 |
|---|---|
| [Google Trends 数据口径](https://support.google.com/trends/answer/4365533?hl=en) | 抽样与归一化；0–100 是相对兴趣，不是搜索量或订单。 |
| [Google Trends related searches](https://support.google.com/trends/answer/4355000?hl=en) | 区分 Top/Rising；Breakout 对应增长超过 5000%，不能与普通 +320% 标注混用。 |
| [Pinterest Trends 官方说明](https://help.pinterest.com/en/business/article/pinterest-trends) | 区分搜索、收藏、购物与预测，记录地区/受众/时间筛选；功能因地区与账号而异。 |
| [Google AI Search 报告](https://support.google.com/webmasters/answer/16984139) | 当前文档列本站 AI 展示及页面/国家/日期/设备等口径；按实有字段导出，不虚构全市场 AI 查询量。 |
| [Bing AI Visibility：Intents、Topics、Citation Share、Compare](https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/) | 主题与意图用于内容缺口观察；引用份额不是流量份额或内容质量分，是否可见以实际账号为准。 |
| [Google AI features and your website](https://developers.google.com/search/docs/appearance/ai-features) | Google AI 搜索沿用基本 SEO；符合资格不保证索引/展示，不要求特殊 AI 文件或专用 Schema。正文可发现、真实、有用才是优化对象。 |
| [Google canonical](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) | 规范 URL 是信号协调问题；根据重复页面/实际站点意图判断，不把一律自指 canonical 当修复。 |
| [Google structured data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) | 标记需匹配可见内容且满足适用政策；语法有效不能保证富结果。 |
| [Google 搜索更新](https://developers.google.com/search/updates) | 开工时核对 FAQ、Product 等功能当前支持情况；不因 JSON 里写入某类型就承诺富结果。 |
| [Google Search Console 帮助](https://support.google.com/webmasters/) | 核验当前账号实际报告、URL 检查和时间窗；细分 AI 数据是否存在/可用需现场确认，不能编造查询维度或独立 CTR。 |
| [OpenAI crawlers](https://developers.openai.com/api/docs/bots) | 搜索爬虫、训练爬虫和用户触发请求用途不同；不要把允许 GPTBot 当成获 ChatGPT 引用的必要条件。 |
| [Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) | 按官方用途和实际访问政策检查；仅放行爬虫不是引用保证。 |
| [Web Vitals](https://web.dev/articles/vitals) | 使用真实用户 p75 LCP/INP/CLS；实验室测试帮助诊断，不能替代真实用户数据。 |
| [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/) | 根据适用成功标准测试；自动检查仅能覆盖其中部分。 |
| [WCAG Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | 320 CSS px 重排及二维布局例外，避免只测常见手机宽度。 |
| [WCAG Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) | 验证 200% 文本缩放后的内容/功能；字号换成 rem 或根字号翻倍都不能单独证明通过。 |
| [WCAG Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | AA 24 CSS px 或适用例外；44px 可以是舒适设计目标，不误称所有元素的 AA 强制要求。 |

SEO/GEO 不做“关键词密度达到某数字”“FAQ 越多越好”“llms.txt 必须有”“每段固定字数”“买一个插件即收录”等机械扣分。llms.txt、WebMCP 等只在项目有明确使用场景时评估，重新核实其标准/实验状态，当前量表不因缺少它们扣分。

结合 Google/Bing/AI 平台数据时记录原始结果与采样条件，不假设所有平台拥有相同报表或更新时延。优化后仍有抓取/索引/统计时间窗，不能即时用本地得分变化代替外部变化。
