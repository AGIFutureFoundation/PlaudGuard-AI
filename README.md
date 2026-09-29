# aull agent mesh

one engine, many harnesses, many providers, one record. hack day 2026 submission.

## what it is

an agent mesh: a scheduler engine that runs agents as **routines** on any harness — claude code, codex, grok, gemini cli, cline, or a raw openai-compatible model call — against any model provider, and a desktop app that connects to engines running elsewhere. agents on the same engine share one machine's record (notes, queue, receipts) and hand work to each other by file and by trigger, so a claude routine, a codex routine, and a grok routine work the same board without a shared vendor. it has been running unattended on a small always-on box for months, dozens of routines a day.

## what we wired today

three sponsor providers into the mesh, through its **translation bridge**: one provider definition, translated into what each harness actually needs (env vars, cli flags, a synthesized profile, or a direct api call).

| provider | route | status |
| --- | --- | --- |
| **crusoe** | openrouter pinned to crusoe, fallbacks off | live, openrouter reports `Crusoe` served the call |
| **nebius** | openrouter pinned to nebius, fallbacks off | live, openrouter reports `Nebius` served the call |
| **openrouter** | gateway for both, and the anthropic-compatible gateway that drives claude code | live |
| crusoe / nebius direct | openai-compatible endpoints | wired, dry-run until keys are present |
| codex harness | synthesized `model_providers` profile | wired, errored on the day (recorded, not hidden) |

## what's in this repo

- [`bridge/`](bridge/) — the translation bridge recreated standalone in stdlib python: `providers.json` → raw / codex / claude harnesses, `receipts.json`, and `engine-register` to push the providers into a running engine.
- [`demo/`](demo/) — the receipts page, live at https://plaudguard-ai.vercel.app.

the engine and desktop app themselves live in the aull repository, shown in the submission video with remote connections open.

## run it

```
cd bridge
python3 bridge.py matrix            # the translation for every provider x harness, no calls
python3 bridge.py run               # execute; dry-run rows where a key is absent; writes receipts.json
python3 render.py                   # rebuild the demo page from receipts
python3 bridge.py engine-register   # register the providers in a running engine (localhost:7700)
```

keys come from the process env or the engine's own env file and are never printed.
