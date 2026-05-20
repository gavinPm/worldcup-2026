#!/usr/bin/env python3
"""Sync all markdown docs to Lark wiki under a given parent node."""

import json, re, subprocess, time, os
import html

SPACE_ID = "7633744969873772255"
PARENT_TOKEN = "Ef3kwuT0fiBRZBkXwbDlxcydgLb"
DOCS_DIR = "/Users/erha/Documents/Claude/Projects/世界杯活动4/需求文档"

FILES = [
    "activity-rules.md",
    "【PRD】世界杯活动落地页.md",
    "【PRD】世界杯活动主要数据表字段参考.md",
    "【PRD】奖励审核后台.md",
    "【PRD】赛事管理页.md",
    "【逻辑说明】清算逻辑.md",
    "【PRD】世界杯活动落地页埋点.md",
    "【汇报】世界杯活动概述.md",
    "【说明】赛程API.md",
    "比赛时间说明.md",
]

# ---------------------------------------------------------------------------
# Lark API helpers
# ---------------------------------------------------------------------------

def lark_api(method, path, data=None, params=None):
    cmd = ["lark-cli", "api", method, path]
    if params:
        cmd += ["--params", json.dumps(params, ensure_ascii=False)]
    if data:
        cmd += ["--data", json.dumps(data, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    return json.loads(out) if out else {}

def list_child_nodes():
    items = []
    page_token = None
    while True:
        p = {"parent_node_token": PARENT_TOKEN, "page_size": 50}
        if page_token:
            p["page_token"] = page_token
        res = lark_api("GET", f"/open-apis/wiki/v2/spaces/{SPACE_ID}/nodes", params=p)
        if res.get("code") != 0:
            break
        data = res.get("data", {})
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return items

def delete_nodes(node_tokens):
    for i in range(0, len(node_tokens), 10):
        batch = node_tokens[i:i+10]
        lark_api("POST", f"/open-apis/wiki/v2/spaces/{SPACE_ID}/nodes/move_docs_to_trash",
                 {"wiki_nodes": [{"wiki_token": t} for t in batch]})

def create_node(title):
    res = lark_api("POST", f"/open-apis/wiki/v2/spaces/{SPACE_ID}/nodes", {
        "node_type": "origin",
        "obj_type": "docx",
        "parent_node_token": PARENT_TOKEN,
        "title": title,
    })
    if res.get("code") != 0:
        raise RuntimeError(f"create_node failed: {res}")
    return res["data"]["node"]["obj_token"]

def _run_doc_update(doc_id, xml_content, command):
    tmp = "_sync_tmp.xml"
    tmp_abs = os.path.join(DOCS_DIR, tmp)
    with open(tmp_abs, "w", encoding="utf-8") as f:
        f.write(xml_content)
    try:
        cmd = [
            "lark-cli", "docs", "+update",
            "--api-version", "v2",
            "--doc", doc_id,
            "--command", command,
            "--doc-format", "xml",
            "--content", f"@{tmp}",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=DOCS_DIR)
        out = r.stdout.strip()
        return json.loads(out) if out else {"ok": False, "stderr": r.stderr[:300]}
    finally:
        os.remove(tmp_abs)

def _split_xml_at_h1(xml):
    """Split XML at <h1> boundaries to avoid Lark's parallel-batch reordering."""
    lines = xml.split('\n')
    chunks, current = [], []
    for line in lines:
        if line.startswith('<h1>') and current:
            chunks.append('\n'.join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append('\n'.join(current))
    return [c for c in chunks if c.strip()]

def overwrite_doc_xml(doc_id, xml_content):
    chunks = _split_xml_at_h1(xml_content)
    if not chunks:
        return {"ok": False, "msg": "no content"}
    result = _run_doc_update(doc_id, chunks[0], "overwrite")
    if not (result.get('ok') or result.get('data', {}).get('result') == 'success'):
        return result
    for i, chunk in enumerate(chunks[1:], 2):
        print(f'    chunk {i}/{len(chunks)}')
        time.sleep(0.5)
        r = _run_doc_update(doc_id, chunk, "append")
        if not (r.get('ok') or r.get('data', {}).get('result') == 'success'):
            print(f'    [WARN chunk {i}] {r}')
    return {"ok": True}

# ---------------------------------------------------------------------------
# Markdown → XML converter
# ---------------------------------------------------------------------------

def escape(text):
    return html.escape(text, quote=False)

def inline_md(text):
    """Convert inline markdown to XML inline tags."""
    # bold
    text = re.sub(r'\*\*([^*]+)\*\*', lambda m: f'<b>{escape(m.group(1))}</b>', text)
    # inline code
    text = re.sub(r'`([^`]+)`', lambda m: f'<code>{escape(m.group(1))}</code>', text)
    # strikethrough
    text = re.sub(r'~~([^~]+)~~', lambda m: f'<del>{escape(m.group(1))}</del>', text)
    # plain text (already escaped above for unmatched parts — handle remaining)
    return text

def inline_md_escaped(text):
    """Escape then apply inline markdown."""
    # Escape first, then apply patterns that wrap with tags
    # But ** and `` should NOT be escaped before processing
    # Strategy: process patterns first on original, then escape remaining plain text
    parts = []
    pattern = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`|~~[^~]+~~|<br\s*/?>)')
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            parts.append(escape(text[last:m.start()]))
        token = m.group(0)
        if token.startswith('**'):
            parts.append(f'<b>{escape(token[2:-2])}</b>')
        elif token.startswith('`'):
            parts.append(f'<code>{escape(token[1:-1])}</code>')
        elif token.startswith('~~'):
            parts.append(f'<del>{escape(token[2:-2])}</del>')
        elif token.startswith('<br'):
            parts.append('<br/>')
        last = m.end()
    parts.append(escape(text[last:]))
    return ''.join(parts)

def parse_col_widths(comment):
    """Extract col_widths list from an HTML comment string."""
    m = re.search(r'col_widths\s*=\s*\[([^\]]+)\]', comment)
    if m:
        return [int(x.strip()) for x in m.group(1).split(',')]
    return None

def has_header_row(comment):
    return 'header_row=True' in comment

def auto_col_widths(rows, min_total=820, min_col=60, max_col=420):
    """
    Width rules:
    1. Each column = max content width (Chinese char=2 units, ASCII=1, 12px/unit + 16px padding)
    2. Each column clamped to [min_col, max_col]
    3. If total < min_total, expand ONLY the last column (capped at max_col)
    4. Total may remain < min_total if last column is already at max_col
    """
    if not rows:
        return None
    n = max(len(r) for r in rows)

    # Measure display units per column
    units = [0] * n
    for row in rows:
        for i, cell in enumerate(row[:n]):
            u = sum(2 if ord(c) > 127 else 1 for c in re.sub(r'\*\*|`|~~', '', cell))
            units[i] = max(units[i], u)

    # Convert to pixels
    widths = [min(max_col, max(min_col, u * 12 + 16)) for u in units]

    # Expand only the last column to reach min_total (no cap during expansion)
    deficit = min_total - sum(widths)
    if deficit > 0:
        widths[-1] += deficit

    return widths

def parse_table(table_lines, col_widths=None, header=True):
    """Convert markdown table lines to HTML table XML."""
    rows = []
    for line in table_lines:
        if re.match(r'^\s*\|[\s\-|:]+\|\s*$', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)

    if not rows:
        return ''

    n_cols = max(len(r) for r in rows)
    parts = ['<table>']

    # Explicit col_widths (metadata tables) used as-is; auto-compute only for content tables
    if col_widths is None:
        col_widths = auto_col_widths(rows)

    if col_widths:
        parts.append('<colgroup>')
        for w in col_widths[:n_cols]:
            parts.append(f'<col width="{w}"/>')
        # pad if fewer widths than columns
        for _ in range(max(0, n_cols - len(col_widths))):
            parts.append('<col width="100"/>')
        parts.append('</colgroup>')

    if header and rows:
        parts.append('<thead><tr>')
        for cell in rows[0]:
            parts.append(f'<th>{inline_md_escaped(cell)}</th>')
        # pad missing cells
        for _ in range(n_cols - len(rows[0])):
            parts.append('<th></th>')
        parts.append('</tr></thead>')
        body_rows = rows[1:]
    else:
        body_rows = rows

    if body_rows:
        parts.append('<tbody>')
        for row in body_rows:
            parts.append('<tr>')
            for cell in row:
                parts.append(f'<td>{inline_md_escaped(cell)}</td>')
            for _ in range(n_cols - len(row)):
                parts.append('<td></td>')
            parts.append('</tr>')
        parts.append('</tbody>')

    parts.append('</table>')
    return ''.join(parts)

def md_to_xml(content):
    """Convert markdown to Lark-compatible XML."""
    lines = content.split('\n')
    out = []
    i = 0
    pending_col_widths = None
    pending_header = True

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip() or 'plain'
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = escape('\n'.join(code_lines))
            out.append(f'<pre lang="{lang}"><code>{code}</code></pre>')
            i += 1
            continue

        # HTML comment — extract col_widths hint, skip output
        if line.strip().startswith('<!--'):
            comment = line
            # multi-line comment
            while '-->' not in comment and i + 1 < len(lines):
                i += 1
                comment += lines[i]
            cw = parse_col_widths(comment)
            if cw:
                pending_col_widths = cw
            pending_header = has_header_row(comment)
            i += 1
            continue

        # Heading
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = re.sub(r'<!--.*?-->', '', m.group(2)).strip()
            out.append(f'<h{level}>{inline_md_escaped(text)}</h{level}>')
            i += 1
            continue

        # Horizontal rule — skip (no clean equivalent)
        if re.match(r'^---+\s*$', line):
            i += 1
            continue

        # Table
        if line.strip().startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            xml_table = parse_table(table_lines, pending_col_widths, pending_header)
            if xml_table:
                out.append(xml_table)
            pending_col_widths = None
            pending_header = True
            continue

        # Blockquote
        if line.startswith('>'):
            out.append(f'<blockquote><p>{inline_md_escaped(line[1:].strip())}</p></blockquote>')
            i += 1
            continue

        # Unordered list — collect consecutive items
        if re.match(r'^(\s*)[-*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^(\s*)[-*]\s+(.*)', lines[i]):
                m2 = re.match(r'^(\s*)[-*]\s+(.*)', lines[i])
                items.append(f'<li>{inline_md_escaped(m2.group(2))}</li>')
                i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue

        # Ordered list — collect consecutive items
        if re.match(r'^(\s*)\d+[.)]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^(\s*)\d+[.)]\s+(.*)', lines[i]):
                m2 = re.match(r'^(\s*)\d+[.)]\s+(.*)', lines[i])
                items.append(f'<li seq="auto">{inline_md_escaped(m2.group(2))}</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
            continue

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Paragraph
        out.append(f'<p>{inline_md_escaped(line.strip())}</p>')
        i += 1

    return '\n'.join(out)

def get_doc_title(content, filename):
    m = re.match(r'^#\s+(.+)', content, re.MULTILINE)
    return m.group(1).strip() if m else filename.replace('.md', '')

# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync_file(filepath, existing_doc_id=None):
    filename = os.path.basename(filepath)
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    title = get_doc_title(content, filename)
    print(f'  title: {title}')

    if existing_doc_id:
        doc_id = existing_doc_id
        print(f'  updating existing doc_id: {doc_id}')
    else:
        doc_id = create_node(title)
        print(f'  created new doc_id: {doc_id}')

    xml = f'<title>{html.escape(title)}</title>\n' + md_to_xml(content)
    result = overwrite_doc_xml(doc_id, xml)
    if result.get('ok') or result.get('data', {}).get('result') == 'success':
        print(f'  ✓ done')
    else:
        print(f'  [WARN] {result}')
    time.sleep(0.5)

def main():
    print('Loading existing nodes...')
    nodes = list_child_nodes()
    existing = {n['title']: n['obj_token'] for n in nodes}
    print(f'  Found {len(existing)} existing node(s)')

    print(f'\nSyncing {len(FILES)} files...')
    for fname in FILES:
        fpath = os.path.join(DOCS_DIR, fname)
        if not os.path.exists(fpath):
            print(f'  [SKIP] {fname}')
            continue
        print(f'\n[{fname}]')
        try:
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
            title = get_doc_title(content, os.path.basename(fpath))
            doc_id = existing.get(title)
            sync_file(fpath, existing_doc_id=doc_id)
        except Exception as e:
            print(f'  [ERROR] {e}')
    print('\nAll done.')

if __name__ == '__main__':
    main()
