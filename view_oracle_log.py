#!/usr/bin/env python3
"""
CyberEden Oracle Log Viewer
用法：python view_oracle_log.py [oracle_turns.jsonl 路径]
会生成 HTML 报告并在浏览器中打开。
"""

import json
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

DEFAULT_LOG = Path(__file__).parent / "logs" / "oracle_turns.jsonl"


def load_turns(path: Path) -> list[dict]:
    turns = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    turns.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return turns


def fmt_ts(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%m-%d %H:%M:%S")
    except Exception:
        return ts[:19]


def escape(s: str) -> str:
    if not isinstance(s, str):
        s = json.dumps(s, ensure_ascii=False)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_turn(t: dict, idx: int) -> str:
    resp = t.get("response") or {}
    usage = t.get("usage") or {}
    req = t.get("request") or {}
    msgs = req.get("messages") or []
    
    thoughts = resp.get("thoughts") or ""
    shell = resp.get("shell_commands") or []
    diary = resp.get("diary_entry")
    new_code = resp.get("new_code")
    sleep = resp.get("sleep_seconds", "?")
    error = t.get("error")
    
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    stop = t.get("stop_reason", "")
    
    # 决定卡片颜色
    if error:
        card_class = "turn-error"
    elif new_code:
        card_class = "turn-mutation"
    elif diary:
        card_class = "turn-diary"
    elif shell:
        card_class = "turn-active"
    else:
        card_class = "turn-idle"
    
    shell_html = ""
    if shell:
        cmds = "".join(f"<code>$ {escape(c)}</code>" for c in shell)
        shell_html = f'<div class="field-shell"><span class="label">SHELL</span>{cmds}</div>'
    
    diary_html = ""
    if diary:
        diary_html = f'<div class="field-diary"><span class="label">DIARY</span><span>{escape(diary)}</span></div>'
    
    mutation_html = ""
    if new_code:
        mutation_html = f'<div class="field-mutation"><span class="label">⚡ NEW CODE</span><pre>{escape(new_code[:300])}...</pre></div>'
    
    error_html = ""
    if error:
        error_html = f'<div class="field-error"><span class="label">ERROR</span><span>{escape(str(error))}</span></div>'

    # 最后一条 user message（本轮发送的内容摘要）
    user_msg = ""
    for m in reversed(msgs):
        if m.get("role") == "user":
            content = m.get("content", "")[:200]
            user_msg = f'<div class="field-user"><span class="label">USER→</span><span>{escape(content)}</span></div>'
            break

    return f"""
<div class="turn {card_class}" id="turn-{idx}">
  <div class="turn-header">
    <span class="turn-num">#{idx + 1}</span>
    <span class="turn-ts">{fmt_ts(t.get('timestamp', ''))}</span>
    <span class="turn-msgs">msgs:{t.get('messages_count', '?')}</span>
    <span class="turn-tokens">in:{in_tok} out:{out_tok}</span>
    <span class="turn-stop">{escape(stop)}</span>
    <span class="turn-sleep">z:{sleep}s</span>
  </div>
  <div class="turn-thoughts">{escape(thoughts)}</div>
  {shell_html}
  {diary_html}
  {mutation_html}
  {error_html}
  {user_msg}
</div>"""


def render_html(turns: list[dict], log_path: Path) -> str:
    total = len(turns)
    total_in = sum((t.get("usage") or {}).get("input_tokens", 0) for t in turns)
    total_out = sum((t.get("usage") or {}).get("output_tokens", 0) for t in turns)
    mutations = sum(1 for t in turns if (t.get("response") or {}).get("new_code"))
    diaries = sum(1 for t in turns if (t.get("response") or {}).get("diary_entry"))
    shells = sum(1 for t in turns if (t.get("response") or {}).get("shell_commands"))
    errors = sum(1 for t in turns if t.get("error"))
    idles = sum(1 for t in turns if not (t.get("response") or {}).get("shell_commands") 
                and not (t.get("response") or {}).get("new_code")
                and not t.get("error"))

    turns_html = "\n".join(render_turn(t, i) for i, t in enumerate(turns))

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Adam Oracle Log Viewer</title>
<style>
  :root {{
    --bg: #0d1117; --bg2: #161b22; --bg3: #1c2128;
    --border: #30363d; --text: #c9d1d9; --muted: #8b949e;
    --green: #3fb950; --blue: #58a6ff; --yellow: #d29922;
    --red: #f85149; --purple: #bc8cff; --orange: #ffa657;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 13px; }}
  
  header {{ background: var(--bg2); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }}
  header h1 {{ font-size: 16px; color: var(--blue); }}
  .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-left: auto; }}
  .stat {{ padding: 3px 10px; border-radius: 12px; font-size: 11px; border: 1px solid; }}
  .stat-total {{ color: var(--blue); border-color: var(--blue); }}
  .stat-tokens {{ color: var(--muted); border-color: var(--border); }}
  .stat-active {{ color: var(--green); border-color: var(--green); }}
  .stat-diary {{ color: var(--purple); border-color: var(--purple); }}
  .stat-mutation {{ color: var(--orange); border-color: var(--orange); }}
  .stat-idle {{ color: var(--muted); border-color: var(--border); }}
  .stat-error {{ color: var(--red); border-color: var(--red); }}
  
  .filter-bar {{ background: var(--bg2); border-bottom: 1px solid var(--border); padding: 8px 24px; display: flex; gap: 8px; }}
  .filter-btn {{ background: var(--bg3); border: 1px solid var(--border); color: var(--muted); padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 11px; transition: all 0.2s; }}
  .filter-btn:hover, .filter-btn.active {{ border-color: var(--blue); color: var(--blue); }}
  
  .container {{ max-width: 960px; margin: 0 auto; padding: 16px 24px; display: flex; flex-direction: column; gap: 8px; }}
  
  .turn {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; transition: border-color 0.2s; }}
  .turn:hover {{ border-color: var(--blue); }}
  .turn-active {{ border-left: 3px solid var(--green); }}
  .turn-mutation {{ border-left: 3px solid var(--orange); background: #1a1300; }}
  .turn-diary {{ border-left: 3px solid var(--purple); }}
  .turn-idle {{ border-left: 3px solid var(--border); opacity: 0.7; }}
  .turn-error {{ border-left: 3px solid var(--red); background: #1a0000; }}
  
  .turn-header {{ background: var(--bg2); padding: 8px 12px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .turn-num {{ color: var(--blue); font-weight: bold; min-width: 32px; }}
  .turn-ts {{ color: var(--muted); font-size: 11px; }}
  .turn-msgs {{ color: var(--muted); font-size: 11px; }}
  .turn-tokens {{ color: var(--muted); font-size: 11px; margin-left: auto; }}
  .turn-stop {{ font-size: 10px; padding: 1px 6px; background: var(--bg3); border-radius: 4px; }}
  .turn-sleep {{ color: var(--yellow); font-size: 11px; }}
  
  .turn-thoughts {{ padding: 10px 12px; color: var(--text); line-height: 1.5; border-bottom: 1px solid var(--border); }}
  
  .field-shell, .field-diary, .field-mutation, .field-error, .field-user {{ padding: 8px 12px; border-bottom: 1px solid var(--border); display: flex; gap: 8px; align-items: flex-start; }}
  .label {{ font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; white-space: nowrap; margin-top: 1px; }}
  
  .field-shell .label {{ background: #162c00; color: var(--green); }}
  .field-shell code {{ background: var(--bg3); padding: 2px 8px; border-radius: 4px; display: block; margin: 2px 0; color: var(--green); }}
  
  .field-diary .label {{ background: #1a1030; color: var(--purple); }}
  .field-diary span {{ color: var(--purple); font-style: italic; }}
  
  .field-mutation .label {{ background: #1a0e00; color: var(--orange); }}
  .field-mutation pre {{ color: var(--orange); font-size: 11px; overflow-x: auto; white-space: pre-wrap; }}
  
  .field-error .label {{ background: #1a0000; color: var(--red); }}
  .field-error span {{ color: var(--red); }}
  
  .field-user .label {{ background: var(--bg3); color: var(--muted); }}
  .field-user span {{ color: var(--muted); font-size: 11px; }}
  
  .log-path {{ text-align: center; color: var(--muted); font-size: 11px; padding: 24px; }}
  
  .hidden {{ display: none; }}
</style>
</head>
<body>
<header>
  <h1>⚡ Adam Oracle Log Viewer</h1>
  <div class="stats">
    <span class="stat stat-total">共 {total} 轮</span>
    <span class="stat stat-tokens">~{(total_in+total_out)//1000}k tokens</span>
    <span class="stat stat-active">🔧 {shells} 执行</span>
    <span class="stat stat-diary">📝 {diaries} 日记</span>
    <span class="stat stat-mutation">⚡ {mutations} 进化</span>
    <span class="stat stat-idle">💤 {idles} 空转</span>
    {'<span class="stat stat-error">❌ ' + str(errors) + ' 错误</span>' if errors else ''}
  </div>
</header>
<div class="filter-bar">
  <button class="filter-btn active" onclick="filterTurns('all', this)">全部</button>
  <button class="filter-btn" onclick="filterTurns('turn-active', this)">🔧 有执行</button>
  <button class="filter-btn" onclick="filterTurns('turn-mutation', this)">⚡ 进化</button>
  <button class="filter-btn" onclick="filterTurns('turn-diary', this)">📝 写日记</button>
  <button class="filter-btn" onclick="filterTurns('turn-idle', this)">💤 空转</button>
  <button class="filter-btn" onclick="filterTurns('turn-error', this)">❌ 错误</button>
</div>
<div class="container" id="main">
{turns_html}
</div>
<div class="log-path">📂 {log_path}</div>
<script>
function filterTurns(cls, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.turn').forEach(el => {{
    if (cls === 'all' || el.classList.contains(cls)) {{
      el.classList.remove('hidden');
    }} else {{
      el.classList.add('hidden');
    }}
  }});
}}
</script>
</body>
</html>"""


def main():
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOG
    if not log_path.exists():
        print(f"找不到日志文件: {log_path}")
        sys.exit(1)

    turns = load_turns(log_path)
    print(f"加载 {len(turns)} 条记录…")

    out_path = log_path.parent / "oracle_log_viewer.html"
    html = render_html(turns, log_path)
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成: {out_path}")
    webbrowser.open(out_path.as_uri())


if __name__ == "__main__":
    main()
