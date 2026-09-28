# 评分与交付契约

## 评分不掩盖盲区

规则在 scripts/site_audit.py 的 RUBRIC 中，版本为 1.0.0。全部权重相加 100，8 项静态语法检查合计 18，其余 18 项检查共 82 分由真实证据支持。不能将一个简单脚本的 100% 当全面诊断分。

- **已证实得分** = PASS 项权重之和 / 100。
- **检查覆盖率** = (PASS + FAIL 的权重) / 100；NOT_RUN 权重保留。
- **已检查项质量** = PASS 权重 / (PASS + FAIL 权重)，无已测项则为空。
- **页面覆盖率** 单独报告：已测 URL / 已知 URL，抽样总数未知则不计算百分比。
- **前后比较** 固定版本、权重和页面列表；compare 只比较前后共同已测项目，另列从未测到已测或失去证据的变化。增加新样本时重新建立可比基线。

例如质量从 60% 提升到 90%，覆盖率却由 80% 降到 20%，不能宣称全站提升。刚修复的代码没有线上/浏览器证据仍不具备该维度的 PASS。P0/P1 应单独列出，不被平均分掩盖。

## 静态助手产物

audit 输出 `audit.json`、中文 `report.md`、`evidence-template.json`；optimize 另外输出 `site/` 候选副本、`before.json`、`changes.json`、`changes.md`、`changes.diff`。失败返回退出码 2；命令成功生成诊断可返回 0，即便报告存在 FAIL，不能把退出码 0 当成站点过关。输出路径不可覆盖已有目录或位于输入内部。

随后由代理继续修改文案、模板或样式时，助手原有 diff/台账只是中间结果。最终必须从原基线到最终源码重新生成完整差异、更新全部变更台账并重新审计；不要用只含自动小修复的文件冒充完整交付。

未传 --lang 不猜语言；已存在 lang/viewport/编码声明不会自动替换。脚本不重写标题、描述、alt、canonical、robots、noindex、结构化业务事实、邮箱或表单端点。格式问题仍可能让静态助手跳过页面；由代理检查原因后在源文件中修复。

`fingerprint` 为输入公开目录全部文件的路径及字节摘要，不只是 HTML。CSS/JS/图片变化会使旧证据失效。多语言或大目录都应使用真实的渲染公开目录；拒绝源码根目录、常见私密目录或符号链接，**这不是完整秘密扫描或发布许可**。

## 外部证据输入

复制本次 audit 的 evidence-template.json，保留 fingerprint 和 pages。每个已测项提供下述字段；保留 NOT_RUN 的项至少写清原因。不要手改指纹来复用旧测试。证据文件保存在私有审计工作区，提交公开仓库前脱敏。

```json
{
  "fingerprint": "复制本次报告中的指纹",
  "pages": ["index.html", "products/index.html"],
  "checks": {
    "hierarchy": {
      "status": "PASS",
      "notes": "完整列明 URL、设备、样本、视觉检查与结论；附件索引链接前后截图",
      "measured_at": "2026-09-27T12:00:00+00:00",
      "artifact": "evidence/visual-review.md",
      "sha256": "该附件原始字节的 SHA-256"
    },
    "delivery": {"status": "NOT_RUN", "notes": "本地失败/重试已测，尚无生产收件证据"}
  }
}
```

相对 artifact 路径相对于 evidence.json；可用 Python hashlib 计算 SHA-256。附件可为包含多个原始日志/截图路径及摘要的索引。工具核验存在性、摘要、带时区的非未来时间和范围，不替代理判断证据真实性/时效/是否足够；PASS 由测试执行者对照诊断标准给出，不能仅因有附件就通过。记录测试人/代理、工具、环境、条件和原始数据；测试必须对应本次改动后的实际状态。

## 完整 Skill 交付目录

按项目需要创建以下实际产物，不建空占位文件：

```text
audit-delivery/
  scope.json              URL/语言/模板/环境及覆盖范围
  before/ after/          评分、检查详情、设备/时间/工具条件
  changes.md              面向业务用户的逐项说明
  changes.json            机器可读变更台账
  changes.diff            精确源码差异；Git 项目可另附 commit/PR
  evidence/               截图、构建/测试、性能、脱敏收件证明
  optimized-site/         可运行改后项目或真实预览入口；不能只给报告
  remaining.md            未完成项目、原因、所需资料/权限与优先级
```

每条变更包含 id、priority、URL/源码路径与位置、before、after、why、事实来源（如适用）、实施状态、复测结果、证据路径、回退方式。特别区分：

| 状态 | 意义 |
|---|---|
| PROPOSED | 替换稿/建议/补丁已准备，尚未应用 |
| APPLIED_LOCAL | 已在本地源码或候选副本落实 |
| VERIFIED_LOCAL | 与改动相关的构建/浏览器/功能验证通过 |
| DEPLOYED | 已发布，但尚未完成线上验收 |
| VERIFIED_LIVE | 实际域名上的对应检查通过 |

最终业务说明格式可以是：“详情页原先缺少选型条件；依据已提供技术表增加适用工况/限制与询盘型号预填；已修改哪些文件；在什么设备完成哪些复测；预期减少采购沟通成本，实际有效询盘提升仍待观察。”不要把预期收益写成已发生业绩。

## 搜索与业务结果单列

发布时间、HTTP/渲染、表单收件、Search Console/Bing 权限和收录、AI 引用观察、有效线索分别记录。AI 观察至少给出引擎/模型、日期、市场/语言、联网模式、问题、引用 URL、重复次数和样本分母。实验只说明该样本；曝光、点击、咨询、合格询盘与成交是不同指标。没有账号数据保持 NOT_RUN，不估造访问量、排名、引用率或询盘涨幅。

## 品类与季节优化交付（Skill 1.1.0）

按 [品类流程](category-seasonal-growth.md) 补充 `trend-evidence`、`procurement-calendar`、`category-page-actions`、`category-prompts`；可用 Markdown/JSON/CSV，不强制新数据库。逐来源记录 OBSERVED/HYPOTHESIS/UNAVAILABLE，逐改动关联品类、市场、采购阶段、证据和实际执行状态。季节规划脚本的 NOT_RUN 只表示尚未研究，不是平台不存在。

规划助手输出 `plan.json`（完整输入/假设及两种情景）、`calendar.md`、`prompts.md`。它不采集平台数据、不确认企业事实、不修改网站；不要将运行成功记为趋势已验证或网站已优化。助手使用串行日历天，实际并行流程/工作日/节假日须先转换。完整字段示例见 [JSON 简报](../assets/seasonal-brief.example.json)；未知关键日期/交期先交付待填方案，脚本拒绝缺项。

本次升级的是 Skill 功能版本 1.1.0，原审计规则版本仍为 1.0.0，保证前后 100 分量表可比。重复运行要核查执行日和事件年度，不直接执行过期提示词；日历上的日期不表示已设置后台自动任务。
