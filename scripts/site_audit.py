#!/usr/bin/env python3
"""Evidence-scoped website audit and conservative static HTML repair. Stdlib only."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys

VERSION = "1.0.0"
# id, category, weight, method, criterion
RUBRIC = [
    ("title", "SEO", 4, "static", "页面有非空且不重复的 title"),
    ("description", "SEO", 3, "static", "页面有单个非空 description"),
    ("crawl", "SEO", 6, "evidence", "状态码、渲染、robots、noindex 与收录意图一致"),
    ("canonical", "SEO", 4, "evidence", "规范化、重定向、站点地图与 URL 策略一致"),
    ("links", "SEO", 3, "evidence", "关键页面可发现，内链、分页、失效链接已检查"),
    ("jsonld", "GEO与可信内容", 1, "static", "存在的 JSON-LD 可解析为对象或数组"),
    ("facts", "GEO与可信内容", 6, "evidence", "采购事实有来源，结构化数据与可见事实一致"),
    ("answers", "GEO与可信内容", 5, "evidence", "关键采购问题有清晰且有条件、有依据的回答"),
    ("identity", "GEO与可信内容", 3, "evidence", "企业实体、联系身份、作者与更新信息可核验"),
    ("hierarchy", "品牌与设计", 5, "evidence", "各断点信息层级、产品视觉、CTA 与品牌一致"),
    ("typography", "品牌与设计", 5, "evidence", "字体、行长、留白、多语言排版与素材质量合适"),
    ("lang", "可访问性", 2, "static", "html 有非空 lang 属性"),
    ("viewport", "可访问性", 2, "static", "viewport 使用设备宽度且不禁止缩放"),
    ("alt", "可访问性", 2, "static", "img 声明 alt；语义是否正确需人工检查"),
    ("structure", "可访问性", 2, "static", "页面包含 h1 与 main 地标"),
    ("keyboard", "可访问性", 4, "evidence", "键盘、焦点、表单标签与错误提示可操作"),
    ("visual_access", "可访问性", 3, "evidence", "对比度、320px 重排、200% 缩放、动效已测试"),
    ("lab", "性能", 4, "evidence", "同条件实验室测试及性能问题复测有记录"),
    ("field", "性能", 6, "evidence", "真实用户 CWV p75 达标，区分 URL 与源站样本"),
    ("buyer_path", "询盘转化", 5, "evidence", "行业采购路径、选型信息与询盘入口可用"),
    ("delivery", "询盘转化", 7, "evidence", "异常恢复、去重与目标收件箱或 CRM 实际收件验证"),
    ("analytics", "询盘转化", 3, "evidence", "转化事件口径、隐私选择与有效线索去重已验证"),
    ("localization", "国际化", 5, "evidence", "目标市场语言、单位、术语及适用 hreflang 正确"),
    ("encoding", "运维与安全", 2, "static", "页面明确声明 UTF-8 字符集"),
    ("transport", "运维与安全", 3, "evidence", "HTTPS、资源、第三方脚本、表单传输与隐私适当"),
    ("maintenance", "运维与安全", 5, "evidence", "可构建、可回退、资产权属清晰且公开目录无私密资料"),
]
assert sum(r[2] for r in RUBRIC) == 100
FORBIDDEN = {".git", "node_modules", "private", "secrets", "package.json"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def invalid_json_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.titles = []
        self.jsonld = []
        self.capture = None
        self.text_buffer = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = {key: value or "" for key, value in attrs}
        self.tags.append((tag, attrs, self.getpos(), self.get_starttag_text()))
        if tag == "title" or (tag == "script" and attrs.get("type", "").lower() == "application/ld+json"):
            self.capture = tag
            self.text_buffer = []

    def handle_endtag(self, tag):
        if tag == self.capture:
            (self.titles if tag == "title" else self.jsonld).append("".join(self.text_buffer).strip())
            self.capture = None

    def handle_data(self, data):
        if self.capture:
            self.text_buffer.append(data)

    def select(self, tag):
        return [a for t, a, _, _ in self.tags if t == tag]


def inventory(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("输入必须是渲染后的公开站点目录")
    files = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_symlink():
            raise ValueError(f"拒绝符号链接: {rel}")
        if any(x in FORBIDDEN or x.startswith(".env") for x in rel.parts):
            raise ValueError(f"请提供独立的公开构建目录，不要提供源码/私密目录: {rel}")
        if p.is_file():
            files.append(p)
    pages = [p for p in files if p.suffix.lower() in {".html", ".htm"}]
    if not pages:
        raise ValueError("没有 HTML 页面；不能评分。SSR/SPA 请先采集渲染结果")
    signature = digest(json.dumps([(p.relative_to(root).as_posix(), digest(p.read_bytes())) for p in files], ensure_ascii=False).encode())
    return root, pages, signature


def static_checks(page, duplicate_titles):
    metas = page.select("meta")
    descriptions = [m.get("content", "").strip() for m in metas if m.get("name", "").lower() == "description"]
    viewports = [m.get("content", "").lower() for m in metas if m.get("name", "").lower() == "viewport"]
    viewport = len(viewports) == 1 and re.search(r"(?:^|,)\s*width\s*=\s*device-width\s*(?:,|$)", viewports[0]) is not None
    if viewport:
        viewport = not re.search(r"user-scalable\s*=\s*(?:no|0)(?:\s*,|$)", viewports[0]) and "maximum-scale" not in viewports[0]
    ld_ok = None
    if page.jsonld:
        try:
            ld_ok = all(isinstance(json.loads(x, parse_constant=invalid_json_constant), (dict, list)) for x in page.jsonld)
        except (ValueError, TypeError):
            ld_ok = False
    return {
        "title": len(page.titles) == 1 and bool(page.titles[0]) and " ".join(page.titles[0].split()).casefold() not in duplicate_titles,
        "description": len(descriptions) == 1 and bool(descriptions[0]),
        "jsonld": ld_ok,
        "lang": len(page.select("html")) == 1 and bool(page.select("html")[0].get("lang", "").strip()),
        "viewport": bool(viewport),
        "alt": all("alt" in a for a in page.select("img")),
        "structure": bool(page.select("h1")) and (bool(page.select("main")) or any(a.get("role") == "main" for _, a, _, _ in page.tags)),
        "encoding": any(m.get("charset", "").lower().replace("-", "") == "utf8" or (m.get("http-equiv", "").lower() == "content-type" and re.search(r"charset\s*=\s*utf-?8", m.get("content", ""), re.I)) for m in metas),
    }


def load_evidence(path, fingerprint, pages):
    if not path:
        return {}
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("fingerprint") != fingerprint or data.get("pages") != pages:
        raise ValueError("证据对应的站点指纹/页面范围已变化；请重新测试")
    records = data.get("checks", {})
    allowed = {r[0] for r in RUBRIC if r[3] == "evidence"}
    if not isinstance(records, dict) or set(records) - allowed:
        raise ValueError("证据包含未知检查项，或尝试覆盖静态检查")
    for cid, item in records.items():
        if not isinstance(item, dict) or set(item) - {"status", "notes", "measured_at", "artifact", "sha256"}:
            raise ValueError(f"{cid}: 证据只能包含状态、说明、时间和附件信息，不能改变量表")
        if item.get("status") not in {"PASS", "FAIL", "NOT_RUN"}:
            raise ValueError(f"{cid}: status 必须为 PASS / FAIL / NOT_RUN")
        if not isinstance(item.get("notes"), str) or not item["notes"].strip():
            raise ValueError(f"{cid}: 需要说明测试范围、条件和结论")
        if item["status"] == "NOT_RUN":
            continue
        measured = datetime.fromisoformat(item.get("measured_at", "").replace("Z", "+00:00"))
        if measured.tzinfo is None or measured > datetime.now(timezone.utc):
            raise ValueError(f"{cid}: 测试时间必须带时区且不能在未来")
        artifact = (path.parent / item.get("artifact", "")).resolve()
        if not artifact.is_file() or digest(artifact.read_bytes()) != item.get("sha256"):
            raise ValueError(f"{cid}: 证据文件不存在或摘要不匹配")
    return records


def score(checks):
    earned = sum(x["weight"] for x in checks if x["status"] == "PASS")
    measured = sum(x["weight"] for x in checks if x["status"] != "NOT_RUN")
    total = sum(x["weight"] for x in checks)
    return {"confirmed_points": earned, "total_points": total, "measured_points": measured,
            "measured_quality_percent": round(100 * earned / measured, 1) if measured else None,
            "coverage_percent": round(100 * measured / total, 1) if total else 0, "complete": measured == total}


def audit(root, evidence=None):
    root, paths, fingerprint = inventory(root)
    pages = {p.relative_to(root).as_posix(): Page(p.read_text(encoding="utf-8")) for p in paths}
    title_counts = Counter(" ".join(t.split()).casefold() for p in pages.values() for t in p.titles if t)
    duplicate_titles = {t for t, count in title_counts.items() if count > 1}
    observations = {name: static_checks(p, duplicate_titles) for name, p in pages.items()}
    records = load_evidence(evidence, fingerprint, list(pages))
    checks = []
    for cid, category, weight, method, label in RUBRIC:
        item = dict(id=cid, category=category, weight=weight, method=method, label=label)
        if method == "static":
            failed = [name for name, obs in observations.items() if obs[cid] is False]
            unknown = [name for name, obs in observations.items() if obs[cid] is None]
            item.update(status="FAIL" if failed else "NOT_RUN" if unknown else "PASS", failed_pages=failed, unmeasured_pages=unknown)
        else:
            item.update(records.get(cid, {"status": "NOT_RUN", "notes": "需要实际浏览器、业务或外部平台证据"}))
        checks.append(item)
    return {"version": VERSION, "created_at": now(), "fingerprint": fingerprint, "pages": list(pages),
            "scope": "仅所列渲染页面；全站覆盖、源代码及外部结果须另有证据", "checks": checks,
            "score": score(checks), "categories": {cat: score([x for x in checks if x["category"] == cat]) for cat in dict.fromkeys(r[1] for r in RUBRIC)}}


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown(report):
    s = report["score"]
    lines = ["# 网站诊断报告", "", f"规则版本：{VERSION} · 页面数：{len(report['pages'])} · {report['created_at']}", "",
             f"**已证实得分 {s['confirmed_points']}/100；检查覆盖率 {s['coverage_percent']}%；已检查项质量 {s['measured_quality_percent']}%。**", "",
             "这是内部质量量表，不是 Google 排名分、AI 引用率或转化保证。NOT_RUN 不算通过，也不能按 100 分对外宣传。", "",
             report["scope"], "", "| 维度 | 已证实分 / 维度分 | 已检查分值 |", "|---|---:|---:|"]
    for cat, value in report["categories"].items():
        lines.append(f"| {cat} | {value['confirmed_points']} / {value['total_points']} | {value['measured_points']} |")
    for item in report["checks"]:
        lines += ["", f"## {item['id']} · {item['status']} · {item['weight']} 分", "", item["label"]]
        if item.get("failed_pages"):
            lines += ["", "发现问题：" + ", ".join(item["failed_pages"])]
        if item.get("unmeasured_pages"):
            lines += ["", "未测页面：" + ", ".join(item["unmeasured_pages"])]
        if item.get("notes"):
            lines += ["", item["notes"]]
        if item.get("artifact"):
            lines += ["", f"证据：{item['artifact']} · SHA-256 {item['sha256']}"]
    return "\n".join(lines) + "\n"


def save_report(folder, report):
    write_json(folder / "audit.json", report)
    (folder / "report.md").write_text(markdown(report), encoding="utf-8")
    write_json(folder / "evidence-template.json", {"fingerprint": report["fingerprint"], "pages": report["pages"],
               "checks": {r[0]: {"status": "NOT_RUN", "notes": "尚未测试"} for r in RUBRIC if r[3] == "evidence"}})


def fresh_output(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    if out == root or root in out.parents or out in root.parents:
        raise ValueError("报告/优化输出必须与输入目录分离")
    if out.exists():
        raise ValueError("输出已存在；请使用新目录，避免覆盖")
    return out


def repair(text, lang=None):
    page = Page(text)
    # ponytail: only edit parser-located opening tags; framework templates require source edits.
    if len(page.select("head")) != 1 or len(page.select("html")) != 1:
        return text, []
    if any(raw.rstrip().endswith("/>") for tag, _, _, raw in page.tags if tag in {"head", "html"}):
        return text, []
    edits, reasons = [], []
    lines = text.splitlines(keepends=True)
    for tag, attrs, (line, column), raw in page.tags:
        start = sum(len(x) for x in lines[:line - 1]) + column
        replacement = raw
        if tag == "head":
            metas = page.select("meta")
            if not any("charset" in m or m.get("http-equiv", "").lower() == "content-type" for m in metas):
                replacement += '\n<meta charset="utf-8">'
                reasons.append({"check": "encoding", "line": line, "why": "明确实际 UTF-8 编码，避免乱码"})
            if not any(m.get("name", "").lower() == "viewport" for m in metas):
                replacement += '\n<meta name="viewport" content="width=device-width, initial-scale=1">'
                reasons.append({"check": "viewport", "line": line, "why": "启用设备宽度布局；仍需视觉重排复测"})
        if tag == "html" and lang and "lang" not in attrs:
            replacement = raw[:-1] + f' lang="{lang}">'
            reasons.append({"check": "lang", "line": line, "why": "使用明确提供的页面语言，辅助读屏和语言识别"})
        if replacement != raw:
            edits.append((start, start + len(raw), replacement))
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text, reasons


def compare(before, after):
    if before["version"] != after["version"] or before["pages"] != after["pages"]:
        raise ValueError("前后规则或页面范围不同，不能直接比较分数")
    pairs = list(zip(before["checks"], after["checks"]))
    if any(a["id"] != b["id"] or a["weight"] != b["weight"] for a, b in pairs) or len(before["checks"]) != len(after["checks"]):
        raise ValueError("前后检查项不同，不能比较")
    common = [(a, b) for a, b in pairs if a["status"] != "NOT_RUN" and b["status"] != "NOT_RUN"]
    return {"comparable_weight": sum(a["weight"] for a, _ in common),
            "before_confirmed_on_common": sum(a["weight"] for a, _ in common if a["status"] == "PASS"),
            "after_confirmed_on_common": sum(b["weight"] for _, b in common if b["status"] == "PASS"),
            "status_changes": [{"id": a["id"], "before": a["status"], "after": b["status"]} for a, b in pairs if a["status"] != b["status"]]}


def optimize(root, out, lang=None):
    if lang and not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", lang):
        raise ValueError("--lang 必须为语言标签，例如 en 或 zh-CN")
    out = fresh_output(root, out)
    before = audit(root)
    out.mkdir(parents=True)
    candidate = out / "site"
    shutil.copytree(root, candidate)
    changes, diffs = [], []
    for name in before["pages"]:
        path = candidate / name
        original = path.read_bytes().decode("utf-8")
        updated, reasons = repair(original, lang)
        if updated != original:
            path.write_bytes(updated.encode("utf-8"))
            patch = "".join(difflib.unified_diff(original.splitlines(keepends=True), updated.splitlines(keepends=True), fromfile=f"before/{name}", tofile=f"after/{name}"))
            diffs.append(patch)
            changes.append({"file": name, "changes": reasons, "before_sha256": digest(original.encode()), "after_sha256": digest(updated.encode()), "state": "APPLIED_LOCAL"})
    after = audit(candidate)
    write_json(out / "before.json", before)
    save_report(out, after)
    comparison = compare(before, after)
    write_json(out / "changes.json", {"changes": changes, "comparison": comparison, "deployment": "NOT_RUN", "rollback": "原目录未修改；丢弃候选目录即可回退"})
    (out / "changes.diff").write_text("\n".join(diffs), encoding="utf-8")
    lines = ["# 优化结果与变更说明", "", f"同范围静态已证实分：{before['score']['confirmed_points']} → {after['score']['confirmed_points']} / 100。", "",
             f"复测覆盖率：{after['score']['coverage_percent']}%；此轮仅执行静态修复，浏览器、线上发布、询盘收件及搜索效果仍需验证。", ""]
    for change in changes:
        lines.append(f"## {change['file']}")
        lines.extend(f"- {r['check']}（原文件第 {r['line']} 行）：{r['why']}；复测 {next(x['status'] for x in after['checks'] if x['id'] == r['check'])}" for r in change["changes"])
        lines.append("")
    if not changes:
        lines.append("未发现可由静态助手安全自动修复的项目；继续按 Skill 做源码和浏览器优化，不将零改动称为完成。")
    lines += ["", "精确前后差异见 changes.diff；剩余问题与未测项见 report.md。候选站点在 site/，原站未修改，未部署。"]
    (out / "changes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("audit", "optimize"):
        p = sub.add_parser(command)
        p.add_argument("site", type=Path, help="渲染后的公开站点目录，不是源码仓库")
        p.add_argument("--out", type=Path, required=True)
        if command == "audit":
            p.add_argument("--evidence", type=Path)
        else:
            p.add_argument("--lang", help="仅适用于全部页面已确认使用同一语言的站点")
    p = sub.add_parser("compare")
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "compare":
            result = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
        elif args.command == "optimize":
            result = optimize(args.site, args.out, args.lang)["score"]
        else:
            out = fresh_output(args.site, args.out)
            report = audit(args.site, args.evidence)
            out.mkdir(parents=True)
            save_report(out, report)
            result = report["score"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, UnicodeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
