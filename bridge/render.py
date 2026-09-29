#!/usr/bin/env python3
"""render ../demo/index.html from receipts.json"""
import json,html
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/'receipts.json').read_text())
rows="".join(f"<tr><td>{html.escape(r['provider'])}</td><td>{r['harness']}</td><td class='{'ok' if r['status']=='ok' else 'bad'}'>{html.escape(r['status'])}</td><td>{html.escape(str(r.get('provider') if r['harness']=='raw' else ''))}</td><td>{html.escape(str(r.get('model','')))}</td><td>{r.get('ms','')}</td><td class='q'>{html.escape(str(r.get('text') or r.get('error','')))[:90]}</td></tr>" for r in R)
page=f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>translation bridge — hack day 2026</title>
<style>body{{font:15px/1.5 system-ui;background:#0f1115;color:#e6e6e6;margin:0}}main{{max-width:1000px;margin:0 auto;padding:1.5rem}}table{{width:100%;border-collapse:collapse;font-size:.85rem}}td,th{{border-bottom:1px solid #2a3140;padding:.4rem;text-align:left;vertical-align:top}}.ok{{color:#22c55e;font-weight:700}}.bad{{color:#ef4444;font-weight:700}}.q{{color:#9aa;font-family:ui-monospace,monospace;font-size:.8rem}}code{{background:#161a22;padding:.1rem .3rem;border-radius:4px}}</style></head><body><main>
<h1>aull agent mesh <small style="font-weight:400;color:#9aa;font-size:.9rem">translation bridge · hack day 2026</small></h1>
<p>one provider definition, translated into what each agent harness needs. sponsor providers: <b>crusoe</b> (direct + via openrouter pin), <b>openrouter</b> (gateway, pinned per request), <b>nebius</b> (direct + via openrouter pin). harnesses: raw chat call, codex cli, claude code. the engine's scheduled routines run on whichever harness and provider a routine names.</p>
<h2>live receipts</h2><p class="q">generated from receipts.json by bridge.py run. "provider served" is what the gateway reports it actually routed to; direct calls report the model.</p>
<table><tr><th>provider def</th><th>harness</th><th>status</th><th>provider served</th><th>model</th><th>ms</th><th>reply / error</th></tr>{rows}</table>
<p><code>python3 bridge.py matrix</code> · <code>python3 bridge.py run</code> · <code>python3 bridge.py engine-register</code> · source: github.com/AGIFutureFoundation/PlaudGuard-AI (bridge/)</p></main></body></html>"""
(HERE.parent/'demo'/'index.html').write_text(page);print('page rendered',len(R),'receipts')
