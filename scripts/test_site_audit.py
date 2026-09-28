#!/usr/bin/env python3
"""One behavioral regression check; all sites and submissions are synthetic/local."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from site_audit import audit, compare, digest, optimize, repair, RUBRIC, write_json


def must_reject(fn):
    try:
        fn()
    except (ValueError, OSError):
        return
    raise AssertionError("unsafe/invalid input was accepted")


def main():
    with tempfile.TemporaryDirectory(prefix="site-audit-test-") as temp:
        base = Path(temp)
        site = base / "public"
        site.mkdir()
        content = '''<!doctype html>
<html><head><title>Sample product</title>
<meta name="description" content="Synthetic fixture, not a real company">
<meta name="robots" content="noindex">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage"}</script>
</head><body><main><h1>产品 α</h1><img src="product.svg" alt="Synthetic drawing">
<a href="mailto:rfq@example.invalid">Contact</a></main></body></html>'''
        (site / "index.html").write_bytes(content.replace("\n", "\r\n").encode())
        (site / "product.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        original = {p.name: p.read_bytes() for p in site.iterdir()}
        before = audit(site)
        assert before["score"]["confirmed_points"] == 12
        assert before["score"]["coverage_percent"] == 18
        assert all(c["status"] == "NOT_RUN" for c in before["checks"] if c["method"] == "evidence")
        assert original == {p.name: p.read_bytes() for p in site.iterdir()}
        after = optimize(site, base / "optimized", "en")
        assert after["score"]["confirmed_points"] == 18
        assert not after["score"]["complete"] and after["score"]["measured_quality_percent"] == 100
        updated = (base / "optimized/site/index.html").read_bytes().decode()
        assert "noindex" in updated and "mailto:rfq@example.invalid" in updated and "产品 α" in updated
        assert original == {p.name: p.read_bytes() for p in site.iterdir()}
        assert repair(updated, "en")[0] == updated
        assert '\r\n<meta name="description"' in updated
        assert (base / "optimized/changes.diff").stat().st_size > 0
        ledger = json.loads((base / "optimized/changes.json").read_text())
        assert {c["check"] for c in ledger["changes"][0]["changes"]} == {"encoding", "lang", "viewport"}
        assert ledger["deployment"] == "NOT_RUN"
        assert compare(before, after)["comparable_weight"] == 18
        must_reject(lambda: optimize(site, site / "result"))
        must_reject(lambda: optimize(site, base / "optimized"))
        must_reject(lambda: optimize(site, base / "bad-lang", '\"><script>alert(1)</script>'))
        assert not (base / "bad-lang").exists()

        # Explicit declarations and text inside scripts/comments are preserved.
        tricky = '''<!-- <html><head> -->
<html lang="zh-CN"><head data-note=">"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body><script>const markup = "<head><html>";</script></body></html>'''
        assert repair(tricky, "en") == (tricky, [])
        with_missing = tricky.replace('<meta charset="utf-8">', '')
        fixed, changes = repair(with_missing, "en")
        assert len(changes) == 1 and '<!-- <html><head> -->' in fixed and 'const markup = "<head><html>"' in fixed
        assert repair('<section>fragment</section>', "en") == ('<section>fragment</section>', [])

        # Evidence must identify the actual artifact and current scope/resources.
        artifact = base / "review.md"
        artifact.write_text("Synthetic review artifact; fixture only.")
        evidence = {"fingerprint": before["fingerprint"], "pages": before["pages"], "checks": {
            "hierarchy": {"status": "PASS", "notes": "Local fixture evidence", "measured_at": datetime.now(timezone.utc).isoformat(),
                          "artifact": "review.md", "sha256": digest(artifact.read_bytes())}}}
        evidence_path = base / "evidence.json"
        write_json(evidence_path, evidence)
        evidenced = audit(site, evidence_path)
        assert evidenced["score"]["confirmed_points"] == 17 and evidenced["score"]["coverage_percent"] == 23
        assert compare(evidenced, after)["comparable_weight"] == 18
        artifact.write_text("changed artifact")
        must_reject(lambda: audit(site, evidence_path))

        artifact.write_text("Synthetic review artifact; fixture only.")
        (site / "product.svg").write_text("changed asset")
        must_reject(lambda: audit(site, evidence_path))
        (site / "product.svg").write_bytes(original["product.svg"])
        changed_scope = copy.deepcopy(after)
        changed_scope["pages"].append("new.html")
        must_reject(lambda: compare(before, changed_scope))
        evidence["checks"]["title"] = {"status": "PASS", "notes": "override attempt"}
        write_json(evidence_path, evidence)
        must_reject(lambda: audit(site, evidence_path))
        evidence["checks"].pop("title")
        evidence["checks"]["hierarchy"]["weight"] = 1000
        write_json(evidence_path, evidence)
        must_reject(lambda: audit(site, evidence_path))

        empty = base / "empty"
        empty.mkdir()
        must_reject(lambda: audit(empty))
        (site / ".env").write_text("SYNTHETIC_ONLY=no-secrets")
        must_reject(lambda: audit(site))
        (site / ".env").unlink()
        (site / "linked.html").symlink_to(site / "index.html")
        must_reject(lambda: audit(site))
        (site / "linked.html").unlink()
        (site / "other.html").write_text(content)
        assert next(c for c in audit(site)["checks"] if c["id"] == "title")["status"] == "FAIL"
        (site / "other.html").unlink()
        (site / "index.html").write_text('<html lang><head><meta name="description" content><meta name="viewport" content></head></html>')
        malformed = audit(site)
        assert next(c for c in malformed["checks"] if c["id"] == "description")["status"] == "FAIL"
        (site / "index.html").write_text(content.replace('{"@context":"https://schema.org","@type":"WebPage"}', '{bad json}'))
        assert next(c for c in audit(site)["checks"] if c["id"] == "jsonld")["status"] == "FAIL"
        (site / "index.html").write_text(content.replace('{"@context":"https://schema.org","@type":"WebPage"}', '{"value":NaN}'))
        assert next(c for c in audit(site)["checks"] if c["id"] == "jsonld")["status"] == "FAIL"
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("site_audit.py")), "audit", str(empty), "--out", str(base / "empty-report")], capture_output=True)
        assert result.returncode == 2 and not (base / "empty-report").exists()
        assert sum(r[2] for r in RUBRIC) == 100
    print("PASS: scoring/coverage, immutable input, safe repairs, idempotence, parser boundaries, artifact/scope validation, stale evidence, empty/private/symlink rejection, duplicate titles, malformed JSON-LD, CLI failure")


if __name__ == "__main__":
    main()
