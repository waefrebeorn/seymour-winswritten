# Model Inference SOP — Gemma 4 12B QAT

## Key Facts

- **Model**: `gemma-4-12B-it-qat-UD-Q4_K_XL.gguf` (6.3GB Q4 quantization)
- **Context window**: 256K tokens (use `--ctx-size 8192` to start, increase as needed)
- **Thinking mode**: ALWAYS ON in QAT. Model always outputs `<|channel>thought\n...` reasoning.
  - Reasoning goes to `reasoning_content` field
  - Actual answer goes to `content` field
  - **Must use sufficient `max_tokens`** (≥256) or thinking eats the budget and content is empty
- **Chat template**: Do NOT override with `--chat-template`. Let the model use its built-in template.
- **Server mode ONLY**: Use `llama-server`, never `llama-cli` (CLI is interactive REPL, not API)

## Correct Server Launch

```bash
llama-server \
  --model /path/to/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf \
  --ctx-size 8192 \
  --host 0.0.0.0 \
  --port 18802
```

**No `-ngl`** — use pure mmap. The OS page cache handles paging automatically.
**No `--chat-template`** — let the model use its built-in template.
**No `--no-mmap`** — mmap is the default and correct behavior.

## Correct API Call

```json
{
  "model": "gemma-4-12b",
  "messages": [{"role": "user", "content": "Your prompt here"}],
  "max_tokens": 512,
  "temperature": 0.7
}
```

- `max_tokens` must be ≥256 to get past thinking into actual content
- Response has two fields: `reasoning_content` (thinking) and `content` (answer)

## Benchmark Results (WSL, no GPU)

| Config | Tokens/sec | Notes |
|--------|-----------|-------|
| mmap only (no -ngl) | ~8.0 tok/s | CPU-only, OS page cache |
| -ngl 10 | N/A | No GPU in WSL |
| -ngl 20 | N/A | No GPU in WSL |

**System**: 7.4GB RAM, model 6.3GB fits in RAM + page cache
**VmRSS**: ~2.7MB (model served from OS page cache, not process RAM)

## Common Mistakes

1. **Using `llama-cli`** — it's an interactive REPL, not an API. Use `llama-server`.
2. **Overriding chat template** — `--chat-template gemma3` produces garbage. Don't override.
3. **Too few max_tokens** — thinking eats the budget. Use ≥256.
4. **Trying -ngl without GPU** — WSL has no `/dev/nvidia*`. Pure mmap is the only option.
5. **Expecting no thinking** — QAT models always think. Read `content` field for the answer.

## Parsing the Response

```python
import json, urllib.request

req_data = json.dumps({
    "model": "gemma-4-12b",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 512,
    "temperature": 0.7
}).encode()

req = urllib.request.Request("http://localhost:18802/v1/chat/completions",
    data=req_data, headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read())

reasoning = resp['choices'][0]['message'].get('reasoning_content', '')
answer = resp['choices'][0]['message'].get('content', '')
usage = resp.get('usage', {})

print(f"Thinking: {reasoning[:200]}...")
print(f"Answer: {answer}")
print(f"Tokens: {usage.get('completion_tokens', '?')} in {elapsed:.1f}s")
```
