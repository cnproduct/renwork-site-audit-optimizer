# RenWork 网站全面诊断与优化

**已有网站 → 有证据的诊断评分 → 实际修改 → 同范围复测 → 逐项说明改了哪些。**

与从零建站的 [b2b-global-brand-site-master](https://github.com/cnproduct/b2b-global-brand-site-master) 配套，也可独立用于现有网站。适合企业站、外贸 B2B 独立站、产品页和询盘落地页；保留原技术栈、品牌身份与已有有效 URL。

## 使用

把本仓库放入你的代理支持的 Skill 目录，入口为 [SKILL.md](SKILL.md)。在 Codex 中可安装到 `~/.codex/skills/renwork-site-audit-optimizer`。只需 Python 3.10+ 运行自带助手；完整视觉和功能复测使用代理环境已有的浏览器、构建工具和项目权限。

```text
使用 $renwork-site-audit-optimizer 全面诊断 https://我的网站，
源码在 /我的项目。直接完成可执行优化，给出前后评分、检查覆盖率、
改后项目或预览、逐项修改说明、复测证据和剩余问题。
```

也支持“只诊断不修改”。只有网址且无写入入口时仍可诊断并准备替换稿/补丁，不能声称已经改好线上网站。

## 提供什么

- 八个维度：SEO、GEO 与可信内容、品牌设计、可访问性、性能、询盘、国际化、运维安全。
- 固定 100 分内部量表，同时显示已证实分数、检查覆盖率、已检查项质量；26 个检查项，未知项目不算通过。
- 直接优化源模板、文案、视觉、性能和询盘链路；按行业采购场景选修复方式，不机械重建全站。
- 逐项说明原问题、实际修改、原因、文件/URL、证据、复测和回退方式。
- 自带零第三方依赖的静态助手，生成 JSON/中文报告、候选站点、前后 diff 和变更台账。

## V1.1：细分品类、趋势与采购季优化

新增 [趋势与采购周期方法](references/category-seasonal-growth.md) 和 [可直接执行的提示词](references/seasonal-prompts.md)：Google Trends、Pinterest Trends、AI 搜索可见度/买家问题分别研究，再与真实询盘交叉判断；按市场、半球、年度和实际交期倒推采购与内容日期。包含 Activewear、Sportswear、Running Wear、Swimming Wear、Beach Wear 五类适配，并可沿用同一方法扩展其他行业。

```text
使用 $renwork-site-audit-optimizer，针对我的网站及源码，
按各细分品类研究 Google Trends、Pinterest Trends 与 AI 搜索信号，
结合目标市场的季节、节日及实际打样/生产/运输周期，
生成采购日历和逐品类优化提示词，直接完成本轮可执行修改并复测。
```

复制并填写 [示例简报](assets/seasonal-brief.example.json) 后生成情景日历与逐品类提示词：

```bash
python3 scripts/seasonal_plan.py /path/to/category-brief.json --out /path/to/new-seasonal-plan
```

示例日期/交期是明确标注的假设，没有实时趋势数字。脚本只计算日期并生成 `plan.json`、`calendar.md`、`prompts.md`；平台研究与网站实施由 Skill 后续执行。不会自动创建定时任务。原 100 分审计量表保持不变。

## 运行静态助手

```bash
python3 scripts/site_audit.py audit /path/to/rendered-public-site --out /path/to/audit-before
python3 scripts/site_audit.py optimize /path/to/rendered-public-site --out /path/to/optimized --lang en
python3 scripts/test_site_audit.py
```

输入是渲染后的公开目录，不是源码仓库。`--lang` 只用于全部页面明确同语言的站点；输出目录必须新建且位于站点之外。助手只补缺失的编码、viewport 和指定语言；静态检查最多覆盖 18 分。**完整 Skill 继续做源码、浏览器、业务证据检查，不把这三个小修复当作全面优化。**

`audit` 产出报告和证据模板；`optimize` 额外产出 `site/`、`changes.md`、`changes.json`、`changes.diff` 和原始基线。原输入不变，不自动部署。非静态项通过带附件摘要的证据导入，详见 [评分与报告契约](references/report-contract.md)。

## 依据与边界

按 [官方来源](references/search-sources.md) 核对当前 SEO/GEO、CWV 与可访问性要求。没有“必排首页”“必被 AI 引用”或“保证询盘涨幅”；不因缺少 llms.txt 或特殊 Schema 扣分。没有真实收件、搜索平台或业务数据就保留未验证状态。

本仓库含 Skill 工作流和保守静态工具，不是托管 SaaS、完整爬虫、自动 CMS 登录器或安全扫描器。官网实际部署与账号数据的验证依赖对应权限；量表不是搜索引擎提供的分数。

版本：1.1.0（审计量表 1.0.0） · MIT License。
