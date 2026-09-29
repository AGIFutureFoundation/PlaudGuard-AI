# translation bridge

one provider definition, translated into what each agent harness actually needs. this is a lightweight recreation of the provider layer inside the aull interface engine, where a provider is `{class, base_url, api_key_env, models}` and each driver wires it into its own harness (env vars, cli flags, a synthesized profile, or a direct api call). the engine's sessions and scheduled routines then run on whichever harness and provider the routine names.

sponsor providers wired here: **crusoe** (managed inference, openai-compatible), **openrouter** (gateway, pinned to crusoe or nebius per request with `provider.only` + `allow_fallbacks:false`), **nebius** (ai studio, openai-compatible).

harnesses: `raw` (chat completions call), `codex` (codex cli with a synthesized `model_providers.<id>`), `claude` (claude code through an anthropic-compatible gateway; openrouter only, because crusoe and nebius speak only the openai wire format).

```
python3 bridge.py matrix            # the translation for every provider x harness, no calls
python3 bridge.py run               # execute the matrix; dry-run rows where the key is absent; receipts.json
python3 bridge.py run --provider openrouter --harness codex
python3 bridge.py engine-register   # register the providers in a running interface engine (localhost:7700)
```

keys come from the process env or `~/.interface/.env` (the engine's own resolution order) and are never printed. `receipts.json` records provider, harness, model, the provider openrouter actually served, latency, and the first 80 chars of the reply.
