**TITLE: The Guy Who Writes CUDA Kernels for Fun (And Cries About Vec_Dot Bugs)**

Q6_K quantization. Vec_dot loop. PTX assembly. If those words made your eyes glaze over, congratulations — you're normal. He writes GPU inference engines *for fun*. On stream. While chat roasts his register allocation.

The Bytropix engine: a from-scratch LLM inference stack in CUDA. Why? Because llama.cpp exists, but "it does too much magic." He wants to *see* the matrix multiply. Feel the warp divergence. Debug the bank conflicts at 2 AM because the profiler said "achieved occupancy: 12%."

```
┌─────────────────────────────────┐
│  BONUS FACT: A single H100      │
│  does ~990 TFLOPS FP16 (sparse),│
│  ~494 dense. His 4050 laptop    │
│  does ~12. He optimizes anyway. │
└─────────────────────────────────┘
```

The vec_dot bug: a dot product kernel that worked on paper, crashed in prod. Turns out Q6_K packing — 6-bit weights, 32 at a time — has edge cases when the vector length isn't a multiple of 32. The fix took three streams. The chat suggested "just use cuBLAS." He banned them.

Why does he do it? Same reason people climb Everest. Not because it's there. Because the *abstraction* is there, and he wants to punch through it. Every kernel he writes is a middle finger to "good enough."

The kicker: the engine works. Runs Gemma 4 12B at 18 tok/s on a laptop GPU. He'll never "ship" it. The code is the point. The struggle is the product.

---

¹ Q6_K = 6-bit quantization, K-means clustering for outliers. ² Vec_dot = vector dot product. The bread and butter of attention. ³ 18 tok/s = usable for chat. Not a benchmark king. ⁴ See entry "The Woman Who Hand-Optimized a Fourier Transform for a Toaster" (p. 401)