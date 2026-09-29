#!/usr/bin/env python3
"""translation bridge: one provider definition -> what each agent harness needs.

    python3 bridge.py matrix                      # show the translation for every provider x harness (no calls)
    python3 bridge.py run  [--provider P] [--harness H] [--prompt "..."]   # execute; dry-run when the key is absent
    python3 bridge.py engine-register             # register the providers in a running interface engine (localhost:7700)

harnesses: raw (openai-compatible chat call), codex (codex cli with a synthesized model_provider), claude (claude code
through an anthropic-compatible gateway; openrouter only). keys are read from the process env or ~/.interface/.env and
are never printed. receipts land in receipts.json next to this file.
"""
import argparse, json, os, shlex, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROVIDERS = json.loads((HERE / "providers.json").read_text())
HARNESSES = ("raw", "codex", "claude")

def load_env():
    p = Path.home() / ".interface" / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))

def key_for(p): return os.environ.get(PROVIDERS[p]["key_env"])

def translate(p, h, prompt):
    """return (description, runnable) where runnable is a callable or None (harness cannot take this provider)."""
    cfg = PROVIDERS[p]; env_name = cfg["key_env"]
    if h == "raw":
        body = {"model": cfg["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 40}
        if cfg.get("pin"): body["provider"] = {"only": [cfg["pin"]], "allow_fallbacks": False}
        desc = f"POST {cfg['base_url']}/chat/completions  Authorization: Bearer ${env_name}  model={cfg['model']}" + (f"  provider.only=[{cfg['pin']}]" if cfg.get("pin") else "")
        def run(key):
            req = urllib.request.Request(cfg["base_url"] + "/chat/completions", data=json.dumps(body).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "X-Title": "translation-bridge"})
            with urllib.request.urlopen(req, timeout=60) as r: j = json.load(r)
            return {"model": j.get("model"), "provider": j.get("provider"), "text": j["choices"][0]["message"]["content"][:80]}
        return desc, run
    if h == "codex":
        args = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only",
                "-c", f"model_provider={p}", "-c", f'model_providers.{p}.name="{p}"',
                "-c", f'model_providers.{p}.base_url="{cfg["base_url"]}"', "-c", f'model_providers.{p}.env_key="{env_name}"',
                "-c", f'model_providers.{p}.wire_api="responses"', "-c", f'model="{cfg["model"]}"', prompt]
        desc = " ".join(shlex.quote(a) for a in args)
        def run(key):
            out = subprocess.run(args, capture_output=True, text=True, timeout=180, env={**os.environ, env_name: key})
            if out.returncode != 0: raise RuntimeError((out.stderr or out.stdout)[-300:])
            return {"model": cfg["model"], "text": out.stdout.strip()[-80:]}
        return desc, run
    if h == "claude":
        if p != "openrouter":
            return f"claude code speaks the anthropic wire format; {p} exposes only openai-compatible chat. route it through openrouter with a preset pinned to {p}.", None
        env = {"ANTHROPIC_BASE_URL": cfg["base_url"].removesuffix("/v1"), "ANTHROPIC_AUTH_TOKEN": f"${env_name}", "ANTHROPIC_MODEL": cfg["model"]}
        desc = " ".join(f"{k}={v}" for k, v in env.items()) + f" claude -p {shlex.quote(prompt)} --model {cfg['model']}"
        def run(key):
            e = {**os.environ, **env, "ANTHROPIC_AUTH_TOKEN": key}; e.pop("ANTHROPIC_API_KEY", None)
            out = subprocess.run(["claude", "-p", prompt, "--model", cfg["model"]], capture_output=True, text=True, timeout=180, env=e)
            if out.returncode != 0: raise RuntimeError((out.stderr or out.stdout)[-300:])
            return {"model": cfg["model"], "text": out.stdout.strip()[-80:]}
        return desc, run
    raise SystemExit(f"unknown harness {h}")

def cmd_matrix(a):
    for p in PROVIDERS:
        for h in HARNESSES:
            desc, run = translate(p, h, a.prompt)
            print(f"[{p:10s} x {h:6s}] {'ok ' if run else 'n/a'} key={'set' if key_for(p) else 'absent'}\n    {desc}")

def cmd_run(a):
    receipts = []
    for p in ([a.provider] if a.provider else list(PROVIDERS)):
        for h in ([a.harness] if a.harness else HARNESSES):
            desc, run = translate(p, h, a.prompt); key = key_for(p)
            rec = {"provider": p, "harness": h, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "translation": desc}
            if run is None: rec["status"] = "n/a"
            elif not key: rec["status"] = "dry-run (no key)"
            else:
                t0 = time.time()
                try: rec.update(run(key)); rec["status"] = "ok"; rec["ms"] = int((time.time() - t0) * 1000)
                except Exception as e: rec["status"] = "error"; rec["error"] = str(e)[:300]
            print(json.dumps({k: v for k, v in rec.items() if k != "translation"})); receipts.append(rec)
    path = HERE / "receipts.json"
    old = json.loads(path.read_text()) if path.exists() else []
    path.write_text(json.dumps(old + receipts, indent=1)); print(f"receipts -> {path}")

def cmd_engine_register(a):
    token = Path(a.token_file).expanduser().read_text().strip()
    for p, cfg in PROVIDERS.items():
        body = {"id": p, "name": p, "class": cfg["class"], "base_url": cfg["base_url"], "api_key_env": cfg["key_env"],
                "models": [{"id": cfg["model"], "name": cfg["model"]}]}
        req = urllib.request.Request(a.engine + "/api/providers", data=json.dumps(body).encode(), method="POST",
              headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r: print(p, r.status, r.read()[:120].decode())
        except urllib.error.HTTPError as e: print(p, e.code, e.read()[:200].decode())

if __name__ == "__main__":
    load_env()
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("matrix"); m.add_argument("--prompt", default="Reply with the single word OK."); m.set_defaults(f=cmd_matrix)
    r = sub.add_parser("run"); r.add_argument("--provider", choices=list(PROVIDERS)); r.add_argument("--harness", choices=HARNESSES)
    r.add_argument("--prompt", default="Reply with the single word OK."); r.set_defaults(f=cmd_run)
    e = sub.add_parser("engine-register"); e.add_argument("--engine", default="http://127.0.0.1:7700")
    e.add_argument("--token-file", default="~/.interface/engine-token"); e.set_defaults(f=cmd_engine_register)
    a = ap.parse_args(); a.f(a)
