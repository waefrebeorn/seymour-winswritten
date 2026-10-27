# Waefrebeorn Umbrella License v3.0 — Migration Plan

## Repo Count: 78 total

### Tier 1: Direct Application (29 repos)
These repos have no license file. The Waefrebeorn Umbrella License v3.0
is applied directly. Add a LICENSE file containing the v3.0 text.

- Bitcoin-Slot-Bot
- Bitcoin-Slot-Machine
- Diffusion_TTS
- GradRetentionNet
- KAN-WuBu-Memory
- OmniPoke
- SFIN
- StellAI
- WuBu-known-examples-in-c
- WuBuMath
- WuBuOS
- WuBuOffice
- WuBuPad
- agentic_structure
- balatro-gba
- bytropix
- coope_audit
- ghost
- grahaos_audit
- lisyarus.github.io
- mediaremux
- money-room
- plfm_radar
- safetensor-index-json-parser
- sd_api_pictures_tag_injection
- seymour-winswritten
- slermes
- system-prompts-and-models-of-ai-tools
- waefrebeorn.github.io

### Tier 2: Dual-License (31 repos)
These repos have existing permissive licenses (MIT, Apache-2.0, BSD-3-Clause).
Apply Waefrebeorn Umbrella v3.0 as a SECOND license option. Existing
contributions remain under their original license. New contributions
can also be under Waefrebeorn Umbrella.

MIT repos (24):
- EnhancedSGD
- FlicFlacMP4
- Godot-MCP
- KAN-Stem
- Moe-KAN
- PyNes
- TF2-OBS-Plugin
- UnityToGodotFork
- VulkanShaderCUDA
- WuBu
- WuBu-DLP
- WuBuCut
- WuBuRouter
- WuBuVideo
- bLocKo
- eshkol_audit
- harnessranger_audit
- hermes-self-evolution_audit
- invisible-watermark-gpu
- quantum_rng_audit
- robloxMCP
- slermes-odyssey
- webgpu-demo
- whisk3d

Apache-2.0 repos (6):
- InstantMesh_Win_Bat
- Mini-GLM5.2
- Rustchain
- dia
- slerm_spacewasm
- tailslayer

BSD-3-Clause repos:
- physics_vault

Migration step for Tier 2:
1. Add a LICENSE.waefrebeorn file (Umbrella v3.0 text) to each repo
2. Update README.md to state: "This project is dual-licensed under MIT (or Apache-2.0) and the Waefrebeorn Umbrella License v3.0."
3. Future contributions default to Waefrebeorn Umbrella unless explicitly choosing the original license

### Tier 3: Leave as-is, do NOT relicense (7 repos)
These repos use GPL-family licenses. GPL §7 prohibits adding additional
restrictions. The Waefrebeorn Umbrella License adds restrictions (corporate
obligations, dispensation, copyleft-at-scale). These cannot be applied
to GPL code without ALL contributors' consent.

GPL repos (leave unchanged):
- CVBX-Via-BNN
- PrismRTMPS
- WuBu-DefCon
- WuBuContainer
- WuBuFX
- obs-dual-format
- spout2

### Tier 4: Investigate first (10 repos)
These repos have 'other' or unclear license identifiers. Need to
investigate the actual license before deciding.

- Bitcoin-Casino
- Kissu-Vi
- OpenIB
- WuBuSkills
- WuBuWallPaper
- claude-export
- lainchan
- nvdiffrast
- perci_audit
- vichan

### Tier 5: Evaluate (1 repo)
- SanctumOS (Unlicense) — public domain. Cannot add restrictions.
  Evaluate if creator wants to keep public domain or switch to a
  Waefrebeorn-compatible permissive license.

### Tier 6: NOASSERTION repos (0 repos identified in this batch)
No repos had NOASSERTION in this scan. All repos were classified above.

---

## Migration Priority

1. Tier 1 (no license repos) — HIGHEST priority, easiest migration
2. Tier 2 (MIT/Apache dual-license) — MEDIUM, existing license stays
3. Tier 4 (investigate other) — MEDIUM, determine actual license first
4. Tier 5 (Unlicense evaluation) — LOW, evaluate case-by-case
5. Tier 3 (GPL, leave as-is) — NO ACTION (cannot relicense)

---

## Execution Commands

For each Tier 1 repo:
```bash
gh repo edit waefrebeorn/<repo-name> --add-topic "waefrebeorn-umbrella-license"
curl -X PUT "https://api.github.com/repos/waefrebeorn/<repo-name>/contents/LICENSE" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  -d '{"message": "Add Waefrebeorn Umbrella License v3.0", "content": "<base64-encoded LICENSE template>", "branch": "main"}'
```

For each Tier 2 repo (MIT → dual-license):
```bash
# Copy the Waefrebeorn license text to LICENSE.waefrebeorn
gh repo create-file waefrebeorn/<repo-name> \
  --path "LICENSE.waefrebeorn" \
  --message "Add Waefrebeorn Umbrella License as dual-license option" \
  --content "$(cat /home/wubu/seymour-project/ponderables/drafts/LICENSE.template)"
```
