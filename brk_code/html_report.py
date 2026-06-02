"""HTML report generation for BRK-Code."""

from __future__ import annotations

import html as html_module
from pathlib import Path
from typing import Any

from .container import BRKCodeContainer
from .util import format_size


def export_html(container: BRKCodeContainer, output_path: Path) -> None:
    """Generate a standalone HTML report from a .brk-code container."""
    data = container.data
    header = data.get("header", {})
    repo = data.get("repo_graph", {})
    ast_graph = data.get("ast_semantic_graph", {})
    symbols = data.get("symbol_table", {})
    deps = data.get("dependency_graph", {})
    sec = data.get("security_report", {})
    tasks = data.get("learning_tasks", [])
    test_map = data.get("test_map", {})
    func_contracts = data.get("function_contracts", {})
    flags = header.get("flags", {})

    file_count = header.get("file_count", 0)
    py_count = header.get("python_file_count", 0)
    func_count = len(ast_graph.get("functions", []))
    class_count = len(ast_graph.get("classes", []))
    import_count = len(deps.get("imports", []))
    sec_count = len(sec.get("findings", []))
    task_count = len(tasks)
    secrets = sec.get("secrets_redacted", 0)

    # Build HTML
    parts: list[str] = []

    parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BRK-Code Report</title>
<style>
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #58a6ff;
  --green: #3fb950;
  --yellow: #d29922;
  --red: #f85149;
  --code-bg: #1c2128;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; padding:2rem; max-width:1100px; margin:0 auto; }
h1 { font-size:2rem; margin-bottom:0.5rem; }
h2 { font-size:1.4rem; margin:2rem 0 0.75rem; padding-bottom:0.4rem; border-bottom:1px solid var(--border); color:var(--accent); }
h3 { font-size:1.1rem; margin:1.5rem 0 0.5rem; color:var(--green); }
p { margin:0.5rem 0; }
code { font-family: 'SFMono-Regular',Consolas,monospace; background:var(--code-bg); padding:0.15rem 0.4rem; border-radius:4px; font-size:0.88em; }
pre { background:var(--code-bg); border:1px solid var(--border); border-radius:8px; padding:1rem; overflow-x:auto; margin:1rem 0; }
table { width:100%; border-collapse:collapse; margin:1rem 0; }
th,td { padding:0.5rem 0.75rem; text-align:left; border-bottom:1px solid var(--border); }
th { color:var(--accent); font-weight:600; }
td { color:var(--muted); }
.badge { display:inline-block; padding:0.2rem 0.6rem; border-radius:999px; font-size:0.8rem; font-weight:600; }
.badge-red { background:#da363333; color:var(--red); border:1px solid #da363355; }
.badge-yellow { background:#9e6a0333; color:var(--yellow); border:1px solid #9e6a0355; }
.badge-green { background:#23863633; color:var(--green); border:1px solid #23863655; }
.badge-blue { background:#1f6feb33; color:var(--accent); border:1px solid #1f6feb55; }
.warning { background:#9e6a0322; border:1px solid #9e6a0355; border-radius:8px; padding:1rem; margin:1rem 0; }
.warning strong { color:var(--yellow); }
.severity-high { color:var(--red); font-weight:bold; }
.severity-medium { color:var(--yellow); font-weight:bold; }
.severity-low { color:var(--green); }
.search-box { margin:1rem 0; }
.search-box input { background:var(--code-bg); color:var(--text); border:1px solid var(--border); border-radius:6px; padding:0.5rem 1rem; width:100%; max-width:400px; font-size:0.95rem; }
.stats { display:flex; gap:1rem; flex-wrap:wrap; margin:1rem 0; }
.stat { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:1rem 1.5rem; text-align:center; min-width:120px; }
.stat .num { font-size:1.8rem; font-weight:bold; color:var(--accent); }
.stat .label { font-size:0.8rem; color:var(--muted); margin-top:0.25rem; }
footer { margin-top:3rem; padding-top:1rem; border-top:1px solid var(--border); color:var(--muted); font-size:0.85rem; text-align:center; }
</style>
</head>
<body>
""")

    # Header
    parts.append(f"""<h1>BRK-Code Report: {esc(header.get("source_root_name", "unknown"))}</h1>
<p><span class="badge badge-blue">BRK-Code-Python v0.1</span>
<span class="badge badge-red">Lossless: {flags.get("lossless", False)}</span>
<span class="badge badge-green">Semantic equivalent: {flags.get("semantic_equivalent", True)}</span>
<span class="badge badge-yellow">AI learning optimized: {flags.get("ai_learning_optimized", True)}</span></p>
""")

    # Warning
    parts.append("""<div class="warning">
<strong>⚠ Important</strong><br>
This BRK-Code file is not a lossless source archive.<br>
It is an AI-learning-optimized semantic code container.<br>
このBRK-Codeはソースコードの完全可逆アーカイブではありません。<br>
AI学習・解析向けの意味構造コンテナです。
</div>""")

    # Stats
    parts.append(f"""<div class="stats">
<div class="stat"><div class="num">{file_count}</div><div class="label">Files</div></div>
<div class="stat"><div class="num">{py_count}</div><div class="label">Python Files</div></div>
<div class="stat"><div class="num">{func_count}</div><div class="label">Functions</div></div>
<div class="stat"><div class="num">{class_count}</div><div class="label">Classes</div></div>
<div class="stat"><div class="num">{import_count}</div><div class="label">Imports</div></div>
<div class="stat"><div class="num">{sec_count}</div><div class="label">Security Findings</div></div>
<div class="stat"><div class="num">{task_count}</div><div class="label">Learning Tasks</div></div>
</div>""")

    # Search box
    parts.append("""<div class="search-box">
<input type="text" id="searchInput" placeholder="Search functions, classes, files..." oninput="filterTables()">
</div>
<script>
function filterTables() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  document.querySelectorAll('table[data-filterable] tbody tr').forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}
</script>""")

    # Files table
    parts.append("""<h2>Files</h2>
<table data-filterable>
<thead><tr><th>Path</th><th>Lines</th><th>Size</th><th>Test</th></tr></thead>
<tbody>""")
    for f in repo.get("files", []):
        test_badge = '<span class="badge badge-green">Yes</span>' if f.get("is_test") else '<span class="badge badge-yellow">No</span>'
        parts.append(f'<tr><td><code>{esc(f["path"])}</code></td><td>{f["line_count"]}</td><td>{format_size(f["size_bytes"])}</td><td>{test_badge}</td></tr>')
    parts.append("</tbody></table>")

    # Functions table
    parts.append("""<h2>Functions</h2>
<table data-filterable>
<thead><tr><th>Name</th><th>File</th><th>Line</th><th>Args</th><th>Async</th><th>Complexity</th></tr></thead>
<tbody>""")
    for f in ast_graph.get("functions", []):
        async_badge = '<span class="badge badge-blue">async</span>' if f.get("is_async") else ""
        parts.append(f'<tr><td><code>{esc(f["qualified_name"])}</code></td><td>{esc(f["file"])}</td><td>{f["line"]}</td><td>{esc(", ".join(f["args"]))}</td><td>{async_badge}</td><td>{f.get("complexity_estimate", 0)}</td></tr>')
    parts.append("</tbody></table>")

    # Classes table
    parts.append("""<h2>Classes</h2>
<table data-filterable>
<thead><tr><th>Name</th><th>File</th><th>Line</th><th>Methods</th><th>Bases</th></tr></thead>
<tbody>""")
    for c in ast_graph.get("classes", []):
        parts.append(f'<tr><td><code>{esc(c["name"])}</code></td><td>{esc(c["file"])}</td><td>{c["line"]}</td><td>{esc(", ".join(c.get("methods", [])))}</td><td>{esc(", ".join(c.get("bases", [])))}</td></tr>')
    parts.append("</tbody></table>")

    # Dependency table
    parts.append("""<h2>Dependencies</h2>
<table data-filterable>
<thead><tr><th>From</th><th>Module</th><th>Kind</th></tr></thead>
<tbody>""")
    for imp in deps.get("imports", []):
        kind_badge = '<span class="badge badge-green">local</span>' if imp["kind"] == "local" else '<span class="badge badge-blue">ext</span>'
        parts.append(f'<tr><td>{esc(imp["from_file"])}</td><td><code>{esc(imp["module"])}</code></td><td>{kind_badge}</td></tr>')
    parts.append("</tbody></table>")

    # Security findings
    parts.append(f"""<h2>Security Findings ({sec_count})</h2>
<p>Secrets redacted: <strong>{secrets}</strong></p>""")
    if sec_count > 0:
        parts.append("""<table data-filterable>
<thead><tr><th>File</th><th>Line</th><th>Severity</th><th>Type</th><th>Message</th></tr></thead>
<tbody>""")
        for finding in sec.get("findings", []):
            sev_class = f"severity-{finding['severity']}"
            parts.append(f'<tr><td>{esc(finding["file"])}</td><td>{finding["line"]}</td><td class="{sev_class}">{finding["severity"]}</td><td>{esc(finding["type"])}</td><td>{esc(finding["message"])}</td></tr>')
        parts.append("</tbody></table>")
    else:
        parts.append('<p style="color:var(--green);">No security findings detected.</p>')

    # Learning tasks
    parts.append(f"""<h2>Learning Tasks ({task_count})</h2>
<table data-filterable>
<thead><tr><th>Type</th><th>Prompt</th></tr></thead>
<tbody>""")
    for task in tasks:
        parts.append(f'<tr><td><span class="badge badge-blue">{esc(task["task_type"])}</span></td><td>{esc(task["prompt"][:120])}...</td></tr>')
    parts.append("</tbody></table>")

    # Footer
    parts.append("""<footer>
<p>BRK-Code Report | lossless=false | bit_exact_reconstruction=false | semantic_equivalent=true | ai_learning_optimized=true</p>
<p>BRK-Code does not break Shannon's theorem. BRK-Code is not a universal lossless source-code compressor.</p>
</footer>
</body>
</html>""")

    output_path.write_text("\n".join(parts), encoding="utf-8")


def esc(text: str) -> str:
    """HTML-escape text."""
    return html_module.escape(str(text))
