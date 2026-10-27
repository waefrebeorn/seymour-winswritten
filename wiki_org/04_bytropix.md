# bytropix Inference Engine

**bytropix** is a multi-model, GPU-accelerated LLM inference engine written in C/CUDA, developed by **WaefreBeorn** (2024–present). It supports simultaneous inference across heterogeneous architectures (Gemma 4, DiffusionGemma, Qwen 3.6) with custom quantization kernels (IQ1_M, Q4_K, Q6_K), NSA-style sparse attention, and chunked SSM (DeltaNet) recursive state — all targeting consumer GPUs (RTX 4050 Laptop, 6GB VRAM) via WSL2.

---

## Overview

| Attribute | Detail |
|-----------|--------|
| **Repository** | `waefrebeorn/bytropix` |
| **Created** | 2024-12-14 |
| **Last Push** | 2026-06-22 |
| **Language** | C, CUDA, C++ (headers), Python (orchestration) |
| **Primary Target** | RTX 4050 Laptop (6140 MiB VRAM) / WSL2 Ubuntu |
| **Models Supported** | Gemma 4 12B, DiffusionGemma 26B, Qwen 3.6 35B (A3B) |
| **Key Innovation** | Tandem SSD→RAM→VRAM staging, heterogeneous GQA head_dim, fused Triton kernels |

---

## Architecture

### Multi-Model Adapter (2026-06-14)
Single engine loads and serves **three architecturally distinct models simultaneously**:
- **Gemma 4 12B** — Standard GQA, tied output embeddings
- **DiffusionGemma 26B** — Heterogeneous GQA (per-layer `head_dim`), diffusion-style denoising
- **Qwen 3.6 35B A3B** — MoE-style (active params ~3.6B), byte-level BPE tokenizer

### Memory Pipeline: Tandem SSD→RAM→VRAM
```
Model Weights (SSD)
    │
    ▼ File-based staging buffer (mmap)
System RAM (pinned)
    │
    ▼ cudaMemcpyAsync + cudaHostRegister
VRAM (GPU)
```
- **WSL2 fix** (2026-06-22): File-based staging buffer bypasses `cudaHostRegister` WSL2 limitation
- **Weight upload**: Asynchronous, stream-prioritized, supports GGUF/GGML shards

### Quantization Kernels (CUDA/Triton)
| Kernel | Precision | Status | Notes |
|--------|-----------|--------|-------|
| **IQ1_M** | 1.56-bit (mixed) | ✅ GPU + CPU fallback | Matrix mul + dequant fused |
| **Q4_K** | 4-bit (k-quants) | ✅ GPU native | `Q4_K` dequant + matmul fused |
| **Q6_K** | 6-bit (k-quants) | ⚠️ vec_dot loop bug | AVX2: 128/256 elements only (fixed in `q6_k_vec_dot_loop_bug`) |
| **GQA MatMul** | FP16/BF16 accum | ✅ | Heterogeneous `head_dim` support |

### Attention Innovations
1. **NSA-Style Sparse Attention** (2026-05-21) — DeepSeek-V3.2 DSA pattern:
   - Compression: `top-k` selection per block
   - Selection: Hardware-friendly bitmask
   - Sliding window: Local + global tokens
   - Implemented in `feat(gqa): NSA-style sparse attention`

2. **Chunked SSM (DeltaNet)** (2026-05-21) — Recursive state with chunked parallelism:
   - `Δ` (delta) parameterization for linear recurrence
   - Chunk boundary state passing
   - Debug pattern: `chunked-ssm-debug-pattern` skill

3. **Heterogeneous GQA** (2026-06-14) — Per-layer `head_dim`:
   - DiffusionGemma: `head_dim` varies by layer
   - `V`-projection sharing fix for large layers
   - Output dim detection for tied/untied embeddings

---

## Development Phases (Git Commit Log)

| Phase | Date Range | Key Commits | Milestone |
|-------|------------|-------------|-----------|
| **Phase 0** | 2024-12-14 | Repo init | Project scaffold |
| **Phase 1–27** | 2025-01 → 2026-05 | 200+ commits | Core engine, single-model |
| **Phase 28** | 2026-05-21 | 28s–28u | IQ1_M, Q4_K, NSA attention, Chunked SSM |
| **Phase 29** | 2026-06-05 → 2026-06-14 | Clean release, multi-model adapter | 3-model simultaneous |
| **Phase 30** | 2026-06-14 → 2026-06-22 | Gemma 4 GPU, Tandem pipeline, WSL2 fix | Production multi-model |

### Phase 28 Detail (2026-05-21 — The "Big Bang" Commit Day)
| Commit | Description |
|--------|-------------|
| `feat(gqa): NSA-style sparse attention (DeepSeek-V3.2 DSA pattern)` | Sparse attention kernel |
| `feat(gpu): IQ1_M + Q4_K quant matmul kernels, CPU IQ1_M fallback` | Quant kernels |
| `docs: Phase 28u IQ1_M model generated` | Model artifact |
| `docs: end-of-session — Phase 28t all P2 items complete` | Milestone |
| `docs: end-of-session — Phase 28s NSA sparse attention done` | Milestone |
| `docs: end-of-session — Phase 28r chunked SSM wired + documented` | Milestone |
| `feat(debug): DUMP_GQA_DEBUG_DIR + per-layer divergence audit` | Debug infra |
| `feat(debug): DUMP_EMBEDDING_DIR + root cause found — token embedding broken` | Root cause |

### Phase 29–30 (2026-06-05 → 2026-06-22)
| Date | Commit | Significance |
|------|--------|--------------|
| 2026-06-05 | `docs: rewrite README — accurate scope, MIT license` | Public readiness |
| 2026-06-14 | `Multi-model adapter: DiffusionGemma-26B + Gemma4-12B + Qwen3.6-35B` | 3-model breakthrough |
| 2026-06-14 | `fix: DGemma LARGE layer V-projection sharing` | Heterogeneous GQA fix |
| 2026-06-14 | `fix: per-layer head_dim for DiffusionGemma` | Core adapter fix |
| 2026-06-22 | `Gemma 4 GPU build + tied output fix for large vocab` | Gemma 4 support |
| 2026-06-22 | `Tandem SSD→RAM→VRAM pipeline + GPU-native Q4_K dequant` | Memory pipeline |
| 2026-06-22 | `gpu_gemma4: WSL2 weight upload fix using file-based staging buffer` | **WSL2 unblocker** |

---

## Key Technical Solutions

### WSL2 GPU Weight Upload (2026-06-22)
**Problem**: `cudaHostRegister` fails in WSL2 (no `/dev/nvidia*` mapping for pinned host memory)
**Solution**: File-backed staging buffer
```c
// mmap model file → pinned host buffer via staging file
int fd = open(staging_path, O_RDWR | O_CREAT, 0600);
ftruncate(fd, size);
void *staging = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
// cudaMemcpyAsync from staging (works in WSL2)
```

### DiffusionGemma Heterogeneous GQA (2026-06-14)
**Problem**: Per-layer `head_dim` breaks standard GQA kernels (assume constant)
**Solution**: 
- Per-layer kernel launch config
- `V`-projection sharing for large layers (memory saver)
- Output dim detection for tied/untied embeddings

### Q6_K AVX2 vec_dot Loop Bug
**File**: `q6_k_vec_dot_loop_bug` skill reference
**Issue**: Loop processes 128/256 elements instead of full vector
**Root Cause**: Incorrect step calculation in unrolled loop
**Fix**: Adjust loop bounds for remainder handling

---

## Integration Points

| Consumer | Integration |
|----------|-------------|
| **WuBu** (P2P inference) | Uses bytropix kernels for edge nodes |
| **WuBuMath** | Extracted VHF engine + training kernels |
| **slermes** | Shares `http_raw.c`, `cdp_client.c` patterns |
| **Seymour Project** | Gemma-4-12B topic tagger runs on bytropix/llama-server |
| **Lean 4 Proofs** | `bytropix/MATH/lean/wubu_proofs/` — WuBu Nesting formalization |

---

## Performance Targets (RTX 4050 Laptop)

| Model | Quant | Tok/s (gen) | VRAM | Notes |
|-------|-------|-------------|------|-------|
| Gemma 4 12B | Q4_K | ~10.9 | ~5.8 GB | Pipeline parallel |
| Gemma 4 12B | IQ1_M | ~2.4 | ~3.2 GB | Thinking baked in |
| DiffusionGemma 26B | Q4_K | ~3.1 | ~5.9 GB | Heterogeneous GQA |
| Qwen 3.6 35B A3B | Q4_K | ~4.2 | ~5.5 GB | MoE active params |

---

## Known Issues / Gaps

| Issue | Location | Status |
|-------|----------|--------|
| Q6_K vec_dot loop bug | `q6_k_vec_dot_loop_bug` skill | Documented, workaround exists |
| Flash-attn + WSL2 stability | `--flash-attn` flag | Use `--no-flash-attn` fallback |
| Multi-model KV cache fragmentation | `gpu_gemma4` commit | Arena allocator planned |
| DiffusionGemma denoising schedule | Not fully wired | Phase 31 target |
| Qwen byte-level BPE tokenizer | `qwen-tokenizer-byte-fix` skill | In progress |

---

## Documentation Artifacts
- `README.md` — Accurate scope, MIT license (2026-06-05)
- `entry.md` / `plan.md` — Llama.cpp project management pattern
- `power_tower/` — Analytical engine + Lean 4 skeleton (separate research)
- `MATH/lean/wubu_proofs/` — WuBu Nesting formalization

---

## See Also
- [WaefreBeorn](01_WaefreBeorn.md) — Creator/organization
- [WuBu Ecosystem](03_WuBu_Ecosystem.md) — Downstream consumers
- [Seymour Project](02_Seymour_Project.md) — Absorption pipeline consumer
- [slermes](05_slermes.md) — C11 agent framework sharing patterns
- [Cross-Referenced Timeline](07_Timeline_Crossref.md) — YouTube ↔ GitHub ↔ Research